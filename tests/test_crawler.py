import unittest
from six import iterkeys
from sentinel_s3.crawler import get_product_metadata_path


class Test(unittest.TestCase):

    def test_get_product_metadata_path(self):

        v = get_product_metadata_path(2015, 9, 2)

        keys = list(iterkeys(v))
        assert len(keys) == 14
        assert 'tiles' in v[keys[0]]
        assert 'metadata' in v[keys[0]]

        metadata = v[keys[0]]['metadata'].split('/')
        tiles = v[keys[0]]['tiles'][0].split('/')

        assert metadata[-1] == 'metadata.xml'
        assert tiles[-1] == 'tileInfo.json'
