import logging
from datetime import date
from scrawler.main import range_metadata


def main():

    start_date = date(2016, 1, 1)
    end_date = date(2016, 3, 22)

    return range_metadata(start_date, end_date, '.', 5)


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
