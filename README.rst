==========
SnapAssist
==========

Welcome to the repository for SnapAssist, the web application for perfect
picture planning!  SnapAssist leverages geotagged photo metadata scraped from
the `Flickr <https://www.flickr.com/>`_ alongside density-based clustering to
determine the most popular photography viewpoints around the Greater Toronto
area.  The app is currently served (using AWS) at
`snapassist.site <https://snapassist.site/>`_.

Requirements
------------

The web app is compatible with Python 3.5 (and may work for Python 3.6+), and
requires the following packages::

    branca
    Flask
    flickrapi
    folium
    h5py
    hdbscan
    numpy
    pandas
    tables
    scikit-learn

In addition, you must possess two pandas HDF5 databases produced by the Flickr
scrapers associated with SnapAssist (found under the `scrapers` folder)
named::

    master_table_processed.hdf5
    popular_table_processed.hdf5

which hold general photo metadata of all photos scraped, and camera model and
photo EXIF data of the most popular 25% of all photos scraped, respectively.

To tell SnapAssist where these tables are, you must set an environmental
variable indicating the path to the tables' folder::

    export FLICKR_TABLES_FOLDER='/PATH/TO/YOUR/FOLDER/'

To create the the tables, please see the files in the `scrapers` folder.

Credits
-------

This package was created by Chenchong Charles Zhu as part of the Insight Data
Science fellowship.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
