import pandas as pd
import numpy as np
import re


def _contains_all(x, wanted):
    return all(item in x for item in wanted)


class FlickrPhotosDatabase:

    def __init__(self, main_table, popular_table):
        self.mtab = pd.read_hdf(main_table, 'table')
        self.poptab = pd.read_hdf(popular_table, 'table')
        self.mtab_75percentile_views = np.percentile(self.mtab['views'], 75)

    @staticmethod
    def search_tags(table, phrase):
        phrase_reduced = re.sub('[^0-9A-z\s]', '', phrase.lower())
        search_args = phrase_reduced.split()
        return table['tags'].apply(_contains_all, args=(search_args,))

    def get_search_results(self, phrase, table='main'):
        if table == 'popular':
            ctab = self.poptab
        else:
            ctab = self.mtab
        search_result_mask = self.search_tags(ctab, phrase)
        return ctab[search_result_mask]
