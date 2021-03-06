"""
Scraping tool to retrieve Flickr photos.
"""

import numpy as np
import flickrapi
from collections import OrderedDict
import re
import time
import pandas as pd


general_metadata_parser = (
    ('id', (str, 'N/A')),
    ('owner', (str, 'N/A')),
    ('title', (str, 'N/A')),
    ('o_width', (int, -1)),
    ('datetaken', (str, 'N/A')),
    ('views', (str, -1)),
    ('tags', (str, "")),
    ('machine_tags', (str, "")),
    ('latitude', (float, np.nan)),
    ('longitude', (float, np.nan)),
    ('accuracy', (int, -1)),
    ('context', (int, -1)),
    ('place_id', (str, 'N/A')),
    ('woeid', (str, 'N/A')),
    ('url_s', (str, 'N/A')),
    ('width_s', (int, -1)),
    ('height_s', (int, -1)),
    ('url_m', (str, 'N/A')),
    ('width_m', (int, -1)),
    ('height_m', (int, -1)),
    ('url_l', (str, 'N/A')),
    ('width_l', (int, -1)),
    ('height_l', (int, -1)),
    ('url_o', (str, 'N/A')),
    ('width_o', (int, -1)),
    ('height_o', (int, -1)))


def process_general_meta(data, key, parser):
    """Process one piece of general metadata using general_metadata_parser."""
    try:
        return parser[0](data.get(key, parser[1]))
    except Exception:
        return parser[1]


def details_extract_comments(comments):
    try:
        return int(comments['_content'])
    except Exception:
        return -1


def details_extract_description(desc):
    try:
        return str(desc['_content'])
    except Exception:
        return 'N/A'


def details_extract_location(loc):
    try:
        loc_accuracy = int(loc['accuracy'])
        loc_neigh = loc['neighbourhood']
        neigh = loc_neigh['_content']
        neigh_id = loc_neigh['place_id']
        neigh_woeid = loc_neigh['woeid']
        return [loc_accuracy, neigh, neigh_id, neigh_woeid]
    except Exception:
        return [-1, 'N/A', -1, -1]


def details_extract_url(urls):
    try:
        return str(urls['url'][0]['_content'])
    except Exception:
        return 'N/A'


photodetails_parser = (
    ('comments', details_extract_comments),
    ('description', details_extract_description),
    ('location', details_extract_location),
    ('secret', str),
    ('urls', details_extract_url))
photodetails_keys = tuple(key for key, parser in photodetails_parser)


def exif_extract_float(exstring):
    return float(re.findall(r"[-+]?\d*\.\d+|\d+", exstring)[0])


def exif_extract_int(exstring):
    return int(re.findall(r"[-+]?\d+", exstring)[0])


def exif_extract_exposure_time(extime):
    # Strip whitespaces and alphabetical chars.
    extime = re.sub('[A-z\s]', '', extime)
    if extime.startswith('1/'):
        return 1 / int(extime[2:])
    else:
        return float(extime)


exif_parser = {
    'Lens': str,
    'FocalLength': exif_extract_float,
    'FocalLengthIn35mmFormat': exif_extract_float,
    'FNumber': exif_extract_float,
    'ExposureTime': exif_extract_exposure_time,
    'ISO': exif_extract_int}
exif_parser_keys = exif_parser.keys()


exif_parser_default = OrderedDict((('Camera', 'N/A'),
                                   ('Lens', 'N/A'),
                                   ('FocalLength', -1.0),
                                   ('FocalLengthIn35mmFormat', -1.0),
                                   ('FNumber', -1.0),
                                   ('ExposureTime', -1.0),
                                   ('ISO', -1)))
exif_parser_default_keys = tuple(exif_parser_default.keys())


class FlickrScraper:
    """Photo metadata scraper using `flickrapi.FlickrAPI.walk`.

    Parameters
    ----------
    api_key : str
        Flickr site API key.
    api_secret : str
        Flickr site API secret.
    max_count : int, optional
        Maximum number of photos to return per search.  Default: 3000, but
        should be kept to below 4000 to prevent the Flickr API from returning
        repeated values.
    verbose : bool, optional
        Print to screen any exceptions encountered while scraping.
    """

    def __init__(self, api_key, api_secret, max_count=3000, verbose=True):
        self.flickr = flickrapi.FlickrAPI(api_key, api_secret)
        self.max_count = max_count
        self.verbose = bool(verbose)

    def _finite_flickr_walk(self, walker):
        for i in range(self.max_count):
            yield walker.__next__()

    def _get_walker(self, **kwargs):
        """Get generator that calls flickr.photo.search.

        Arguments: https://www.flickr.com/services/api/flickr.photos.search.html
        """
        self.fwalk = self._finite_flickr_walk(self.flickr.walk(**kwargs))

    def scrape(self, settings):
        data = []
        self._get_walker(**settings)
        for i, photo in enumerate(self.fwalk):
            try:
                photo_info = tuple(process_general_meta(photo, key, parser)
                                   for key, parser in general_metadata_parser)
                data.append(photo_info)
            except Exception as exc:
                if self.verbose:
                    excmsg = ""
                    if hasattr(exc, 'message'):
                        excmsg += exc.message
                        print("Exception '{0}' raised when parsing item {1}"
                              .format(excmsg, i))
        return data


