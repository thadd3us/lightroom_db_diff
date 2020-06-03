"""Compares two versions of a Lightroom database.

Example command line:

python3 db_diff.py \
    --db1 "/Users/thad/Dropbox/thad/Lightrooom/Backups/2020-02-27 0339/Lightroom Catalog-4.lrcat.zip" \
    --db2 "/Users/thad/Dropbox/thad/Lightrooom/Backups/2020-05-12 1526/Lightroom Catalog-4.lrcat.zip" \
    --alsologtostderr

TODO:
* Labels, collections, faces.
* Publish on github
"""

import enum
import glob
import maya
import os
import pandas as pd
import sqlite3
import sys
import zipfile

from absl import app
from absl import flags
import logging

from typing import Iterable, Text

FLAGS = flags.FLAGS
flags.DEFINE_string('db1', None, 'First database.')
flags.DEFINE_string('db2', None, 'Second database.')

DB1_SUFFIX = '_db1'
DB2_SUFFIX = '_db2'

DIFF_TYPE = 'DIFF_TYPE'
VALUE_DB1 = 'value' + DB1_SUFFIX
VALUE_DB2 = 'value' + DB2_SUFFIX
VALUE_DELTA = 'value_delta'


def maybe_unzip(filename: str) -> str:
  """If a catalog is a zip file, extract to a known cache location."""
  if not filename.endswith('.zip'):
    logging.info('Not a zipfile, no need to extract.')
    return filename
  filename_without_slash = filename.replace('/', '_')
  dest_dir = f'/tmp/{filename_without_slash}'
  if not os.path.exists(dest_dir):
    logging.info('Extracting to %s', dest_dir)
    with zipfile.ZipFile(filename) as zf:
      zf.extractall(dest_dir)
  else:
    logging.info('Already extracted.')

  dest_dir_contents = glob.glob(os.path.join(dest_dir, '*.lrcat'))
  assert len(dest_dir_contents) == 1, dest_dir_contents
  return os.path.join(dest_dir, dest_dir_contents[0])


@enum.unique
class Column(enum.Enum):
  ROOT_FILE = 'Adobe_images_rootFile'
  CAPTION = 'AgLibraryIPTC_caption'
  GPS_LATITUDE = 'AgHarvestedExifMetadata_gpsLatitude'
  GPS_LONGITUDE = 'AgHarvestedExifMetadata_gpsLongitude'
  RATING = 'Adobe_images_rating'
  COLOR_LABELS = 'Adobe_images_colorLabels'
  CAPTURE_TIME = 'Adobe_images_captureTime'
  HASH = 'AgLibraryFile_importHash'
  ID_GLOBAL = 'Adobe_images_id_global'
  PARSED_CAPTURE_TIME = 'PARSED_CAPTURE_TIME'

  KEYWORD = 'AgLibraryKeyword_name'
  COLLECTION = 'AgLibraryCollection_name'


DIFF_COLUMNS = [
  Column.CAPTION,
  Column.GPS_LATITUDE,
  Column.GPS_LONGITUDE,
  Column.RATING,
  Column.COLOR_LABELS,
  Column.PARSED_CAPTURE_TIME,
  Column.HASH,
]


REPORT_COLUMNS = [
  'AgLibraryFile_idx_filename' + DB1_SUFFIX,
  'AgLibraryFolder_pathFromRoot' + DB1_SUFFIX,
  'AgLibraryRootFolder_absolutePath' + DB1_SUFFIX,
]

SORT_COLUMNS = [
  'DIFF_TYPE',
  'AgLibraryRootFolder_absolutePath' + DB1_SUFFIX,
  'AgLibraryFolder_pathFromRoot' + DB1_SUFFIX,
  'AgLibraryFile_idx_filename' + DB1_SUFFIX,
]

VACUOUS_CAPTIONS = set([
  '',
  'OLYMPUS DIGITAL CAMERA',
  'Exif JPEG',
])

