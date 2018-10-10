"""
Flickr EXIF metadata scraper, which extracts camera model and photo settings of
the top 25% most popular photos from the general metadata data frame.

To use, run on the command line::

    python run_scraper_2_exif.py start_date stop_date outname [--secrets] [-v]

where

master_table : str
    Master table, of general metadata.
outname : str
    Path and filename of output pandas HDF5.  (If the file extension is not
    .hdf5, ".hdf5" will be appended.)
division : int
    Number of subdivisions to split popular photos of master table into, in
    line with how ``run_scraper_1_general.py`` works.  This is to prevent
    exceptions from causing total loss of data already scraped.
--secrets : flag, optional
    Flickr API key and secret, separated by space.  If not given, attempts to
    import them from `secrets`.
-v, --verbose" : flag, optional
    Print status during run.  Default: True.
"""

import pandas as pd
import numpy as np

from snapassist.scrapers import scraper as sc
from snapassist.scrapers import postprocessor as ppc


def counter_gen(global_start, global_end, divisions):
    sections = np.linspace(global_start, global_end, divisions + 1, dtype=int)
    if np.unique(sections).size < sections.size:
        raise ValueError('sections bounds are not unique.  Please ensure '
                         'global_end - global_start can evenly be divided '
                         'into divisions')
    for i in range(sections.size - 1):
        yield (sections[i], sections[i + 1])


def get_photo_metadata_exif(master_table, divisions,
                            outname, api_key, api_secret, tsleep=1.,
                            verbose=False):

    if len(outname.split(".hdf5")) == 1:
        outname_final = outname + ".hdf5"
    else:
        outname_final = outname
    outname_raw = outname_final.split(".hdf5")[0] + "_raw.hdf5"

    mtab = pd.read_hdf(master_table, 'table')
    poptab = ppc.get_popular_table(mtab)

    # To save RAM, just in case.
    del mtab

    flickr_h5 = pd.HDFStore(outname_raw, 'w')
    ex_sc = sc.FlickrDetailedScraper(api_key, api_secret, verbose=verbose)

    for i, (start, stop) in enumerate(counter_gen(0, len(poptab), divisions)):
        if verbose:
            print("Working on division {i}".format(i=i))
        cexifs = ex_sc.get_exif_data(poptab.iloc[start:stop], tsleep=tsleep)
        flickr_h5["table{i:d}".format(i=i)] = cexifs

    flickr_h5.flush()
    flickr_h5.close()

    ppc.combine_exif_tables(outname_raw, poptab, outname)


if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument("master_table", type=str,
                        help="Table of general metadata.")
    parser.add_argument("divisions", type=int,
                        help="Number of divisions to split general metadata.")
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

    get_photo_metadata_exif(args.master_table, args.divisions, args.outname,
                            api_key, api_secret, verbose=args.verbose)