class FlickrDetailedScraper:
    """Detailed metadata scraper using `flickrapi.FlickrAPI.photos.getInfo`.

    This function cycles through the general metadata data frame created by
    `FlickrScraper` and returns tables with further details of each photo, such
    as detailed photo descriptions, or EXIF data.

    Parameters
    ----------
    api_key : str
        Flickr site API key.
    api_secret : str
        Flickr site API secret.
    verbose : bool, optional
        Print to screen any exceptions encountered while scraping.
    """

    def __init__(self, api_key, api_secret, verbose=True):

        self.flickrjson = flickrapi.FlickrAPI(api_key, api_secret,
                                              format='parsed-json')
        self.verbose = bool(verbose)

    def _get_exif(self, exif_data):

        found_tags = exif_parser_default.copy()
        if len(exif_data.keys()):
            if 'camera' in exif_data['photo'].keys():
                found_tags['Camera'] = exif_data['photo']['camera']

            exif_data_body = exif_data['photo']['exif']

            for item in exif_data_body:
                itemtag = item['tag']
                if itemtag in exif_parser_keys:
                    try:
                        found_tags[itemtag] = exif_parser[itemtag](
                            item['raw']['_content'])
                    except Exception:
                        pass

        return tuple(found_tags.values())

    def get_photo_details(self, general_df, tsleep=1.):
        """Retrieve comments and descriptions of general metadata entries.

        Because scraping must be done photo-by-photo, must be slowed down by
        pausing between API queries to prevent exceeding the query limit per
        hour of 3600.

        Parameters
        ----------
        general_df : pandas.DataFrame
            General metadata data frame.
        tsleep : float, optional
            Number of seconds to wait between scraping to prevent exceeding the
            Flickr API query limit (3600 times / hour).
        verbose : bool, optional
            If True (default), prints current status and any exceptions.
        """
        photos_data = []

        for i, (ind, row) in enumerate(general_df.iterrows()):

            if self.verbose:
                print("Working on photo", i)

            time.sleep(tsleep)

            try:
                cphotodata = self.flickrjson.photos.getInfo(photo_id=row['id'])
                cphotodata_processed = tuple(
                    parser(cphotodata['photo'][key])
                    for key, parser in photodetails_parser)
                photos_data.append((row['id'],) + cphotodata_processed)
            except Exception as exc:
                if self.verbose:
                    print("Exception '{0}' raised when parsing photo "
                          "with id {1}".format(str(exc), row['id']))

        return pd.DataFrame(photos_data, columns=(('id',) + photodetails_keys))

    def get_exif_data(self, general_df, tsleep=1.):
        """Retrieve comments and descriptions of general metadata entries.

        Because scraping must be done photo-by-photo, must be slowed down by
        pausing between API queries to prevent exceeding the query limit per
        hour of 3600.

        Parameters
        ----------
        general_df : pandas.DataFrame
            General metadata data frame.
        tsleep : float, optional
            Number of seconds to wait between scraping to prevent exceeding the
            Flickr API query limit (3600 times / hour).
        """

        exif_data = []
        exif_index = []

        for i, (ind, row) in enumerate(general_df.iterrows()):

            if self.verbose:
                print("Working on photo", i)

            time.sleep(tsleep)

            try:
                cphotexif = self.flickrjson.photos.getExif(photo_id=row['id'])
                cphotexif_processed = self._get_exif(cphotexif)
                exif_data.append((row['id'],) + cphotexif_processed)
                exif_index.append(ind)
            except Exception as exc:
                if self.verbose:
                    print("Exception '{0}' raised when parsing photo "
                          "with id {1}".format(str(exc), row['id']))

        return pd.DataFrame(exif_data, index=exif_index,
                            columns=(('id',) + exif_parser_default_keys))