TABLE_MARKER_PREFIX = 'TABLE_MARKER_'

QUERY_SNIPPET_SELECT_IMAGE_LOCATION = """
    0 AS TABLE_MARKER_Adobe_images,
    Adobe_images.*,
    0 AS TABLE_MARKER_AgLibraryFile,
    AgLibraryFile.*,
    0 AS TABLE_MARKER_AgLibraryFolder,
    AgLibraryFolder.*,
    0 AS TABLE_MARKER_AgLibraryRootFolder,
    AgLibraryRootFolder.*
"""

QUERY_SNIPPET_JOIN_IMAGE_LOCATION = """
LEFT JOIN AgLibraryFile ON AgLibraryFile.id_local = Adobe_images.rootFile
LEFT JOIN AgLibraryFolder ON AgLibraryFolder.id_local = AgLibraryFile.folder
LEFT JOIN AgLibraryRootFolder ON AgLibraryRootFolder.id_local = AgLibraryFolder.rootFolder
"""

# Using *s below since I don't know the DB schema well, and want to notice
# if new things appear.
# Using dummy columns to mark which columns come from which tables.
QUERY_IMAGES = f"""
SELECT
    0 AS TABLE_MARKER_AgLibraryIPTC,
    AgLibraryIPTC.*,
    0 AS TABLE_MARKER_AgHarvestedExifMetadata,
    AgHarvestedExifMetadata.*,
    {QUERY_SNIPPET_SELECT_IMAGE_LOCATION}
FROM Adobe_images
LEFT JOIN AgLibraryIPTC ON AgLibraryIPTC.image = Adobe_images.id_local
LEFT JOIN AgHarvestedExifMetadata ON AgHarvestedExifMetadata.image = Adobe_images.id_local
{QUERY_SNIPPET_JOIN_IMAGE_LOCATION}
;
"""


QUERY_KEYWORDS = f"""
SELECT
    0 AS TABLE_MARKER_AgLibraryKeywordImage,
    AgLibraryKeywordImage.*,
    0 AS TABLE_MARKER_AgLibraryKeyword,
    AgLibraryKeyword.*,
    {QUERY_SNIPPET_SELECT_IMAGE_LOCATION}
FROM AgLibraryKeywordImage 
LEFT JOIN Adobe_images ON Adobe_images.id_local = AgLibraryKeywordImage.image
LEFT JOIN AgLibraryKeyword ON AgLibraryKeyword.id_local = AgLibraryKeywordImage.tag
{QUERY_SNIPPET_JOIN_IMAGE_LOCATION}
;
"""


QUERY_COLLECTIONS = f"""
SELECT
    0 AS TABLE_MARKER_AgLibraryCollectionImage,
    AgLibraryCollectionImage.*,
    0 AS TABLE_MARKER_AgLibraryCollection,
    AgLibraryCollection.*,
    {QUERY_SNIPPET_SELECT_IMAGE_LOCATION}
FROM AgLibraryCollectionImage 
LEFT JOIN Adobe_images ON Adobe_images.id_local = AgLibraryCollectionImage.image
LEFT JOIN AgLibraryCollection ON AgLibraryCollection.id_local = AgLibraryCollectionImage.collection
{QUERY_SNIPPET_JOIN_IMAGE_LOCATION}
;
"""


def parse_date_time(date_time_str):
  if date_time_str is None:
    return None
  try:
    return maya.parse(date_time_str)
  except ValueError as e:
    logging.error('Unable to parse time: %s\n%s', date_time_str, e)
  return None


class LightroomDb(object):
  
  def __init__(self):
    self.images_df = None
    self.keywords_df = None
    self.collections_df = None


class MergedDbs(object):

  def __init__(self):
    self.images_df = None
    self.keywords_df = None
    self.collections_df = None

  
