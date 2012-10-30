import unittest, weakref, copy

from pyorm.column import Column


class MockOwner(object):
    pass


class ColumnTestCase(unittest.TestCase):
    def test_path(self):
        """
            Test to verify that a new column creates a new
            path chain based on the attributes accessed.
        """
        col = Column.test.column.chain
        self.assertEqual(col._path, ['test','column','chain'])

    def test_alias(self):
        """
            Tests that an alias can be applied, and re-applied
        """
        col = Column.test.field

        col.set_alias('fish')
        self.assertEqual(col._alias, 'fish')
        self.assertEqual(col.get_alias(), 'fish')

        col.set_alias('cheese')
        self.assertEqual(col._alias, 'cheese')
        self.assertEqual(col.get_alias(), 'cheese')

    def test_scope(self):
        """
            Test setting scope both on Column initialization and
            after column initialization.
        """
        col = Column(scope='parent').test.field
        self.assertEqual(col._scope, 'parent')
        self.assertEqual(col.get_scope(), 'parent')

        col.set_scope('normal')
        self.assertEqual(col._scope, 'normal')
        self.assertEqual(col.get_scope(), 'normal')

    def test_owner(self):
        """
            Verify that the owner is saved as a weak reference proxy
            to the original object.
        """
        col = Column.test.field
        mock_owner = MockOwner()
        col.owner = mock_owner

        self.assertEqual(col._owner, weakref.proxy(mock_owner))
        self.assertEqual(col.owner, weakref.proxy(mock_owner))

    def test_copy(self):
        """
            Tests the creation of a copy
        """
        mock_owner = MockOwner()
        col = Column(scope='parent').test.field
        col.set_alias('cheese')
        col.owner = mock_owner

        col_copy = copy.copy(col)

        self.assertNotEqual(id(col), id(col_copy))
        self.assertEqual(id(col._owner), id(col_copy._owner))
        

    def test_deepcopy(self):
        """
            Tests the creation of a deep copy (which is the same as
            a copy for column objects, due to the use of weakref.proxy()
            for the owner).
        """
        mock_owner = MockOwner()
        col = Column(scope='parent').test.field
        col.set_alias('cheese')
        col.owner = mock_owner

        col_copy = copy.copy(col)

        self.assertNotEqual(id(col), id(col_copy))
        self.assertEqual(id(col._owner), id(col_copy._owner))        
