"""Tests for db_diff.py.
"""
import sys
import db_diff
import unittest
import logging


TEST_CATALOGS = [
  'testdata/test_catalogs/test_catalog_01/test_catalog_01_fresh.lrcat',
  'testdata/test_catalogs/test_catalog_02/test_catalog_02_gps_captions_collections_keywords.lrcat',
  'testdata/test_catalogs/test_catalog_03/test_catalog_03_two_more_photos_and_edits.lrcat',
  'testdata/test_catalogs/test_catalog_04/test_catalog_04_more_face_tags_gps_edit.lrcat',
]


class DbDiffTest(unittest.TestCase):
  
  def test_01_02(self):
    diff_df = db_diff.diff_catalogs(TEST_CATALOGS[0], TEST_CATALOGS[1])
    expected_csv = """DIFF_TYPE,value_db1,value_db2,AgLibraryFile_idx_filename_db1,AgLibraryFolder_pathFromRoot_db1,AgLibraryRootFolder_absolutePath_db1"""
    self.maxDiff = None
    actual_csv = diff_df.to_csv(index=False).strip()
    self.assertEqual(actual_csv, expected_csv, f'actual=\n{actual_csv}')

  def test_02_01(self):
    diff_df = db_diff.diff_catalogs(TEST_CATALOGS[1], TEST_CATALOGS[0])
    expected_csv = """DIFF_TYPE,value_db1,value_db2,value_delta,AgLibraryFile_idx_filename_db1,AgLibraryFolder_pathFromRoot_db1,AgLibraryRootFolder_absolutePath_db1
GPS_LATITUDE,48.13746461620167,,,1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg,,/Users/thad/Google Drive/src/lightroom/testdata/test_photos/
GPS_LONGITUDE,11.575437771163333,,,1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg,,/Users/thad/Google Drive/src/lightroom/testdata/test_photos/
RATING,3.0,,,1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg,,/Users/thad/Google Drive/src/lightroom/testdata/test_photos/
GPS_LATITUDE,37.82686602640833,,,GoldenGateBridge-001.jpg,,/Users/thad/Google Drive/src/lightroom/testdata/test_photos/
GPS_LONGITUDE,-122.48635834924333,,,GoldenGateBridge-001.jpg,,/Users/thad/Google Drive/src/lightroom/testdata/test_photos/
RATING,3.0,,,GoldenGateBridge-001.jpg,,/Users/thad/Google Drive/src/lightroom/testdata/test_photos/
RATING,4.0,,,Hermann_Hesse_2.jpg,,/Users/thad/Google Drive/src/lightroom/testdata/test_photos/
RATING,5.0,,,"Martin_Luther_King,_Jr..jpg",,/Users/thad/Google Drive/src/lightroom/testdata/test_photos/"""
    self.maxDiff = None
    actual_csv = diff_df.to_csv(index=False).strip()
    self.assertEqual(actual_csv, expected_csv, f'actual=\n{actual_csv}')

  def test_04_03(self):
    diff_df = db_diff.diff_catalogs(TEST_CATALOGS[3], TEST_CATALOGS[2])
    expected_csv = """DIFF_TYPE,value_db1,value_db2,value_delta,AgLibraryFile_idx_filename_db1,AgLibraryFolder_pathFromRoot_db1,AgLibraryRootFolder_absolutePath_db1
GPS_LATITUDE,37.827544289161665,37.827827756526666,0.0002834673650013997,GoldenGateBridge-001.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
GPS_LONGITUDE,-122.48189497883833,-122.48773672802666,-0.005841749188334688,GoldenGateBridge-001.jpg,FastFoto/test_photos/,/Users/thad/Pictures/"""
    self.maxDiff = None
    actual_csv = diff_df.to_csv(index=False).strip()
    self.assertEqual(actual_csv, expected_csv, f'actual=\n{actual_csv}')

  def test_03_02(self):
    diff_df = db_diff.diff_catalogs(TEST_CATALOGS[2], TEST_CATALOGS[1])
    expected_csv = """DIFF_TYPE,value_db1,value_db2,value_delta,AgLibraryFile_idx_filename_db1,AgLibraryFolder_pathFromRoot_db1,AgLibraryRootFolder_absolutePath_db1
CAPTION,View from Petersdom.  August 2006.,,,1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
GPS_LATITUDE,48.13732308062167,48.13746461620167,0.00014153557999918576,1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
GPS_LONGITUDE,11.575565271141667,11.575437771163333,-0.00012749997833338966,1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
RATING,4.0,3.0,-1.0,1200px-Rathaus_and_Marienplatz_from_Peterskirche_-_August_2006.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
CAPTION,View over Africa.,,,1200px-The_Earth_seen_from_Apollo_17.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
PRESENCE,PRESENT,ABSENT,,1920px-Aldrin_Apollo_11_original.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
PRESENCE,PRESENT,ABSENT,,1_Live_Krone_2013_dth_1.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
CAPTION,"The Golden Gate Bridge in San Francisco, CA at sunset.  Taken from Marin.","The Golden Gate Bridge in San Francisco, CA at sunset.",,GoldenGateBridge-001.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
GPS_LATITUDE,37.827827756526666,37.82686602640833,-0.0009617301183340032,GoldenGateBridge-001.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
GPS_LONGITUDE,-122.48773672802666,-122.48635834924333,0.0013783787833290262,GoldenGateBridge-001.jpg,FastFoto/test_photos/,/Users/thad/Pictures/
RATING,5.0,4.0,-1.0,Hermann_Hesse_2.jpg,FastFoto/test_photos/,/Users/thad/Pictures/"""
    self.maxDiff = None
    actual_csv = diff_df.to_csv(index=False).strip()
    self.assertEqual(actual_csv, expected_csv, f'actual=\n{actual_csv}')


if __name__ == '__main__':
  logging.basicConfig(stream=sys.stderr, level=logging.INFO)
  unittest.main()