def query_to_data_frame(cursor: Text, query: Text) -> pd.DataFrame:
  cursor.execute(query)
  rows = cursor.fetchall()
  column_names = []
  table_marker_columns = []
  table_prefix = ''
  for d in cursor.description:
    name = d[0]
    if name.startswith(TABLE_MARKER_PREFIX):
      # This is a special marker column.
      table_prefix = name[len(TABLE_MARKER_PREFIX):] + '_'
      column_names.append(name)
      table_marker_columns.append(name)
    else:
      column_names.append(table_prefix + name)
  df = pd.DataFrame.from_records(rows, columns=column_names)
  df = df.drop(labels=table_marker_columns, axis=1)
  return df


def load_db(path: Text):
  logging.info('load_db, path=%s', path)
  lightroom_db = LightroomDb()

  connection = sqlite3.connect(path)
  try:
    cursor = connection.cursor()
    lightroom_db.images_df = query_to_data_frame(cursor, QUERY_IMAGES)
    lightroom_db.images_df[Column.PARSED_CAPTURE_TIME.name] = (
      lightroom_db.images_df[Column.CAPTURE_TIME.value].map(parse_date_time))
    lightroom_db.images_df.set_index(Column.ID_GLOBAL.value, verify_integrity=True)

    lightroom_db.keywords_df = query_to_data_frame(cursor, QUERY_KEYWORDS)
    lightroom_db.collections_df = query_to_data_frame(cursor, QUERY_COLLECTIONS)
  finally:
    connection.close()
  return lightroom_db


def merge_db_images(db1: LightroomDb, db2: LightroomDb) -> pd.DataFrame:
  logging.info('merge_db_images')
  merged_images_df = db1.images_df.merge(
      db2.images_df, how='outer',
      on=Column.ID_GLOBAL.value, suffixes=('_db1', '_db2'))
  return merged_images_df


def merge_db_keywords(db1: LightroomDb, db2: LightroomDb) -> pd.DataFrame:
  logging.info('merge_db_keywords')
  merged_keywords_df = db1.keywords_df.merge(
      db2.keywords_df, how='outer',
      on=[Column.ID_GLOBAL.value, Column.KEYWORD.value],
      suffixes=('_db1', '_db2'),
      indicator='presence')
  return merged_keywords_df


def merge_db_collections(db1: LightroomDb, db2: LightroomDb) -> pd.DataFrame:
  logging.info('merge_db_collections')
  merged_collections_df = db1.collections_df.merge(
      db2.collections_df, how='outer',
      on=[Column.ID_GLOBAL.value, Column.COLLECTION.value],
      suffixes=('_db1', '_db2'),
      indicator='presence')
  return merged_collections_df



def compute_merge_dbs(db1: LightroomDb, db2: LightroomDb) -> MergedDbs:
  logging.info('computed_merge_dbs')
  merged_dbs = MergedDbs()
  merged_dbs.images_df = merge_db_images(db1, db2)
  merged_dbs.keywords_df = merge_db_keywords(db1, db2)
  merged_dbs.collections_df = merge_db_collections(db1, db2)
  return merged_dbs
  

def diff_image_presence(merged_images_df):
  logging.info('diff_image_presence')
  image_removed = pd.isna(merged_images_df[Column.ROOT_FILE.value + DB2_SUFFIX])
  diff_chunk = merged_images_df.loc[image_removed, REPORT_COLUMNS]
  diff_chunk[DIFF_TYPE] = 'PRESENCE'
  diff_chunk[VALUE_DB1] = 'PRESENT'
  diff_chunk[VALUE_DB2] = 'ABSENT'
  return diff_chunk, image_removed


