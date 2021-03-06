"""Compares multiple versions of a Lightroom Catalog database.

Example command line:

python db_diff.py testdata/test_catalogs/test_catalog_*/*.lrcat > z.html
"""

import dataclasses
import enum
import glob
import html
import logging
import os
import sqlite3
import urllib
import zipfile
from typing import Iterable, List, Optional, Set, Text, Tuple

import dataclasses_json
import geopy.distance
import maya
import numpy as np
import pandas as pd
from absl import app
from absl import flags

DEFAULT_CONFIG_JSON = """
{
  "diff_columns": [
    "AgLibraryIPTC_caption", 
    "GPS_LOCATION", 
    "Adobe_images_rating", 
    "Adobe_images_colorLabels", 
    "PARSED_CAPTURE_TIME", 
    "AgLibraryFile_importHash"
  ],
  "report_columns": [
    "AgLibraryFile_idx_filename_db1",
    "AgLibraryFolder_pathFromRoot_db1",
    "AgLibraryRootFolder_absolutePath_db1",
    "IMAGE_LINK_db1"
  ],
  "sort_columns": [
    "DIFF_TYPE", 
    "AgLibraryRootFolder_absolutePath_db1", 
    "AgLibraryFolder_pathFromRoot_db1", 
    "AgLibraryFile_idx_filename_db1"
  ], 
  "vacuous_captions": [
    "", 
    "OLYMPUS DIGITAL CAMERA", 
    "Exif JPEG",
    "My beautiful picture"
  ],
  "ignore_collections": [
    "quick collection"
  ]
}
"""

flags.DEFINE_string('config_json', DEFAULT_CONFIG_JSON, 'db_diff config.')
FLAGS = flags.FLAGS

DB1_SUFFIX = '_db1'
DB2_SUFFIX = '_db2'

DIFF_TYPE = 'DIFF_TYPE'
VALUE_DB1 = 'value' + DB1_SUFFIX
VALUE_DB2 = 'value' + DB2_SUFFIX
VALUE_DELTA = 'value_delta'


@enum.unique
class Column(enum.Enum):
  ID_GLOBAL = 'Adobe_images_id_global'
  ROOT_FILE = 'Adobe_images_rootFile'  # Pointer to the file index.

  FILENAME = 'AgLibraryFile_idx_filename'
  PATH_FROM_ROOT = 'AgLibraryFolder_pathFromRoot'
  ROOT_PATH = 'AgLibraryRootFolder_absolutePath'
  IMAGE_LINK = 'IMAGE_LINK'

  GPS_LATITUDE = 'AgHarvestedExifMetadata_gpsLatitude'
  GPS_LONGITUDE = 'AgHarvestedExifMetadata_gpsLongitude'
  RATING = 'Adobe_images_rating'
  COLOR_LABELS = 'Adobe_images_colorLabels'
  CAPTURE_TIME = 'Adobe_images_captureTime'
  HASH = 'AgLibraryFile_importHash'
  CAPTION = 'AgLibraryIPTC_caption'

  GPS_LOCATION = 'GPS_LOCATION'
  PARSED_CAPTURE_TIME = 'PARSED_CAPTURE_TIME'

  # Not present for images; just in specific DataFrames.
  KEYWORD = 'AgLibraryKeyword_name'
  COLLECTION = 'AgLibraryCollection_name'


@dataclasses.dataclass
class Config(dataclasses_json.DataClassJsonMixin):
  diff_columns: List[Column] = dataclasses.field(default_factory=list)
  report_columns: List[str] = dataclasses.field(default_factory=list)
  sort_columns: List[str] = dataclasses.field(default_factory=list)
  vacuous_captions: Set[str] = dataclasses.field(default_factory=set)
  ignore_collections: Set[str] = dataclasses.field(default_factory=set)


TABLE_MARKER_PREFIX = 'TABLE_MARKER_'

