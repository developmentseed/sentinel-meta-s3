import json
import unittest
from copy import copy
from collections import OrderedDict

from six import iterkeys
from scrawler.converter import camelcase_underscore, metadata_to_dict, tile_metadata, to_latlon


class Test(unittest.TestCase):

    def test_camelcase_underscore(self):

        assert camelcase_underscore('productName') == 'product_name'
        assert camelcase_underscore('ProductName') == 'product_name'
        assert camelcase_underscore('productname') == 'productname'
        assert camelcase_underscore('product1Name') == 'product1_name'

    def test_metadata_to_dict(self):

        xml = open('tests/samples/metadata.xml')
        product = metadata_to_dict(xml)

        assert isinstance(product, OrderedDict)
        assert 'band_list' in product
        assert 'tiles' in product
        assert product['spacecraft_name'] == 'Sentinel-2A'
        assert len(product['band_list']) == 13

        tiles = list(iterkeys(product['tiles']))
        assert len(tiles) == 20

    def test_tile_metadata(self):

        f = open('tests/samples/tileInfo.json', 'rb')
        tile_info = json.loads(f.read().decode(), object_pairs_hook=OrderedDict)

        tile = tile_metadata(tile_info, metadata_to_dict('tests/samples/metadata.xml'))

        assert isinstance(tile, OrderedDict)
        assert tile['thumbnail'] == 'http://sentinel-s2-l1c.s3.amazonaws.com/tiles/56/X/NF/2016/3/16/0/preview.jp2'
        assert tile['tile_name'] == 'S2A_OPER_MSI_L1C_TL_SGS__20160316T054120_A003818_T56XNF_N02.01'
        assert tile['utm_zone'] == 56
        assert tile['data_coverage_percentage'] == 65.58
        assert tile['sensing_orbit_direction'] == 'DESCENDING'
        assert len(tile['download_links']['aws_s3']) == 13
        assert tile['tile_origin']['crs']['properties']['name'] == 'urn:ogc:def:crs:EPSG:8.9:4326'

    def test_to_latlon(self):

        geojson = {
            'type': 'Polygon',
            'coordinates': [
                [
                    [448938.374906865, 2500019.0],
                    [509759.0, 2500019.0],
                    [509759.0, 2390221.0],
                    [424439.204990156, 2390221.0],
                    [430306.260834363, 2416547.808440298],
                    [444965.351229892, 2482150.64898733],
                    [448938.374906865, 2500019.0]
                ]
            ],
            'crs': {'type': 'name', 'properties': {'name': 'urn:ogc:def:crs:EPSG:8.8.1:32632'}}
        }

        gj = to_latlon(copy(geojson))
        assert gj['coordinates'][0][0] != geojson['coordinates'][0][0]
        assert gj['crs']['properties']['name'] == 'urn:ogc:def:crs:EPSG:8.9:4326'
