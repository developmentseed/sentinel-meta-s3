import json
import datetime

import boto3

bucket_name = 'sentinel-s2-l1c'
s3 = boto3.resource('s3', region_name='eu-central-1')
bucket = s3.Bucket(bucket_name)


def get_tile_metadata_path(path):

    meta_obj = s3.Object(bucket_name, path)

    meta = json.loads(meta_obj.get()['Body'].read().decode())

    paths = []
    for tile in meta['tiles']:
        paths.append(tile['path'] + '/tileInfo.json')

    return paths


def get_product_metadata_path(product_name):
    """ gets a single products metadata """

    string_date = product_name.split('_')[-1]
    date = datetime.datetime.strptime(string_date, '%Y%m%dT%H%M%S')
    path = 'products/{0}/{1}/{2}/{3}'.format(date.year, date.month, date.day, product_name)

    return {
        product_name: {
            'metadata': '{0}/{1}'.format(path, 'metadata.xml'),
            'tiles': get_tile_metadata_path('{0}/{1}'.format(path, 'productInfo.json'))
        }
    }


def get_products_metadata_path(year, month, day):
    """ Get paths to multiple products metadata """

    products = {}
    path = 'products/{0}/{1}/{2}/'.format(year, month, day)
    for key in bucket.objects.filter(Prefix=path):
        product_path = key.key.replace(path, '').split('/')
        name = product_path[0]
        if name not in products:
            products[name] = {}

        if product_path[1] == 'metadata.xml':
            products[name]['metadata'] = key.key

        if product_path[1] == 'productInfo.json':
            products[name]['tiles'] = get_tile_metadata_path(key.key)

    return products
