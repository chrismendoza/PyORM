import unittest

from pyorm.column import Column


class ColumnTestCase(unittest.TestCase):
    def test_path(self):
        """
            Test to verify that a new column creates a new
            path chain based on the attributes accessed.
        """
        col = Column.test.column.chain
        self.assertEqual(col._path, ['test','column','chain'])
