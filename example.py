import logging
from datetime import date, timedelta
from scrawler.main import generate_metadata


def main():

    start_date = date(2015, 11, 28)
    end_date = date(2015, 12, 31)

    delta = end_date - start_date

    dates = []

    for i in range(delta.days + 1):
        dates.append(start_date + timedelta(days=i))

    for d in dates:
        print('Getting metadata of {0}-{1}-{2}'.format(d.year, d.month, d.day))
        generate_metadata(d.year, d.month, d.day, '.')


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
