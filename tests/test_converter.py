import json
import unittest
from copy import copy
from collections import OrderedDict

from six import iterkeys
from sentinel_s3.converter import (camelcase_underscore, metadata_to_dict, tile_metadata, to_latlon,
                                   get_tile_geometry, convert_coordinates)


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

        # Make sure bands urls are left padded
        d_link = tile['download_links']['aws_s3'][0].split('.')[-2].split('/')
        assert d_link[-1] == 'B01'

    def test_tile_metadata_with_geometry_check(self):

        def geometry_check(meta):
            if meta['latitude_band'] == 'N':
                return False

            return True

        f = open('tests/samples/tileInfo.json', 'rb')
        tile_info = json.loads(f.read().decode(), object_pairs_hook=OrderedDict)

        tile = tile_metadata(tile_info, metadata_to_dict('tests/samples/metadata.xml'), geometry_check)

        assert isinstance(tile, OrderedDict)
        assert tile['thumbnail'] == 'http://sentinel-s2-l1c.s3.amazonaws.com/tiles/56/X/NF/2016/3/16/0/preview.jp2'
        assert tile['tile_name'] == 'S2A_OPER_MSI_L1C_TL_SGS__20160316T054120_A003818_T56XNF_N02.01'
        assert tile['utm_zone'] == 56
        assert tile['data_coverage_percentage'] == 65.58
        assert tile['sensing_orbit_direction'] == 'DESCENDING'
        assert len(tile['download_links']['aws_s3']) == 13
        assert tile['tile_origin']['crs']['properties']['name'] == 'urn:ogc:def:crs:EPSG:8.9:4326'

        # Make sure bands urls are left padded
        d_link = tile['download_links']['aws_s3'][0].split('.')[-2].split('/')
        assert d_link[-1] == 'B01'

    def test_to_latlon_edge_of_coordinate_system(self):

        geojson = {
            "type": "Polygon",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "urn:ogc:def:crs:EPSG:8.8.1:32601"
                }
            },
            "coordinates": [
                [
                    [
                        336706.875271381,
                        7799999.0
                    ],
                    [
                        409799.0,
                        7799999.0
                    ],
                    [
                        409799.0,
                        7690201.0
                    ],
                    [
                        300001.0,
                        7690201.0
                    ],
                    [
                        300001.0,
                        7728957.392986406
                    ],
                    [
                        315164.079827873,
                        7758207.990416902
                    ],
                    [
                        330501.865974295,
                        7787926.032465892
                    ],
                    [
                        336706.875271381,
                        7799999.0
                    ]
                ]
            ]
        }

        gj = to_latlon(copy(geojson))
        self.assertNotEqual(gj['coordinates'][0][0], geojson['coordinates'][0][0])
        self.assertEqual(gj['crs']['properties']['name'], 'urn:ogc:def:crs:EPSG:8.9:4326')
        self.assertAlmostEqual(gj['coordinates'][0][1][0], 180.60306, 4)

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

    def test_get_tile_geometry(self):

        tiles = {
            'partial_right': {
                'path': 'tests/samples/B01_right.jp2',
                'tile': [-75.3723, -74.8924],
                'data': [-75.0555, -75.3723],
                'epsg': 32618
            },
            'partial_left': {
                'path': 'tests/samples/B01_left.jp2',
                'tile': [-62.1004, -61.113],
                'data': [-62.1002, -62.0978],
                'epsg': 32620
            },
            'full': {
                'path': 'tests/samples/B01_full.jp2',
                'tile': [-67.4893, -67.4893],
                'data': [-67.4893, -67.4893],
                'epsg': 32620
            },
            'edge_case': {
                'path': 'tests/samples/B01_multi.jp2',
                'tile': [-69.0002, -68.8339],
                'data': [-68.9683, -68.8339],
                'epsg': 32619
            },
        }

        for t in iterkeys(tiles):
            print(t)
            (tile, data) = get_tile_geometry(tiles[t]['path'], tiles[t]['epsg'])

            fc = {
                'type': 'FeatureCollection',
                'features': []
            }

            for g in [data]:
                f = {
                    'type': 'Feature',
                    'properties': {},
                    'geometry': g
                }
                fc['features'].append(f)

            # # uncommen to write the results to disk for testing
            # f = open('test_%s.geojson' % t, 'w')
            # f.write(json.dumps(fc))

            for i in range(0, 2):
                self.assertEqual(tiles[t]['tile'][i], round(tile['coordinates'][0][i][0], 4))
                self.assertEqual(tiles[t]['data'][i], round(data['coordinates'][0][i][0], 4))
