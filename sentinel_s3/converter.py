import re
import logging
from collections import OrderedDict
import xml.etree.cElementTree as etree

from pyproj import Proj, transform
from six import iteritems


logger = logging.getLogger('sentinel.meta.s3')


def pad(value, width, char='0', direction='left'):

    value = str(value)

    while len(value) < width:
        if direction == 'left':
            value = '{0}{1}'.format(char, value)
        else:
            value = '{1}{0}'.format(char, value)

    return value


def epsg_code(geojson):

    if isinstance(geojson, dict):
        if 'crs' in geojson:
            urn = geojson['crs']['properties']['name'].split(':')
            if 'EPSG' in urn:
                try:
                    return int(urn[-1])
                except (TypeError, ValueError):
                    return None

    return None


def convert_coordinates(coords, origin, wgs84):
    if isinstance(coords, list) or isinstance(coords, tuple):
        try:
            if isinstance(coords[0], list) or isinstance(coords[0], tuple):
                return [convert_coordinates(list(c), origin, wgs84) for c in coords]
            elif isinstance(coords[0], float):
                return list(transform(origin, wgs84, *coords))
        except IndexError:
            pass

    return None


def to_latlon(geojson):

    if isinstance(geojson, dict):

        # get epsg code:
        code = epsg_code(geojson)
        if code:
            origin = Proj(init='epsg:%s' % code)
            wgs84 = Proj(init='epsg:4326')

            new_coords = convert_coordinates(geojson['coordinates'], origin, wgs84)
            if new_coords:
                geojson['coordinates'] = new_coords
                geojson['crs']['properties']['name'] = 'urn:ogc:def:crs:EPSG:8.9:4326'

    return geojson


def camelcase_underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_tiles_list(element):
    """ Returns the list of all tile names from Product_Organisation element
    in metadata.xml """

    tiles = {}

    for el in element:
        g = el.findall('.//Granules')[0]
        name = g.attrib['granuleIdentifier']

        name_parts = name.split('_')
        mgs = name_parts[-2]
        tiles[mgs] = name

    return tiles


def metadata_to_dict(metadata):
    """ Looks at metadata.xml file of sentinel product and extract useful keys
    Returns a python dict """

    tree = etree.parse(metadata)
    root = tree.getroot()

    meta = OrderedDict()

    keys = [
        'SPACECRAFT_NAME',
        'PRODUCT_STOP_TIME',
        'Cloud_Coverage_Assessment',
        'PROCESSING_LEVEL',
        'PRODUCT_TYPE',
        'PROCESSING_BASELINE',
        'SENSING_ORBIT_NUMBER',
        'SENSING_ORBIT_DIRECTION',
        'PRODUCT_FORMAT',
    ]

    # grab important keys from the file
    for key in keys:
        try:
            meta[key.lower()] = root.findall('.//' + key)[0].text
        except IndexError:
            meta[key.lower()] = None

    meta['product_cloud_coverage_assessment'] = float(meta.pop('cloud_coverage_assessment'))

    meta['sensing_orbit_number'] = int(meta['sensing_orbit_number'])

    # get tile list
    meta['tiles'] = get_tiles_list(root.findall('.//Product_Organisation')[0])

    # get available bands
    bands = root.findall('.//Band_List')[0]
    meta['band_list'] = []
    for b in bands:
        band = b.text.replace('B', '')
        if len(band) == 1:
            band = 'B' + pad(band, 2)
        else:
            band = b.text
        meta['band_list'].append(band)

    return meta


def tile_metadata(tile, product):

    s3_url = 'http://sentinel-s2-l1c.s3.amazonaws.com'
    grid = 'T{0}{1}{2}'.format(pad(tile['utmZone'], 2), tile['latitudeBand'], tile['gridSquare'])

    meta = OrderedDict({
        'tile_name': product['tiles'][grid]
    })

    logger.info('Processing tile %s' % meta['tile_name'])

    meta['date'] = tile['timestamp'].split('T')[0]

    meta['thumbnail'] = '{1}/{0}/preview.jp2'.format(tile['path'], s3_url)

    # remove unnecessary keys
    product.pop('tiles')
    tile.pop('datastrip')
    bands = product.pop('band_list')

    for k, v in iteritems(tile):
        meta[camelcase_underscore(k)] = v

    meta.update(product)

    # construct download links
    links = ['{2}/{0}/{1}.jp2'.format(meta['path'], b, s3_url) for b in bands]

    meta['download_links'] = {
        'aws_s3': links
    }

    # change coordinates to wsg4 degrees
    keys = ['tile_origin', 'tile_geometry', 'tile_data_geometry']
    for key in keys:
        if key in meta:
            meta[key] = to_latlon(meta[key])

    return meta