def diff_column(merged_images_df, column: Column, rows_to_ignore):
  logging.info('diff_column: %s', column)
  column_db1 = merged_images_df[column.value + DB1_SUFFIX]
  column_db2 = merged_images_df[column.value + DB2_SUFFIX]
  
  # Gate on FLAG?
  rows_to_ignore = rows_to_ignore | pd.isna(column_db1)
  rows_to_ignore = rows_to_ignore | column_db1.isin(VACUOUS_CAPTIONS)  
  
  value_altered = (column_db1 != column_db2) & ~rows_to_ignore
  
  diff_chunk = merged_images_df.loc[value_altered, REPORT_COLUMNS]
  diff_chunk[DIFF_TYPE] = column.name
  diff_chunk[VALUE_DB1] = column_db1[value_altered]
  diff_chunk[VALUE_DB2] = column_db2[value_altered]

  if pd.api.types.is_numeric_dtype(column_db1):
    diff_chunk[VALUE_DELTA] = diff_chunk[VALUE_DB2] - diff_chunk[VALUE_DB1]

  return diff_chunk, value_altered


def diff_keywords_or_collections(merged_keywords_df: pd.DataFrame, name_column: Column) -> pd.DataFrame:
  logging.info('diff_keywords')
  missing_columns = set(REPORT_COLUMNS).difference(set(merged_keywords_df))
  assert not missing_columns, missing_columns
  removed = (merged_keywords_df.presence == 'left_only')
  diff_chunk = merged_keywords_df.loc[removed, REPORT_COLUMNS]
  diff_chunk[DIFF_TYPE] = f'REMOVED FROM {name_column.name}'
  diff_chunk[VALUE_DB1] = merged_keywords_df.loc[removed, name_column.value]
  diff_chunk[VALUE_DB2] = None
  return diff_chunk


def compute_diff(merged_dbs: MergedDbs, diff_columns: Iterable[Column]) -> pd.DataFrame:
  logging.info('compute_diff')
  diff_chunks = []
  image_removed_diff_chunk, image_removed = diff_image_presence(merged_dbs.images_df)
  diff_chunks.append(image_removed_diff_chunk)
  
  for column in diff_columns:
    diff_chunk, _ = diff_column(merged_dbs.images_df, column, rows_to_ignore=image_removed)
    diff_chunks.append(diff_chunk)
    
  keyword_diff_chunk = diff_keywords_or_collections(merged_dbs.keywords_df, name_column=Column.KEYWORD)
  diff_chunks.append(keyword_diff_chunk)

  collection_diff_chunk = diff_keywords_or_collections(merged_dbs.collections_df, name_column=Column.COLLECTION)
  diff_chunks.append(collection_diff_chunk)

  diff_df = pd.concat(objs=diff_chunks, axis='index', ignore_index=True, sort=False)
  diff_df = diff_df.sort_values(by=SORT_COLUMNS)

  column_ordering = [DIFF_TYPE, VALUE_DB1, VALUE_DB2]
  if VALUE_DELTA in diff_df.columns:
    column_ordering.append(VALUE_DELTA)
  column_ordering += REPORT_COLUMNS
  diff_df = diff_df.loc[:, column_ordering]
  
  return diff_df
 

def diff_catalogs(db1_filename: str, db2_filename: str) -> pd.DataFrame:
  logging.info('diff_catalogs')
  db1 = load_db(maybe_unzip(db1_filename))
  db2 = load_db(maybe_unzip(db2_filename))
  merged_dbs = compute_merge_dbs(db1, db2)
  diff_df = compute_diff(merged_dbs, DIFF_COLUMNS)
  return diff_df


def main(argv):
  if len(argv) > 1:
    logging.fatal('Unparsed arguments: %s', argv)
  diff_df = diff_catalogs(FLAGS.db1, FLAGS.db2)
  logging.info('Printing diff to stdout.')
  print(diff_df.to_csv(sep='\t', index=False))
  

if __name__ == '__main__':
  logging.basicConfig(stream=sys.stderr, level=logging.INFO)
  flags.mark_flag_as_required('db1')
  flags.mark_flag_as_required('db2')
  app.run(main)
