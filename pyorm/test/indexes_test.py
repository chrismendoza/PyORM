import unittest

from pyorm.indexes import MetaIndexes

class MockGeneric(object):
    def __init__(self, hash_value=None):
        self._hash = hash_value if hash_value is not None else 1

    def __hash__(self):
        return self._hash


class MockOwner(MockGeneric):
    pass


class MockIndex(MockGeneric):
    pass


class MockUnbound(object):
    def __init__(self, cls):
        self.cls = cls
    
    def bind(self, name, owner):
        index = self.cls()
        index.name = name
        index.owner = owner
        return index


class MetaIndexesTestCase(unittest.TestCase):
    def setUp(self):
        class MockMetaIndexes(MockGeneric):
            __metaclass__ = MetaIndexes

        self.MockMetaIndexes = MockMetaIndexes
        self.MockMetaIndexes.owner = MockOwner

    def test_cls_no_indexes(self):
        self.assertEqual(self.MockMetaIndexes._unbound, [])

    def test_instance_no_indexes(self):
        mock_owner = MockOwner()
        indexes = self.MockMetaIndexes(_owner=mock_owner)
        self.assertEqual(indexes._unbound, [])

    def test_cls_w_indexes(self):
        self.MockMetaIndexes.test = MockUnbound(MockIndex)
        self.assertEqual(self.MockMetaIndexes._unbound, ['test'])

    def test_instance_w_indexes(self):
        self.MockMetaIndexes.test = MockUnbound(MockIndex)
        mock_owner = MockOwner()
        indexes = self.MockMetaIndexes(_owner=mock_owner)

        self.assertEqual(indexes._unbound, ['test'])

    def test_cls_trailing_underscore_name(self):
        self.MockMetaIndexes.test_ = MockUnbound(MockIndex)
        self.assertEqual(self.MockMetaIndexes.test_.name, 'test')

    def test_instance_trailing_underscore_name(self):
        self.MockMetaIndexes.test_ = MockUnbound(MockIndex)
        mock_owner = MockOwner()
        indexes = self.MockMetaIndexes(_owner=mock_owner)
        self.assertEqual(indexes.test_.name, 'test')

    def test_owner(self):
        mock_owner = MockOwner()
        indexes = self.MockMetaIndexes(_owner=mock_owner)

        self.assertEqual(id(mock_owner), id(indexes._owner_ref()))
