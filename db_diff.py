"""Compares two versions of a Lightroom database.

Example command line:

python3 db_diff.py \
    --db1 "/Users/thadh/Google Drive/Lightroom Backups/Lightroom Backups - contain lost metadata/2014-06-19 1511/Lightroom 5 Catalog.lrcat" \
    --db2 "/Users/thadh/Google Drive/Lightroom Backups/2019-11-24 1444/Lightroom Catalog-2-3.lrcat" \
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

# Using *s below since I don't know the DB schema well, and want to notice
# if new things appear.
# Using dummy columns to mark which columns come from which tables.
TABLE_MARKER_PREFIX = 'TABLE_MARKER_'
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
       'AgHarvestedExifMetadata_image', 'AgHarvestedExifMetadata_aperture',
       'AgHarvestedExifMetadata_cameraModelRef',
       'AgHarvestedExifMetadata_cameraSNRef',
       'AgHarvestedExifMetadata_dateDay', 'AgHarvestedExifMetadata_dateMonth',
       'AgHarvestedExifMetadata_dateYear',
       'AgHarvestedExifMetadata_flashFired',
       'AgHarvestedExifMetadata_focalLength',
       'AgHarvestedExifMetadata_gpsLatitude',
       'AgHarvestedExifMetadata_gpsLongitude',
       'AgHarvestedExifMetadata_gpsSequence', 'AgHarvestedExifMetadata_hasGPS',
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
      # This is a special marker column
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
  #lightroom_db.images_df.loc[lightroom_db.images_df.caption == '', 'caption'] = None
  return lightroom_db


VACUOUS_CAPTIONS = set([
  '',
  'OLYMPUS DIGITAL CAMERA',
  'Exif JPEG',
])


def merge_db_images(db1: LightroomDb, db2: LightroomDb):
  merged_images_df = db1.images_df.merge(
      db2.images_df, how='outer', on='Adobe_images_id_local', suffixes=('_db1', '_db2'))
  return merged_images_df

def diff_captions(merged_images_df):
  IMAGE_COLS = ['pathFromRoot_db1', 'originalFilename_db1']

  image_removed = pd.isna(joined_df.pathFromRoot_db2)
  print('SUMMARY: image_removed, n=%d' % sum(image_removed))
  if sum(image_removed) > 0:
    print(joined_df[image_removed].pathFromRoot_db1.value_counts(dropna=False))
  print()

  caption_1 = joined_df.caption_db1.fillna('')
  caption_2 = joined_df.caption_db2.fillna('')
  caption_removed = (caption_1 != '') & (caption_2 == '') & (~image_removed )
  caption_removed &= ~caption_1.isin(VACUOUS_CAPTIONS)
  print('SUMMARY: caption_removed, n=%d' % sum(caption_removed))
  if sum(caption_removed) > 0:
    print(joined_df[caption_removed].pathFromRoot_db1.value_counts(dropna=False))
  print()
  
  caption_altered = (caption_1 != caption_2) & ~caption_removed & ~image_removed
  caption_altered &= ~caption_1.isin(VACUOUS_CAPTIONS)
  print('SUMMARY: caption_altered n=%d' % sum(caption_altered))
  if sum(caption_altered) > 0:
    print(joined_df[caption_altered].pathFromRoot_db1.value_counts(dropna=False))
  print()
   
  return (image_removed, caption_removed, caption_altered)


def main(argv):
  if len(argv) > 1:
    logging.fatal('Unparsed arguments: %s', argv)
  db1 = load_db(FLAGS.db1)
  db2 = load_db(FLAGS.db2)
  merged_images_df = merge_db_images(db1, db2)
  diff_captions(merged_images_df)


if __name__ == '__main__':
  flags.mark_flag_as_required('db1')
  flags.mark_flag_as_required('db2')
  app.run(main)
