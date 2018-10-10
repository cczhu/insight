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
application reads these tables in and performs keyword searching to retrieve
relevant photos.  It then clusters the relevant photos' geolocations to
determine regions where many people have taken pictures, and calculates summary
statistics for each cluster.  Finally, the photos' locations and cluster
summaries are displayed on an interactive map.  For more information about each,
please see the sections below!

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

Data Mining Flickr
==================

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

The SnapAssist Web Application
==============================

With databases in hand, we can now run the web app.  The app loads the pandas
tables on launch.  When a user enters a keyword query, the app performs a tag
search of the query on the tables[#]_.  The matching photos' geolocations are
then passed to the OPTICS clustering algorithm (taken from the development
version of scikit-learn) to determine high-density clusters of photos.  For each
cluster, the app calculates the number of photos, average number of views per
photo, and a cluster center defined by the popularity-weighted mean longitude
and latitude of the cluster's photos.  The clusters are ranked by their average
views to photo number ratio::

    R = avg. views / number of photos

which is a joint measure of the quality of the photos taken at a location and
how original the location is.  Finally, all photos and clusters are plotted on a
map of Toronto using Leaflet.js through Folium.

.. [#] Currently, exact keyword matching is used (with some intelligent
   handling of white space.  I had considered creating an embedded space of tags
   and using semantic similarity, but there is no obvious way to set a critical
   similarity beyond which two photos are considered different.  Without this,
   there is no natural boundary for the number of photos to return to the user.

OPTICS
------

SnapAssist uses clustering in geolocation to find and characterize popular
photo locations.  This translates to finding clusters of high density against a
background of lower density, which is a task for density-based algorithms like
`DBSCAN <http://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html>`_.

DBSCAN determines clusters by picking a point from the data and determining
whether there are more than the minimum number of neighbouring points within a
radius :math:`\epsilon`.  If so, the point is considered a core member of its
cluster.  It then performs the same check for all of the neighbouring points. 
This continues until no more points can be walked to.  Points without enough
neighbours are considered background noise.  Here's a great animation from
`David Sheehan <https://dashee87.github.io/data%20science/general/Clustering-with-Scikit-with-GIFs/>`_
showing the process:

.. image:: https://dashee87.github.io/images/DBSCAN_tutorial.gif
    :alt: DBSCAN GIF by dashee
    :align: "center"

DBSCAN works well for clustering on a background of uniform density, but not for
one where the density changes, which is frequently the case for SnapAssist. 
This is why it uses the `OPTICS algorithm
<http://scikit-learn.org/dev/modules/clustering.html#optics>`_, which replaces
checking for neighbours within a fixed :math:`\epsilon` with creating a
"reachability graph" that encodes how far each point is from its nearest
neighbours.  Clusters are determined by finding local minima in reachability,
then moving outward until the increase in reachability moving from one point to
the next becomes too high.

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

To run the app locally, use the ``run_webapp.py`` script.  On a server, we
recommend using `gunicorn <https://gunicorn.org/>` server, which is launched
using the command::

    gunicorn snapassist.web::app

To use gunicorn, you will need to add the ``snapassist`` root folder to your
Python PATH.

Credits
=======

This package was created by Chenchong Charles Zhu as part of the Insight Data
Science fellowship.

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
