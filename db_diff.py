"""Compares two versions of a Lightroom database.

Example command line:

python3 db_diff.py \
    --db1 "/Users/thadh/Google Drive/Lightroom Backups/Contain lost metadata/2014-06-19 1511/Lightroom 5 Catalog.lrcat" \
    --db2 "/Users/thadh/personal/Lightroom/Lightroom Catalog-2-3-2.lrcat" \
    --alsologtostderr

TODO:
* GPS deletions / alterations
* Timestamp alterations
* Star alterations
* Unzip to tmp directory, delete at end.
* Publish on github
* Labels, collections, faces.
"""

import pandas as pd
import sqlite3

from absl import app
from absl import flags
from absl import logging

from typing import Text

FLAGS = flags.FLAGS
flags.DEFINE_string('db1', None, 'First database.')
flags.DEFINE_string('db2', None, 'Second database.')

MAIN_CATALOG = '/Users/thadh/personal/Lightroom/Lightroom Catalog-2-3-2.lrcat'

DB1_SUFFIX = '_db1'
DB2_SUFFIX = '_db2'

DIFF_TYPE = 'DIFF_TYPE'
VALUE_DB1 = 'value' + DB1_SUFFIX
VALUE_DB2 = 'value' + DB2_SUFFIX
VALUE_DELTA = 'value_delta'


# Make enum. 
class Columns(object):
  ROOT_FILE = 'Adobe_images_rootFile'
  CAPTION = 'AgLibraryIPTC_caption'
  GPS_LATITUDE = 'AgHarvestedExifMetadata_gpsLatitude'
  GPS_LONGITUDE = 'AgHarvestedExifMetadata_gpsLongitude'
  RATING = 'Adobe_images_rating'
  COLOR_LABELS = 'Adobe_images_colorLabels'
  CAPTURE_TIME = 'Adobe_images_captureTime'
  
DIFF_COLUMNS = [
  Columns.CAPTION,
  Columns.GPS_LATITUDE,
  Columns.GPS_LONGITUDE,
  Columns.RATING,
  Columns.COLOR_LABELS,
  Columns.CAPTURE_TIME,
]

REPORT_COLUMNS = [
  'AgLibraryFile_idx_filename' + DB1_SUFFIX,
  'AgLibraryFolder_pathFromRoot' + DB1_SUFFIX,
  'AgLibraryRootFolder_absolutePath' + DB1_SUFFIX,
]

