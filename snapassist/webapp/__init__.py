# -*- coding: utf-8 -*-

__author__ = """Chenchong Zhu"""
__email__ = 'chenchong.zhu@gmail.com'
__version__ = '0.1.0'

from flask import Flask
import os
from .. import database


# Do `export FLICKR_TABLE_FOLDER=XXXXXX`. in the same command prompt before
# running the flask app.
FLICKR_TABLES_FOLDER = os.environ.get('FLICKR_TABLES_FOLDER') or './'
flickr_tables_main = os.path.join(FLICKR_TABLES_FOLDER +
                                  'master_table_processed.hdf5')
flickr_tables_popular = os.path.join(FLICKR_TABLES_FOLDER +
                                     'popular_table_processed.hdf5')

# Launch app.
app = Flask(__name__)

db = database.FlickrPhotosDatabase(flickr_tables_main, flickr_tables_popular)
toronto_longlat = database.TorontoLongLat()
global_min_samples = 15
global_max_eps_scaling = 1.
master_sigma_cut = 2.5


# Circular import, so needs to be defined after `app` is.
from . import views