QUERY_SNIPPET_SELECT_IMAGE_LOCATION = f"""
    0 AS {TABLE_MARKER_PREFIX}Adobe_images,
    Adobe_images.*,
    0 AS {TABLE_MARKER_PREFIX}AgLibraryFile,
    AgLibraryFile.*,
    0 AS {TABLE_MARKER_PREFIX}AgLibraryFolder,
    AgLibraryFolder.*,
    0 AS {TABLE_MARKER_PREFIX}AgLibraryRootFolder,
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
    0 AS {TABLE_MARKER_PREFIX}AgLibraryIPTC,
    AgLibraryIPTC.*,
    0 AS {TABLE_MARKER_PREFIX}AgHarvestedExifMetadata,
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
    0 AS {TABLE_MARKER_PREFIX}AgLibraryKeywordImage,
    AgLibraryKeywordImage.*,
    0 AS {TABLE_MARKER_PREFIX}AgLibraryKeyword,
    AgLibraryKeyword.*,
    0 AS {TABLE_MARKER_PREFIX}Adobe_images,
    Adobe_images.id_global    
FROM AgLibraryKeywordImage 
LEFT JOIN Adobe_images ON Adobe_images.id_local = AgLibraryKeywordImage.image
LEFT JOIN AgLibraryKeyword ON AgLibraryKeyword.id_local = AgLibraryKeywordImage.tag
;
"""

QUERY_COLLECTIONS = f"""
SELECT
    0 AS {TABLE_MARKER_PREFIX}AgLibraryCollectionImage,
    AgLibraryCollectionImage.*,
    0 AS {TABLE_MARKER_PREFIX}AgLibraryCollection,
    AgLibraryCollection.*,
    0 AS {TABLE_MARKER_PREFIX}Adobe_images,
    Adobe_images.id_global    
FROM AgLibraryCollectionImage 
LEFT JOIN Adobe_images ON Adobe_images.id_local = AgLibraryCollectionImage.image
LEFT JOIN AgLibraryCollection ON AgLibraryCollection.id_local = AgLibraryCollectionImage.collection
;
"""


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


def query_to_data_frame(cursor: sqlite3.Cursor, query: Text) -> pd.DataFrame:
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


def parse_date_time(date_time_str: Optional[str]) -> Optional[maya.MayaDT]:
  if date_time_str is None:
    return None
  try:
    return maya.parse(date_time_str)
  except ValueError as e:
    logging.error('Unable to parse time: %s\n%s', date_time_str, e)
  return None


def load_db(config: Config, path: str) -> LightroomDb:
  logging.info('load_db, path=%s', path)
  lightroom_db = LightroomDb()

  connection = sqlite3.connect(path)
  try:
    cursor = connection.cursor()
    lightroom_db.images_df = query_to_data_frame(cursor, QUERY_IMAGES)
    lightroom_db.images_df[Column.PARSED_CAPTURE_TIME.value] = (
      lightroom_db.images_df[Column.CAPTURE_TIME.value].map(parse_date_time))

    def lat_lon_join(x):
      assert len(x) == 2
      if pd.isna(x[0]) and pd.isna(x[1]):
        return None
      return x[0], x[1]

    lightroom_db.images_df[Column.GPS_LOCATION.value] = (
      lightroom_db.images_df[[Column.GPS_LATITUDE.value, Column.GPS_LONGITUDE.value]].apply(
        apply_if_none_null, args=(tuple, None), axis='columns', raw=True))

    def image_link(x):
      filename = os.path.join(*x.tolist())
      escaped = urllib.parse.quote(filename, safe="/")
      return f'file://{escaped}'

    lightroom_db.images_df[Column.IMAGE_LINK.value] = (
      lightroom_db.images_df[[Column.ROOT_PATH.value, Column.PATH_FROM_ROOT.value, Column.FILENAME.value]].apply(
        image_link, axis='columns', raw=True))

    # Not using the index, just checking integrity.
    lightroom_db.images_df.set_index(Column.ID_GLOBAL.value, verify_integrity=True)

    keywords_df = query_to_data_frame(cursor, QUERY_KEYWORDS)
    keywords_df = keywords_df.merge(lightroom_db.images_df, how='left', left_on=Column.ID_GLOBAL.value,
                                    right_on=Column.ID_GLOBAL.value, suffixes=('', ''))
    lightroom_db.keywords_df = keywords_df

    collections_df = query_to_data_frame(cursor, QUERY_COLLECTIONS)
    collections_df = collections_df[
      ~collections_df[Column.COLLECTION.value].isin(config.ignore_collections)]
    collections_df = collections_df.merge(lightroom_db.images_df, how='left', left_on=Column.ID_GLOBAL.value,
                                          right_on=Column.ID_GLOBAL.value, suffixes=('', ''))
    lightroom_db.collections_df = collections_df

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