SORT_COLUMNS = [
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

# Using *s below since I don't know the DB schema well, and want to notice
# if new things appear.
# Using dummy columns to mark which columns come from which tables.
QUERY_CAPTIONS = """
SELECT
    0 AS TABLE_MARKER_Adobe_images,
    Adobe_images.*,
    0 AS TABLE_MARKER_AgLibraryFile,
    AgLibraryFile.*,
    0 AS TABLE_MARKER_AgLibraryFolder,
    AgLibraryFolder.*,
    0 AS TABLE_MARKER_AgLibraryRootFolder,
    AgLibraryRootFolder.*,
    0 AS TABLE_MARKER_AgLibraryIPTC,
    AgLibraryIPTC.*,
    0 AS TABLE_MARKER_AgHarvestedExifMetadata,
    AgHarvestedExifMetadata.*
FROM Adobe_images
LEFT JOIN AgLibraryFile ON AgLibraryFile.id_local = Adobe_images.rootFile
LEFT JOIN AgLibraryFolder ON AgLibraryFolder.id_local = AgLibraryFile.folder
LEFT JOIN AgLibraryRootFolder ON AgLibraryRootFolder.id_local = AgLibraryFolder.rootFolder
LEFT JOIN AgLibraryIPTC ON AgLibraryIPTC.image = Adobe_images.id_local
LEFT JOIN AgHarvestedExifMetadata ON AgHarvestedExifMetadata.image = Adobe_images.id_local
;
"""

# What's in the tables.
['Adobe_images_id_local', 'Adobe_images_id_global',
       'Adobe_images_aspectRatioCache', 'Adobe_images_bitDepth',
       'Adobe_images_captureTime', 'Adobe_images_colorChannels',
       'Adobe_images_colorLabels', 'Adobe_images_colorMode',
       'Adobe_images_copyCreationTime', 'Adobe_images_copyName',
       'Adobe_images_copyReason', 'Adobe_images_developSettingsIDCache',
       'Adobe_images_fileFormat', 'Adobe_images_fileHeight',
       'Adobe_images_fileWidth', 'Adobe_images_hasMissingSidecars',
       'Adobe_images_masterImage', 'Adobe_images_orientation',
       'Adobe_images_originalCaptureTime', 'Adobe_images_originalRootEntity',
       'Adobe_images_panningDistanceH', 'Adobe_images_panningDistanceV',
       'Adobe_images_pick', 'Adobe_images_positionInFolder',
       'Adobe_images_propertiesCache', 'Adobe_images_pyramidIDCache',
       'Adobe_images_rating', 'Adobe_images_rootFile',
       'Adobe_images_sidecarStatus', 'Adobe_images_touchCount',
       'Adobe_images_touchTime', ]
['AgLibraryFile_id_local',
       'AgLibraryFile_id_global', 'AgLibraryFile_baseName',
       'AgLibraryFile_errorMessage', 'AgLibraryFile_errorTime',
       'AgLibraryFile_extension', 'AgLibraryFile_externalModTime',
       'AgLibraryFile_folder', 'AgLibraryFile_idx_filename',
       'AgLibraryFile_importHash', 'AgLibraryFile_lc_idx_filename',
       'AgLibraryFile_lc_idx_filenameExtension', 'AgLibraryFile_md5',
       'AgLibraryFile_modTime', 'AgLibraryFile_originalFilename',
       'AgLibraryFile_sidecarExtensions', ]
['AgLibraryFolder_id_local',
       'AgLibraryFolder_id_global', 'AgLibraryFolder_pathFromRoot',
       'AgLibraryFolder_rootFolder', ]
['AgLibraryRootFolder_id_local',
       'AgLibraryRootFolder_id_global', 'AgLibraryRootFolder_absolutePath',
       'AgLibraryRootFolder_name',
       'AgLibraryRootFolder_relativePathFromCatalog', ]
['AgLibraryIPTC_id_local',
       'AgLibraryIPTC_caption', 'AgLibraryIPTC_copyright',
       'AgLibraryIPTC_image']
['AgHarvestedExifMetadata_id_local',
       'AgHarvestedExifMetadata_image',
       'AgHarvestedExifMetadata_aperture',
       'AgHarvestedExifMetadata_cameraModelRef',
       'AgHarvestedExifMetadata_cameraSNRef',
       'AgHarvestedExifMetadata_dateDay',
       'AgHarvestedExifMetadata_dateMonth',
       'AgHarvestedExifMetadata_dateYear',
       'AgHarvestedExifMetadata_flashFired',
       'AgHarvestedExifMetadata_focalLength',
       'AgHarvestedExifMetadata_gpsLatitude',
       'AgHarvestedExifMetadata_gpsLongitude',
       'AgHarvestedExifMetadata_gpsSequence',
       'AgHarvestedExifMetadata_hasGPS',
       'AgHarvestedExifMetadata_isoSpeedRating',
       'AgHarvestedExifMetadata_lensRef',
       'AgHarvestedExifMetadata_shutterSpeed']


class LightroomDb(object):
  
  def __init__(self):
    self.images_df = None

  
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
  connection = sqlite3.connect(path)
  cursor = connection.cursor()
  lightroom_db = LightroomDb()
  lightroom_db.images_df = query_to_data_frame(cursor, QUERY_CAPTIONS)
  return lightroom_db


def merge_db_images(db1: LightroomDb, db2: LightroomDb):
  logging.info('merge_db_images')
  merged_images_df = db1.images_df.merge(
      db2.images_df, how='outer', on='Adobe_images_id_local', suffixes=('_db1', '_db2'))
  return merged_images_df


def diff_image_presence(merged_images_df):
  logging.info('diff_image_presence')
  image_removed = pd.isna(merged_images_df[Columns.ROOT_FILE + DB2_SUFFIX])
  diff_chunk = merged_images_df.loc[image_removed, REPORT_COLUMNS]
  diff_chunk[DIFF_TYPE] = 'PRESENCE'
  diff_chunk[VALUE_DB1] = 'PRESENT'
  diff_chunk[VALUE_DB2] = 'ABSENT'
  return diff_chunk, image_removed


def diff_column(merged_images_df, column_name, rows_to_ignore):
  column_db1 = merged_images_df[column_name + DB1_SUFFIX]
  column_db2 = merged_images_df[column_name + DB2_SUFFIX]
  
  # Gate on FLAG?
  rows_to_ignore = rows_to_ignore | pd.isna(column_db1)
  rows_to_ignore = rows_to_ignore | column_db1.isin(VACUOUS_CAPTIONS)  
  
  value_altered = (column_db1 != column_db2) & ~rows_to_ignore
  
  diff_chunk = merged_images_df.loc[value_altered, REPORT_COLUMNS]
  diff_chunk[DIFF_TYPE] = column_name
  diff_chunk[VALUE_DB1] = column_db1[value_altered]
  diff_chunk[VALUE_DB2] = column_db2[value_altered]
  
  if column_db1.dtype in ('float64', 'float32', 'int32', 'int64'):
    diff_chunk[VALUE_DELTA] = diff_chunk[VALUE_DB2] - diff_chunk[VALUE_DB1]
    
  return diff_chunk, value_altered

def compute_diff(merged_images_df, diff_column_names):
  logging.info('compute_diff')
  diff_chunks = []
  image_removed_diff_chunk, image_removed = diff_image_presence(merged_images_df)
  diff_chunks.append(image_removed_diff_chunk)
  
  for column_name in diff_column_names:
    diff_chunk, _ = diff_column(merged_images_df, column_name, rows_to_ignore=image_removed)
    diff_chunks.append(diff_chunk)
    
  diff_df = pd.concat(objs=diff_chunks, axis=0, ignore_index=True, sort=False)
  diff_df = diff_df.sort_values(by=SORT_COLUMNS)
  
  column_ordering = [DIFF_TYPE, VALUE_DB1, VALUE_DB2]
  if VALUE_DELTA in diff_df.columns:
    column_ordering.append(VALUE_DELTA)
  column_ordering += REPORT_COLUMNS
  diff_df = diff_df[column_ordering]
  
  return diff_df
 

def main(argv):
  if len(argv) > 1:
    logging.fatal('Unparsed arguments: %s', argv)
  db1 = load_db(FLAGS.db1)
  db2 = load_db(FLAGS.db2)
  merged_images_df = merge_db_images(db1, db2)
  diff_df = compute_diff(merged_images_df, DIFF_COLUMNS)

  logging.info('Printing diff to stdout.')
  print(diff_df.to_csv(sep='\t', index=False))
  

if __name__ == '__main__':
  flags.mark_flag_as_required('db1')
  flags.mark_flag_as_required('db2')
  app.run(main)
