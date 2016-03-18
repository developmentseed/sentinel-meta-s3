
import unittest

from scrawler.main import generate_metadata


class Test(unittest.TestCase):

    def test_camelcase_underscore(self):
        generate_metadata(2015, 9, 1, '.')
