import os
import errno
import shutil
import unittest
from tempfile import mkdtemp
from sentinel_s3 import daily_metadata, single_metadata, file_writer


class Test(unittest.TestCase):

    def setUp(self):
        self.tmp_folder = mkdtemp()

    def tearDown(self):
        try:
            shutil.rmtree(self.tmp_folder)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def test_daily_metadata_with_no_results(self):
        # run with a date that doesn't exist
        daily_metadata(2015, 9, 1, '.')

    def test_single_metadata(self):
        product = 'S2A_OPER_PRD_MSIL1C_PDMC_20160311T194734_R031_V20160311T011614_20160311T011614'
        metas = []

        def retainer(d, meta):
            metas.append(meta)

        counter = single_metadata(product, self.tmp_folder, writers=[file_writer, retainer])

        self.assertEqual(len(os.listdir(self.tmp_folder)), 2)
        self.assertEqual(counter['saved_tiles'], 2)
        self.assertEqual(counter['products'], 1)

        self.assertTrue(isinstance(metas[0], dict))
        self.assertEqual(metas[0]['product_name'], product)
