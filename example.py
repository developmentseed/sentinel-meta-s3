import logging
from datetime import date
from sentinel_s3 import range_metadata, s3_writer


def main():

    start_date = date(2015, 9, 2)
    end_date = date(2015, 9, 2)

    return range_metadata(start_date, end_date, '.', 0, [s3_writer])


if __name__ == '__main__':
    logger = logging.getLogger('sentinel.meta.s3')
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    result = main()

    print(result)
