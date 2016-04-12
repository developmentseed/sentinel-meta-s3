import unittest
from sentinel_s3 import daily_metadata


class Test(unittest.TestCase):

    def test_camelcase_underscore(self):
        daily_metadata(2015, 9, 1, '.')
