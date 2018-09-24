import pandas as pd
import numpy as np
import re


class FlickrPhotosDatabase():

    def __init__(self, main_table, popular_table):
        self.mtab = pd.read_hdf(main_table, 'table')
        self.poptab = pd.read_hdf(popular_table, 'table')

    @staticmethod
    def _contains_all(x, wanted):
        return all(item in x for item in wanted)

    @staticmethod
    def make_flickr_link(row):
        return 'https://www.flickr.com/photos/{owner}/{photoid}'.format(
            photoid=row['id'], owner=row['owner'])

    def search_tags(self, phrase, table='main'):
        if table == 'popular':
            ctab = self.poptab
        else:
            ctab = self.mtab
        phrase_reduced = re.sub('[^0-9A-z\s]', '', phrase.lower())
        search_args = phrase_reduced.split()
        return ctab['tags'].apply(self._contains_all, args=(search_args,))
