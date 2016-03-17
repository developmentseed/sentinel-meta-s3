import json
import unittest
from collections import OrderedDict

from six import iterkeys
from scrawler.converter import camelcase_underscore, metadata_to_dict, tile_metadata


class Test(unittest.TestCase):

    def test_camelcase_underscore(self):

        assert camelcase_underscore('productName') == 'product_name'
        assert camelcase_underscore('ProductName') == 'product_name'
        assert camelcase_underscore('productname') == 'productname'
        assert camelcase_underscore('product1Name') == 'product1_name'

    def test_metadata_to_dict(self):

        product = metadata_to_dict('tests/samples/metadata.xml')

        assert isinstance(product, OrderedDict)
        assert 'band_list' in product
        assert 'tiles' in product
        assert product['spacecraft_name'] == 'Sentinel-2A'
        assert len(product['band_list']) == 13

        tiles = list(iterkeys(product['tiles']))
        assert len(tiles) == 20

    def test_tile_metadata(self):

        f = open('tests/samples/tileInfo.json', 'r')
        tile_info = json.loads(f.read(), object_pairs_hook=OrderedDict)

        tile = tile_metadata(tile_info, metadata_to_dict('tests/samples/metadata.xml'))

        assert isinstance(tile, OrderedDict)
        assert tile['tile_name'] == 'S2A_OPER_MSI_L1C_TL_SGS__20160316T054120_A003818_T56XNF_N02.01'
        assert tile['utm_zone'] == 56
        assert tile['data_coverage_percentage'] == 65.58
        assert tile['sensing_orbit_direction'] == 'DESCENDING'
        assert len(tile['download_links']['aws_s3']) == 13
