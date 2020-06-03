"""Tests for db_diff.py.
"""
import logging
import os
import sys
import unittest

import db_diff

UPDATE_GOLDEN_FILES = False


TEST_CATALOG_FILE_NAMES = [
  'testdata/test_catalogs/test_catalog_01/test_catalog_01_fresh.lrcat',
  'testdata/test_catalogs/test_catalog_02/test_catalog_02_gps_captions_collections_keywords.lrcat',
  'testdata/test_catalogs/test_catalog_03/test_catalog_03_two_more_photos_and_edits.lrcat',
  'testdata/test_catalogs/test_catalog_04/test_catalog_04_more_face_tags_gps_edit.lrcat',
]


TEST_LIGHTROOM_DBS = [db_diff.load_db(db_diff.maybe_unzip(f)) for f in TEST_CATALOG_FILE_NAMES]


class DbDiffTest(unittest.TestCase):

  def check_match(self, golden_file, value):
    golden_path = os.path.join('testdata', 'goldens', golden_file)
    if UPDATE_GOLDEN_FILES:
      with open(golden_path, 'w') as f:
        f.write(value)
    else:
      with open(golden_path, 'r') as f:
        golden = f.read()
      self.maxDiff = None
      self.assertEqual(golden, value)

  def test_sequence(self):
    html = db_diff.diff_catalog_sequence(TEST_CATALOG_FILE_NAMES)
    self.check_match('test_sequence.html', html)

  def test_01_02(self):
    diff_df = db_diff.diff_catalogs(TEST_LIGHTROOM_DBS[0], TEST_LIGHTROOM_DBS[1])
    actual_csv = diff_df.to_csv(index=False)
    self.check_match('test_01_02.csv', actual_csv)

  def test_02_01(self):
    diff_df = db_diff.diff_catalogs(TEST_LIGHTROOM_DBS[1], TEST_LIGHTROOM_DBS[0])
    actual_csv = diff_df.to_csv(index=False)
    self.check_match('test_02_01.csv', actual_csv)

  def test_03_02(self):
    diff_df = db_diff.diff_catalogs(TEST_LIGHTROOM_DBS[2], TEST_LIGHTROOM_DBS[1])
    actual_csv = diff_df.to_csv(index=False)
    self.check_match('test_03_02.csv', actual_csv)

  def test_03_04(self):
    diff_df = db_diff.diff_catalogs(TEST_LIGHTROOM_DBS[2], TEST_LIGHTROOM_DBS[3])
    actual_csv = diff_df.to_csv(index=False)
    self.check_match('test_03_04.csv', actual_csv)

  def test_04_03(self):
    diff_df = db_diff.diff_catalogs(TEST_LIGHTROOM_DBS[3], TEST_LIGHTROOM_DBS[2])
    actual_csv = diff_df.to_csv(index=False)
    self.check_match('test_04_03.csv', actual_csv)


if __name__ == '__main__':
  logging.basicConfig(stream=sys.stderr, level=logging.INFO)
  unittest.main()
