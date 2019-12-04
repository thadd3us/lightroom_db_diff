"""Compares two versions of a Lightroom database.

Example command line:

python3 db_diff.py \
    --db1 "/Users/thadh/Google Drive/Lightroom Backups/2019-11-11 0637/Lightroom Catalog-2-3.lrcat" \
    --db2 "/Users/thadh/Google Drive/Lightroom Backups/2019-11-24 1444/Lightroom Catalog-2-3.lrcat" \
    --alsologtostderr
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
    self.captions_df = None

  
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
  lightroom_db.captions_df = query_to_data_frame(cursor, QUERY_CAPTIONS)
  lightroom_db.captions_df.loc[lightroom_db.captions_df.caption == '', 'caption'] = None
  return lightroom_db


def diff_captions(db1: LightroomDb, db2: LightroomDb):
  joined_df = db1.captions_df.merge(db2.captions_df, how='outer', on='image', suffixes=('_db1', '_db2'))
  caption_1 = joined_df.caption_db1.fillna('')
  caption_2 = joined_df.caption_db2.fillna('')
  caption_altered = (caption_1 != caption_2)
  if sum(caption_altered) > 0:
    print('caption_altered count=%d' % len(caption_altered.index))
    IMAGE_COLS = ['pathFromRoot_db1', 'originalFilename_db1']
    print(joined_df[caption_altered][IMAGE_COLS + ['caption_db1', 'caption_db2']])
      

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