def diff_image_presence(config: Config, merged_images_df) -> Tuple[pd.DataFrame, pd.Series]:
  logging.info('diff_image_presence')
  image_removed = pd.isna(merged_images_df[Column.ROOT_FILE.value + DB2_SUFFIX])
  diff_chunk = merged_images_df.loc[image_removed, config.report_columns]
  diff_chunk[DIFF_TYPE] = 'PRESENCE'
  diff_chunk[VALUE_DB1] = 'PRESENT'
  diff_chunk[VALUE_DB2] = 'ABSENT'
  return diff_chunk, image_removed


def apply_if_none_null(values: np.ndarray, fn, null_result=None):
  if pd.isna(values).any():
    return null_result
  return fn(values)


def diff_column(config: Config, merged_images_df, column: Column, rows_to_ignore) -> pd.DataFrame:
  logging.info('diff_column: %s', column)
  column_db1 = merged_images_df[column.value + DB1_SUFFIX]
  column_db2 = merged_images_df[column.value + DB2_SUFFIX]

  # Gate on FLAG?
  rows_to_ignore = rows_to_ignore | pd.isna(column_db1)
  rows_to_ignore = rows_to_ignore | column_db1.isin(config.vacuous_captions)

  value_altered = (column_db1 != column_db2) & ~rows_to_ignore

  diff_chunk = merged_images_df.loc[value_altered, config.report_columns]
  diff_chunk[DIFF_TYPE] = column.name
  diff_chunk[VALUE_DB1] = column_db1[value_altered]
  diff_chunk[VALUE_DB2] = column_db2[value_altered]

  if column == Column.GPS_LOCATION:
    def gps_location_diff(s: np.ndarray):
      assert len(s) == 2
      c1 = s[0]
      c2 = s[1]
      if pd.isna(c1) or pd.isna(c2):
        return float('inf')
      for c in c1 + c2:
        if pd.isna(c):
          return float('inf')
      d = geopy.distance.geodesic(c1, c2).meters
      return f'{d} meters'

    d = diff_chunk[[VALUE_DB1, VALUE_DB2]].apply(apply_if_none_null, args=(gps_location_diff, np.inf),
                                                 axis='columns', raw=True, result_type='reduce')
    diff_chunk[VALUE_DELTA] = d
  elif column == Column.PARSED_CAPTURE_TIME:
    def time_delta(values: np.ndarray):
      assert len(values) == 2
      return f'{(values[1] - values[0]).total_seconds()} seconds'

    d = diff_chunk[[VALUE_DB1, VALUE_DB2]].apply(apply_if_none_null, args=(time_delta, np.inf),
                                                 axis='columns', raw=True, result_type='reduce')
    diff_chunk[VALUE_DELTA] = d
  elif pd.api.types.is_numeric_dtype(column_db1):
    diff_chunk[VALUE_DELTA] = diff_chunk[VALUE_DB2] - diff_chunk[VALUE_DB1]
  return diff_chunk


