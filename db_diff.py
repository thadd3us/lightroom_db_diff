"""Compares two versions of a Lightroom database.

Example command line:

python3 db_diff.py \
    --db1 "/Users/thadh/Google Drive/Lightroom Backups/Lightroom Backups - contain lost metadata/2014-06-19 1511/Lightroom 5 Catalog.lrcat" \
    --db2 "/Users/thadh/Google Drive/Lightroom Backups/2019-11-24 1444/Lightroom Catalog-2-3.lrcat" \
    --alsologtostderr

TODO:
* Unzip to tmp directory, delete at end.
* GPS deletions / alternations
* Timestamp alterations
* Star alterations
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

QUERY_CAPTIONS = """
SELECT
    *
FROM Adobe_images
LEFT JOIN AgLibraryFile ON Adobe_images.rootFile = AgLibraryFile.id_local
LEFT JOIN AgLibraryFolder ON AgLibraryFile.folder = AgLibraryFolder.id_local
LEFT JOIN AgLibraryIPTC ON AgLibraryIPTC.image = Adobe_images.id_local
;
"""

class LightroomDb(object):
  
  def __init__(self):
    self.images_df = None

  
def query_to_data_frame(cursor: Text, query: Text) -> pd.DataFrame:
  cursor.execute(query)
  rows = cursor.fetchall()
  columns = [d[0] for d in cursor.description]
  df = pd.DataFrame.from_records(rows, columns=columns)
  return df

def load_db(path: Text):
  logging.info('load_db, path=%s', path)
  connection = sqlite3.connect(path)
  cursor = connection.cursor()
  lightroom_db = LightroomDb()
  lightroom_db.images_df = query_to_data_frame(cursor, QUERY_CAPTIONS)
  lightroom_db.images_df.loc[lightroom_db.images_df.caption == '', 'caption'] = None
  return lightroom_db


VACUOUS_CAPTIONS = set([
  '',
  'OLYMPUS DIGITAL CAMERA',
  'Exif JPEG',
])

def diff_captions(db1: LightroomDb, db2: LightroomDb):
  joined_df = db1.images_df.merge(db2.images_df, how='outer', on='image', suffixes=('_db1', '_db2'))

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

  diff_captions(db1, db2)


if __name__ == '__main__':
  flags.mark_flag_as_required('db1')
  flags.mark_flag_as_required('db2')
  app.run(main)
