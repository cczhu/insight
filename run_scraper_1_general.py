"""
Basic Flickr metadata scraper, which extracts dates, long-lat, tags, number of
views and download links (and corresponding length/width of images) of
geotagged images taken within 25 km of Weston Rd. and Eglinton W. Ave. in
Toronto between user-defined start and end dates.

Scraping is done day-by-day from the start to the end dates to optimize the
number of photos retrieved (the Flickr API only returns a representative subset
of all photos taken in a geographic region and over some span of time).
Scraping over fractions of a day is possible by modifying the code such that
min_taken_date and max_taken_date are UNIX timestamps, but the number of
additional photos this yields is minor for a major increase in the number of
API calls.

To use, run on the command line::

    python run_scraper_1_general.py start_date stop_date outname [--secrets] [-v]

where

start_date : str
    Start date, in YYYY-MM-DD form.
stop_date : str
    Stop date, in YYYY-MM-DD form.
outname : str
    Path and filename of output pandas HDF5.  (If the file extension is not
    .hdf5, ".hdf5" will be appended.)
--secrets : flag, optional
    Flickr API key and secret, separated by space.  If not given, attempts to
    import them from `secrets`.
-v, --verbose" : flag, optional
    Print status during run.  Default: True.
"""

import pandas as pd
import time
import datetime
import unidecode as ud
import re

from snapassist.scrapers import scraper as sc
from snapassist.scrapers import postprocessor as ppc

metadata_keys = tuple(key for key, parser in sc.general_metadata_parser)
metadata_types = tuple(parser[0] for key, parser in sc.general_metadata_parser)


def clean_title(raw_title):
    """Clean photo title to get a command-line friendly name."""
    title_cleaned = ud.unidecode(raw_title.lower().strip())
    title_cleaned = re.sub('[^0-9a-zA-Z]+', ' ', title_cleaned).strip()
    return re.sub('\s+', '_', title_cleaned)


def make_date_generator(start_date, stop_date):
    current_date = start_date
    dt = datetime.timedelta(days=1)
    while current_date < stop_date:
        next_date = current_date + dt
        yield (current_date, next_date)
        current_date = next_date


def get_photo_metadata_general(start_date, stop_date, outname,
                               api_key, api_secret, verbose=True):

    # https://chrisalbon.com/python/basics/strings_to_datetime/
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
    stop_date = datetime.datetime.strptime(stop_date, '%Y-%m-%d').date()

    date_generator = make_date_generator(start_date, stop_date)

    # https://www.flickr.com/services/api/flickr.photos.search.html
    base_settings = {'extras': ('description,date_upload,date_taken,geo,'
                                'tags,machine_tags,o_dims,views,url_s,'
                                'url_m,url_l,url_o'),
                     'media': 'photos',
                     'safe_search': 1,
                     'content_type': 1,   # For photos only.
                     'per_page': 500,     # Max value to minimize API calls.
                     'has_geo': True,
                     'lat': 43.68641,     # Long/lat for Weston Rd./Eglinton W.
                     'lon': -79.489219,
                     'radius': 25}        # In km.

    flickrscraper = sc.FlickrScraper(api_key, api_secret, verbose=verbose)

    flickr_h5 = pd.HDFStore(outname, 'w')

    for i, (min_taken_date, max_taken_date) in enumerate(date_generator):

        time.sleep(2)

        # Prep settings.  (Can use UNIX time instead for min_taken_date and
        # max_taken_date, which allows scraping over fractional dates.)
        settings = base_settings.copy()
        settings['min_taken_date'] = min_taken_date.strftime('%Y-%m-%d')
        settings['max_taken_date'] = max_taken_date.strftime('%Y-%m-%d')

        # Grab data.
        try:
            results = flickrscraper.scrape(settings)

            # Dump results.
            results_f = pd.DataFrame(results, columns=metadata_keys)
            results_f['file_title'] = results_f['title'].apply(clean_title)

            flickr_h5["table{i:d}".format(i=i)] = results_f

            if verbose:
                print("For ", min_taken_date, ", got ",
                      len(results_f), " photos.")

        # If that doesn't work, print the error and save what you have.
        except Exception as exc:
            if verbose:
                print("Exception '{0}' raised when parsing photos taken on {1}"
                      .format(str(exc), min_taken_date))
            break

    flickr_h5.flush()
    flickr_h5.close()


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("start_date", type=str,
                        help="Start date, in YYYY-MM-DD form.")
    parser.add_argument("stop_date", type=str,
                        help="Stop date, in YYYY-MM-DD form.")
    parser.add_argument("outname", type=str,
                        help="Path and filename of output pandas HDF5.")
    parser.add_argument("--secrets", default="False",
                        help="Flickr API key and secret, separated by space.")
    parser.add_argument("-v", "--verbose", action="store_true", default=True,
                        help="Print status during run.")
    args = parser.parse_args()

    if args.secrets == "False":
        import secrets
        api_key = secrets.FLICKR_API_KEY
        api_secret = secrets.FLICKR_API_SECRET
    else:
        api_key, api_secret = args.secrets.split()

    if len(args.outname.split(".hdf5")) == 1:
        outname_final = args.outname + ".hdf5"
    else:
        outname_final = args.outname
    outname_raw = outname_final.split(".hdf5")[0] + "_raw.hdf5"

    get_photo_metadata_general(args.start_date, args.stop_date, outname_raw,
                               api_key, api_secret, verbose=args.verbose)

    ppc.combine_master_tables(outname_raw, outname_final)
