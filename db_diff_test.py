"""
"""
import db_diff
import unittest

catalogs = [
  'testdata/test_catalogs/test_catalog_01_fresh/test_catalog_fresh.lrcat',
]

class DbDiffTest(unittest.TestCase):
  
  def test_01_02(self):
    diff_df = db_diff.diff_catalogs('testdata/test_catalog_01.lrcat', 'testdata/test_catalog_02.lrcat')
    expected_csv = """"""
    self.maxDiff = None
    actual_csv = diff_df.to_csv(index=False)
    self.assertEqual(actual_csv, expected_csv, f'actual=\n{actual_csv}')

if __name__ == '__main__':
    unittest.main()

