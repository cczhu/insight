import pandas as pd
import numpy as np
import re


def _contains_all(x, search_args_split, search_args_joined):
    split_result = all(item in x for item in search_args_split)
    joined_result = search_args_joined in x
    return (split_result or joined_result)


class FlickrPhotosDatabase:

    def __init__(self, main_table, popular_table):
        self.mtab = pd.read_hdf(main_table, 'table')
        self.poptab = pd.read_hdf(popular_table, 'table')
        ################## REMOVE FOR LATER????######################
        self.mtab['tags'] = self.mtab['tags'].str.split()
        self.poptab['tags'] = self.poptab['tags'].str.split()
        #############################################################
        self.mtab_75percentile_views = np.percentile(self.mtab['views'], 75)

    @staticmethod
    def search_tags(table, phrase):
        phrase_reduced = re.sub('[^0-9A-z\s]', '', phrase.lower())
        search_args_split = phrase_reduced.split()
        search_args_joined = "".join(search_args_split)
        return table['tags'].apply(_contains_all, args=(search_args_split,
                                                        search_args_joined))

    def get_search_results(self, phrase, table='main'):
        if table == 'popular':
            ctab = self.poptab
        else:
            ctab = self.mtab
        search_result_mask = self.search_tags(ctab, phrase)
        return ctab[search_result_mask].copy()