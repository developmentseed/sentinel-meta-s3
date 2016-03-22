sentinel-s3
-----------

|Build Status|

This packages includes a few functions that facilitates extraction of
Sentinel-2's metadata from Amazon S3.

Installation
~~~~~~~~~~~~

::

    $ pip install sentinel-s3

or

::

    $ python setup.py install

Tests
~~~~~

::

    $ python setup.py test

Example
~~~~~~~

.. code:: python

    import logging
    from datetime import date
    from sentinel_s3 import range_metadata


    def main():

        start_date = date(2016, 2, 1)
        end_date = date(2016, 3, 22)

        return range_metadata(start_date, end_date, '.', 20)


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

.. |Build Status| image:: https://travis-ci.org/developmentseed/sentinel-s3.svg?branch=master
   :target: https://travis-ci.org/developmentseed/sentinel-s3
