import os
import json
import logging
import requests
from copy import copy
from six import iteritems, iterkeys

from scrawler.crawler import get_product_metadata_path
from scrawler.converter import metadata_to_dict, tile_metadata


logger = logging.getLogger('sentinel.meta.s3')


def mkdirp(path):

    if not os.path.exists(path):
        os.makedirs(path)


def generate_metadata(year, month, day, dst_folder):

    # create folders
    year_dir = os.path.join(dst_folder, str(year))
    month_dir = os.path.join(year_dir, str(month))
    day_dir = os.path.join(month_dir, str(day))

    s3_url = 'http://sentinel-s2-l1c.s3.amazonaws.com'
    product_list = get_product_metadata_path(year, month, day)

    logger.info('There are %s products in %s-%s-%s' % (len(list(iterkeys(product_list))),
                                                       year, month, day))

    for name, product in iteritems(product_list):

        mkdirp(year_dir)
        mkdirp(month_dir)
        mkdirp(day_dir)

        product_info = requests.get('{0}/{1}'.format(s3_url, product['metadata']), stream=True)
        product_metadata = metadata_to_dict(product_info.raw)

        for tile in product['tiles']:
            tile_info = requests.get('{0}/{1}'.format(s3_url, tile))
            try:
                metadata = tile_metadata(tile_info.json(), copy(product_metadata))

                product_dir = os.path.join(day_dir, metadata['product_name'])
                mkdirp(product_dir)

                f = open(os.path.join(product_dir, metadata['tile_name'] + '.json'), 'w')
                f.write(json.dumps(metadata))
                f.close()

                logger.info('Saving to disk: %s' % metadata['tile_name'])
            except json.decoder.JSONDecodeError:
                print(tile_info.status_code)
                print(tile_info.content)
                logger.info('Tile: %s was not found' % tile)
