**********
SnapAssist
**********

Welcome to the repository for SnapAssist, the web application for perfect
picture planning!  SnapAssist leverages geotagged photo metadata scraped from
the `Flickr <https://www.flickr.com/>`_ to determine the most popular
photography viewpoints around the Greater Toronto area.  The app is currently
served (using AWS) at `snapassist.site <https://snapassist.site/>`_.

The SnapAssist repo consists of two components: a set of scrapers to data mine
Flickr using its API and dump the results into a set of pandas data frames 
(stored as HDF5), and a web application that performs the mapping.  The web
application reads these tables in, performs keyword searching to retrieve
relevant photos, and

Requirements
============

The web app is compatible with Python 3.5 (and may work for Python 3.6+), and
requires the following packages::

    branca
    Cython
    Flask
    flickrapi
    folium
    h5py
    hdbscan
    numpy
    pandas
    tables
    scikit-learn
    unidecode

Database Construction
=====================

Snapassist relies on two pandas HDF5 databases::

    master_table_processed.hdf5
    popular_table_processed.hdf5

which hold general photo metadata of all photos scraped, and camera model and
photo EXIF data of the most popular 25% of all photos scraped, respectively. 
Scraping for the EXIF data needs to be done photo-by-photo, making it
considerably more expensive than getting the general metadata, hence why it is
only done on the most popular photos.

To generate these tables, SnapAssist has a ``scrapers`` module, which is
accessed by the ``run_scraper_...py`` files in the root directory.  Details on
how to run each are in their respective docstrings.

All the scrapers require `Flickr API keys
<https://www.flickr.com/services/api/misc.api_keys.html>`_, which can either be
manually passed to the scraper, or stored in a ``secrets.py`` file that
contains the following::

    # Flickr API key.
    FLICKR_API_KEY = '<YOUR API KEY HERE>'
    FLICKR_API_SECRET = '<YOUR API SECRET HERE'

The scrapers will attempt to ``import secrets``, so include the path to your
file in your Python PATH.  I recommend running SnapAssist in a virtualenv, and
adding a ``secrets.py`` file in a folder included in the virtualenv's path (see
`adding .pth files <https://docs.python.org/3/install/index.html#modifying-python-s-search-path>`_).

The overall scraping workflow (with generic table names) is

1. Run the general scraper::

      python run_scraper_1_general.py <START_DATE> <END_DATE> 'master_table.hdf5'-v

2. Run the EXIF scraper.  Here, ``DIVISIONS`` is the number of blocks to
   subdivide the 25% most popular photos in master table into, to avoid losing
   all the data already scrapedif an exception is raised in the script; a
   reasonable number is 10::

      python run_scraper_2_exif.py 'master_table.hdf5' <DIVISIONS> 'popular_table.hdf5'

3. In the Python interpreter of your choice, run::

      from snapassist.scrapers import postprocessor as ppc
      read_and_preprocess_tables(
        table_folder='./',
        master_table='master_table.hdf5',
        popular_table='popular_table.hdf5',
        master_table_processed='master_table_processed.hdf5',
        popular_table_processed='popular_table_processed.hdf5')

Deploying the Web Application
=============================

With databases in hand

OPTICS
------

Scikit-learn's `OPTICS module
<http://scikit-learn.org/dev/modules/generated/sklearn.cluster.OPTICS.html>`_ is
currently not available through pip-install, so its code has been included under
``snapassist/sklearn_optics/``.  OPTICS requires `Cython <http://cython.org/>`_ 
(which has C package dependencies).  Once installed, build the ``_optics_inner``
module by running::

    python setup.py build_ext --inplace

in the SnapAssist root folder.

This module will become deprecated when scikit-learn 0.21 is released.

Running the Web App
-------------------

Before running the web app, you must tell SnapAssist where your tables are by
setting the environmental variable::

    export FLICKR_TABLES_FOLDER='/PATH/TO/YOUR/FOLDER/'

To run the app locally

Credits
=======

This package was created by Chenchong Charles Zhu as part of the Insight Data
Science fellowship.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
