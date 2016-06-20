import unittest
from six import iterkeys
from sentinel_s3.crawler import get_product_metadata_path, get_products_metadata_path


class Test(unittest.TestCase):

    def test_get_product_metadata_path(self):

        product = 'S2A_OPER_PRD_MSIL1C_PDMC_20160311T194734_R031_V20160311T011614_20160311T011614'
        v = get_product_metadata_path(product)

        keys = list(iterkeys(v))
        assert len(keys) == 1
        assert 'tiles' in v[keys[0]]
        assert 'metadata' in v[keys[0]]
        assert keys[0] == product

        metadata = v[keys[0]]['metadata'].split('/')
        tiles = v[keys[0]]['tiles'][0].split('/')

        self.assertEqual(metadata[-1], 'metadata.xml')
        self.assertEqual(tiles[-1], 'tileInfo.json')
        self.assertEqual(len(v[product]['tiles']), 2)

    def test_get_products_metadata_path(self):

        v = get_products_metadata_path(2015, 9, 2)

        keys = list(iterkeys(v))
        self.assertEqual(len(keys), 69)
        self.assertTrue('tiles' in v[keys[0]])
        self.assertTrue('metadata' in v[keys[0]])

        metadata = v[keys[0]]['metadata'].split('/')
        tiles = v[keys[0]]['tiles'][0].split('/')

        self.assertEqual(metadata[-1], 'metadata.xml')
        self.assertEqual(tiles[-1], 'tileInfo.json')
