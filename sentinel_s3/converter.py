import re
import os
import errno
import shutil
import logging
import threading
from tempfile import mkdtemp
from collections import OrderedDict
import xml.etree.cElementTree as etree

import rasterio
import requests
from wordpad import pad
from six import iteritems
from pyproj import Proj, transform
from rasterio.features import shapes
from shapely.ops import cascaded_union
from shapely.geometry import mapping, Polygon

logger = logging.getLogger('sentinel.meta.s3')
s3_url = 'http://sentinel-s2-l1c.s3.amazonaws.com'


def epsg_code(geojson):
    """ get the espg code from the crs system """

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
    """ Convert coordinates from one crs to another """
    if isinstance(coords, list) or isinstance(coords, tuple):
        try:
            if isinstance(coords[0], list) or isinstance(coords[0], tuple):
                return [convert_coordinates(list(c), origin, wgs84) for c in coords]
            elif isinstance(coords[0], float):
                c = list(transform(origin, wgs84, *coords))
                if c[0] < -170:
                    c[0] = c[0] + 360
                return c

        except IndexError:
            pass

    return None


def to_latlon(geojson, origin_espg=None):
    """
    Convert a given geojson to wgs84. The original epsg must be included insde the crs
    tag of geojson
    """

    if isinstance(geojson, dict):

        # get epsg code:
        if origin_espg:
            code = origin_espg
        else:
            code = epsg_code(geojson)
        if code:
            origin = Proj(init='epsg:%s' % code)
            wgs84 = Proj(init='epsg:4326')

            new_coords = convert_coordinates(geojson['coordinates'], origin, wgs84)
            if new_coords:
                geojson['coordinates'] = new_coords
                if 'crs' not in geojson:
                    geojson['crs'] = {
                        'type': 'name',
                        'properties': {
                            'name': 'urn:ogc:def:crs:EPSG:8.9:4326'
                        }
                    }
                else:
                    geojson['crs']['properties']['name'] = 'urn:ogc:def:crs:EPSG:8.9:4326'

    return geojson


def camelcase_underscore(name):
    """ Convert camelcase names to underscore """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def get_tiles_list(element):
    """
    Returns the list of all tile names from Product_Organisation element
    in metadata.xml
    """

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


def get_tile_geometry(path, origin_espg, tolerance=500):
    """ Calculate the data and tile geometry for sentinel-2 tiles """

    with rasterio.open(path) as src:

        # Get tile geometry
        b = src.bounds
        tile_shape = Polygon([(b[0], b[1]), (b[2], b[1]), (b[2], b[3]), (b[0], b[3]), (b[0], b[1])])
        tile_geojson = mapping(tile_shape)

        # read first band of the image
        image = src.read(1)

        # create a mask of zero values
        mask = image == 0.

        # generate shapes of the mask
        novalue_shape = shapes(image, mask=mask, transform=src.affine)

        # generate polygons using shapely
        novalue_shape = [Polygon(s['coordinates'][0]) for (s, v) in novalue_shape]

        if novalue_shape:

            # Make sure polygons are united
            # also simplify the resulting polygon
            union = cascaded_union(novalue_shape)

            # generates a geojson
            data_shape = tile_shape.difference(union)

            # If there are multipolygons, select the largest one
            if data_shape.geom_type == 'MultiPolygon':
                areas = {p.area: i for i, p in enumerate(data_shape)}
                largest = max(areas.keys())
                data_shape = data_shape[areas[largest]]

            # if the polygon has interior rings, remove them
            if list(data_shape.interiors):
                data_shape = Polygon(data_shape.exterior.coords)

            data_shape = data_shape.simplify(tolerance, preserve_topology=False)
            data_geojson = mapping(data_shape)

        else:
            data_geojson = tile_geojson

        # convert cooridnates to degrees
        return (to_latlon(tile_geojson, origin_espg), to_latlon(data_geojson, origin_espg))


def get_tile_geometry_from_s3(meta):

    # create a temp folder
    tmp_folder = mkdtemp()
    f = os.path.join(tmp_folder, 'B01.jp2')

    # donwload B01
    r = requests.get('{0}/{1}/B01.jp2'.format(s3_url, meta['path']), stream=True)
    chunk_size = 1024

    with open(f, 'wb') as fd:
        for chunk in r.iter_content(chunk_size):
            fd.write(chunk)

    (meta['tile_geometry'],
     meta['tile_data_geometry']) = get_tile_geometry(f, epsg_code(meta['tile_geometry']))
    meta['tile_origin'] = to_latlon(meta['tile_origin'])

    # remove temp folder
    try:
        shutil.rmtree(tmp_folder)
    except OSError as exc:
        if exc.errno != errno.ENOENT:
            raise

    return meta


def tile_metadata(tile, product, geometry_check=None):
    """ Generate metadata for a given tile

    - geometry_check is a function the determines whether to calculate the geometry by downloading
    B01 and override provided geometry in tilejson. The meta object is passed to this function.
    The function return a True or False response.
    """

    grid = 'T{0}{1}{2}'.format(pad(tile['utmZone'], 2), tile['latitudeBand'], tile['gridSquare'])

    meta = OrderedDict({
        'tile_name': product['tiles'][grid]
    })

    logger.info('%s Processing tile %s' % (threading.current_thread().name, tile['path']))

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

    meta['original_tile_meta'] = '{0}/{1}/tileInfo.json'.format(s3_url, meta['path'])

    def internal_latlon(meta):
        keys = ['tile_origin', 'tile_geometry', 'tile_data_geometry']
        for key in keys:
            if key in meta:
                meta[key] = to_latlon(meta[key])
        return meta

    # change coordinates to wsg4 degrees
    if geometry_check:
        if geometry_check(meta):
            meta = get_tile_geometry_from_s3(meta)
        else:
            meta = internal_latlon(meta)
    else:
        meta = internal_latlon(meta)

    # rename path key to aws_path
    meta['aws_path'] = meta.pop('path')

    return meta
