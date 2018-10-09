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

Scikit-learn's `OPTICS module
<http://scikit-learn.org/dev/modules/generated/sklearn.cluster.OPTICS.html>`_ is
currently not available through pip-install, so its code has been included under
``snapassist/sklearn_optics/``.  OPTICS requires `Cython <http://cython.org/>`_ 
(which has C package dependencies).  Once installed, build the ``_optics_inner``
module by running::

    python setup.py build_ext --inplace

in the SnapAssist root folder.

This module will become deprecated when scikit-learn 0.21 is released.

In addition, you must possess two pandas HDF5 databases produced by the Flickr
scrapers associated with SnapAssist (found under the ``scrapers`` folder)
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
