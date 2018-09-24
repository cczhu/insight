import pandas as pd
import numpy as np

import datetime
import unidecode as ud
import re


def clean_title(raw_title):
    """Clean photo title to get a command-line friendly name."""
    title_cleaned = ud.unidecode(raw_title.strip())
    title_cleaned = re.sub('[^0-9a-zA-Z]+', ' ', title_cleaned).strip()
    return title_cleaned


def extract_times(results):
    results['datetaken'] = results['datetaken'].apply(
        datetime.datetime.strptime, args=('%Y-%m-%d %H:%M:%S',))
    results['hour'] = results['datetaken'].apply(lambda x: x.hour)
    results['month'] = results['datetaken'].apply(lambda x: x.month)


def read_and_preprocess_tables(
        table_folder='/home/cczhu/InsightData/flickr_meta/',
        master_table='master_table.hdf5',
        popular_table='master_table_popular.hdf5',
        popular_exif='master_table_popular_exif.hdf5',
        savepath='/home/cczhu/InsightData/flickr_meta_processed/',
        master_table_processed='master_table_processed.hdf5',
        popular_table_processed='popular_table_processed.hdf5'):

    # Read tables.
    mtab = pd.read_hdf(table_folder + master_table, 'table')
    poptab = pd.read_hdf(table_folder + popular_table, 'table')
    popexif = pd.read_hdf(table_folder + popular_exif, 'table')

    # Join popular and EXIF tables on index, then double-check IDs.
    poptab = poptab.join(popexif, how='left', rsuffix='_exif')
    has_id_exif = poptab['id_exif'].notnull()
    assert np.all((poptab.loc[has_id_exif, 'id'] ==
                   poptab.loc[has_id_exif, 'id_exif'])), (
        "id mismatch between EXIF and popular photos datasets!")

    poptab.drop(columns='id_exif', inplace=True)

    # Basic preprocessing.
    mtab['views'] = mtab['views'].astype(int)
    poptab['views'] = poptab['views'].astype(int)
    mtab['title_cleaned'] = mtab['title'].apply(clean_title)
    poptab['title_cleaned'] = poptab['title'].apply(clean_title)

    extract_times(mtab)
    extract_times(poptab)

    mtab.to_hdf(savepath + master_table_processed, 'table')
    poptab.to_hdf(savepath + popular_table_processed, 'table')
