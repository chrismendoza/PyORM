import unittest, weakref, copy

from pyorm.column import Column


class MockOwner(object):
    def __hash__(self):
        return 1


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
        self.assertEqual(id(col._owner_ref()), id(mock_owner))

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

    def test_hash(self):
        """
            Checks to see if the has of two objects with the same options
            hash to the same value, and that two column objects that do
            not share all of the same objects hash to different values
        """
        mock_owner = MockOwner()
        col = Column(scope='parent').test.field
        col.set_alias('fish')
        col.owner = mock_owner

        mock_owner2 = MockOwner()
        col2 = Column(scope='parent').test.field
        col2.set_alias('fish')
        col2.owner = mock_owner2

        self.assertEqual(hash(col), hash(col2))

        mock_owner3 = MockOwner()
        col3 = Column(scope='parent').test.field
        col3.set_alias('cheese')
        col3.owner = mock_owner

        self.assertNotEqual(hash(col), hash(col3))
