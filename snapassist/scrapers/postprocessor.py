import pandas as pd
import numpy as np

import datetime
import unidecode as ud
import re


def combine_master_tables(raw_master_table, outname):
    tables = pd.HDFStore(raw_master_table, 'r')
    bigtable = tables['table0']
    for i in range(1, len(tables.keys())):
        bigtable = bigtable.append(tables['table{i}'.format(i=i)])
        bigtable.reset_index(drop=True, inplace=True)
    tables.close()
    bigtable.drop_duplicates(subset='id', keep='first', inplace=True)
    bigtable.to_hdf(outname, 'table')


def get_popular_table(mtab):
    mtab['views'] = mtab['views'].astype(int)
    return mtab.loc[
        mtab['views'] > np.percentile(mtab['views'], 75), :].copy()


def combine_exif_tables(raw_exif_table_name, poptab, outname):
    tables = pd.HDFStore(raw_exif_table_name, 'r')
    bigtable = tables['table0']
    for i in range(1, len(tables.keys())):
        bigtable = bigtable.append(tables['table{i}'.format(i=i)])
        bigtable.reset_index(drop=True, inplace=True)
    tables.close()
    bigtable.drop_duplicates(subset='id', keep='first', inplace=True)

    # Reset the big table's index to be that of poptab.
    bigtable.set_index(poptab.index, inplace=True)

    # Join popular and EXIF tables on index, then double-check IDs.
    poptab = poptab.join(bigtable, how='left', rsuffix='_exif')
    has_id_exif = poptab['id_exif'].notnull()
    assert np.all((poptab.loc[has_id_exif, 'id'] ==
                   poptab.loc[has_id_exif, 'id_exif'])), (
        "id mismatch between EXIF and popular photos datasets!")

    poptab.drop(columns='id_exif', inplace=True)
    poptab.to_hdf(outname, 'table')


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
        table_folder='./',
        master_table='master_table.hdf5',
        popular_table='popular_table.hdf5',
        master_table_processed='master_table_processed.hdf5',
        popular_table_processed='popular_table_processed.hdf5'):

    # Read tables.
    mtab = pd.read_hdf(table_folder + master_table, 'table')
    poptab = pd.read_hdf(table_folder + popular_table, 'table')

    # Basic preprocessing.
    mtab['views'] = mtab['views'].astype(int)
    poptab['views'] = poptab['views'].astype(int)
    mtab['title_cleaned'] = mtab['title'].apply(clean_title)
    poptab['title_cleaned'] = poptab['title'].apply(clean_title)

    extract_times(mtab)
    extract_times(poptab)

    mtab.to_hdf(table_folder + master_table_processed, 'table')
    poptab.to_hdf(table_folder + popular_table_processed, 'table')