def diff_keywords_or_collections(config: Config, merged_keywords_df: pd.DataFrame, name_column: Column) -> pd.DataFrame:
  logging.info('diff_keywords')
  missing_columns = set(config.report_columns).difference(set(merged_keywords_df))
  assert not missing_columns, missing_columns
  removed = (merged_keywords_df.presence == 'left_only')
  diff_chunk = merged_keywords_df.loc[removed, config.report_columns]
  diff_chunk[DIFF_TYPE] = f'REMOVED FROM {name_column.name}'
  diff_chunk[VALUE_DB1] = merged_keywords_df.loc[removed, name_column.value]
  diff_chunk[VALUE_DB2] = None
  return diff_chunk


def compute_diff(config: Config, merged_dbs: MergedDbs, diff_columns: Iterable[Column]) -> pd.DataFrame:
  logging.info('compute_diff')
  diff_chunks = []
  image_removed_diff_chunk, image_removed = diff_image_presence(config, merged_dbs.images_df)
  diff_chunks.append(image_removed_diff_chunk)

  for column in diff_columns:
    diff_chunk = diff_column(config, merged_dbs.images_df, column, rows_to_ignore=image_removed)
    diff_chunks.append(diff_chunk)

  keyword_diff_chunk = diff_keywords_or_collections(config, merged_dbs.keywords_df, name_column=Column.KEYWORD)
  diff_chunks.append(keyword_diff_chunk)

  collection_diff_chunk = diff_keywords_or_collections(config, merged_dbs.collections_df, name_column=Column.COLLECTION)
  diff_chunks.append(collection_diff_chunk)

  diff_df = pd.concat(objs=diff_chunks, axis='index', ignore_index=True, sort=False)
  diff_df = diff_df.sort_values(by=config.sort_columns)

  column_ordering = [DIFF_TYPE, VALUE_DB1, VALUE_DB2]
  if VALUE_DELTA in diff_df.columns:
    column_ordering.append(VALUE_DELTA)
  column_ordering += config.report_columns
  diff_df = diff_df.loc[:, column_ordering]

  return diff_df


def diff_catalogs(config: Config, db1: LightroomDb, db2: LightroomDb) -> pd.DataFrame:
  logging.info('diff_catalogs')
  merged_dbs = compute_merge_dbs(db1, db2)
  diff_df = compute_diff(config, merged_dbs, config.diff_columns)
  return diff_df


def diff_catalog_sequence(config: Config, db_file_names: List[str]) -> str:
  assert len(db_file_names) >= 2, db_file_names
  db2 = load_db(config, maybe_unzip(db_file_names[0]))
  lines = []
  for i in range(1, len(db_file_names)):
    db1 = db2  # Push the right one to the left.
    db2 = load_db(config, maybe_unzip(db_file_names[i]))
    diff_df = diff_catalogs(config, db1, db2)
    lines.append(f'<h1>Compare {i - 1} vs {i}</h1>')
    lines.append('<ul>')
    lines.append(f'<li> db1: {db_file_names[i - 1]}')
    lines.append(f'<li> db2: {db_file_names[i]}')
    lines.append('</ul>')

    def basic_formatter(value):
      if pd.isna(value):
        return ''
      return html.escape(str(value))

    formatters = {}
    for column_name in diff_df.columns:
      if Column.IMAGE_LINK.value in column_name:
        formatters[column_name] = lambda x: x
      else:
        formatters[column_name] = basic_formatter

    lines.append(diff_df.to_html(
      formatters=formatters, col_space=100, index=False, escape=False, justify='left', na_rep='',
      render_links=True))
    lines.append('<p>')
    lines.append('If the above looks OK, you can remove the left catalog (db1) using:')
    lines.append('<pre>')
    lines.append(f'rm "{db_file_names[i - 1]}"')
    lines.append('</pre>')
  return '\n'.join(lines)


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


def main(argv) -> None:
  config = Config.from_json(FLAGS.config_json)
  db_file_names = argv[1:]
  print(diff_catalog_sequence(config, db_file_names))


if __name__ == '__main__':
  # logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
  app.run(main)
