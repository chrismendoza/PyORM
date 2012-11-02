import unittest

from pyorm.model import Meta, MetaIndexes


class MockGeneric(object):
    def __init__(self, hash_value=None):
        self._hash = hash_value if hash_value is not None else 1

    def __hash__(self):
        return self._hash


class MockOwner(MockGeneric):
    pass


class MetaTestCase(unittest.TestCase):
    def setUp(self):
        class MockMeta(MockGeneric):
            __metaclass__ = Meta

        self.MockMeta = MockMeta
        self.MockMeta.owner = MockOwner

    def test_class_owner(self):
        self.assertEqual(id(self.MockMeta.owner), id(MockOwner))

    def test_instance_owner(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)

        self.assertEqual(id(mock_owner), id(meta.owner_ref()))

    def test_instance_db_table_undefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)

        self.assertEqual(meta.db_table, 'mockowner')

    def test_class_db_table_undefined(self):
        self.assertEqual(self.MockMeta.db_table, 'mockowner')

    def test_class_db_table_defined(self):
        self.MockMeta.db_table = 'cheeseshop'
        self.assertEqual(self.MockMeta.db_table, 'cheeseshop')

    def test_instance_db_table_defined(self):
        self.MockMeta.db_table = 'cheeseshop'
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)

        self.assertEqual(meta.db_table, 'cheeseshop')

    def test_class_db_table_redefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)
        self.MockMeta.db_table = 'cheeseshop'

        self.assertEqual(self.MockMeta.db_table, 'cheeseshop')
        self.assertEqual(meta.db_table, 'mockowner')

    def test_instance_db_table_redefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)
        meta.db_table = 'cheeseshop'

        self.assertEqual(self.MockMeta.db_table, 'mockowner')
        self.assertEqual(meta.db_table, 'cheeseshop')

    def test_instance_verbose_name_undefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)

        self.assertEqual(meta.verbose_name, 'MockOwner')

    def test_class_verbose_name_undefined(self):
        self.assertEqual(self.MockMeta.verbose_name, 'MockOwner')

    def test_class_verbose_name_defined(self):
        self.MockMeta.verbose_name = 'cheeseshop'
        self.assertEqual(self.MockMeta.verbose_name, 'cheeseshop')

    def test_instance_verbose_name_defined(self):
        self.MockMeta.verbose_name = 'cheeseshop'
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)

        self.assertEqual(meta.verbose_name, 'cheeseshop')

    def test_class_verbose_name_redefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)
        self.MockMeta.verbose_name = 'cheeseshop'

        self.assertEqual(self.MockMeta.verbose_name, 'cheeseshop')
        self.assertEqual(meta.verbose_name, 'MockOwner')

    def test_instance_verbose_name_redefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)
        meta.verbose_name = 'cheeseshop'

        self.assertEqual(self.MockMeta.verbose_name, 'MockOwner')
        self.assertEqual(meta.verbose_name, 'cheeseshop')

    def test_instance_auto_pk_undefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)

        self.assertEqual(meta.auto_primary_key, True)

    def test_class_auto_pk_undefined(self):
        self.assertEqual(self.MockMeta.auto_primary_key, True)

    def test_class_auto_pk_defined(self):
        self.MockMeta.auto_primary_key = False
        self.assertEqual(self.MockMeta.auto_primary_key, False)

    def test_instance_auto_pk_defined(self):
        self.MockMeta.auto_primary_key = False
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)

        self.assertEqual(meta.auto_primary_key, False)

    def test_class_auto_pk_redefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)
        self.MockMeta.auto_primary_key = False

        self.assertEqual(self.MockMeta.auto_primary_key, False)
        self.assertEqual(meta.auto_primary_key, True)

    def test_instance_auto_pk_redefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)
        meta.auto_primary_key = False

        self.assertEqual(self.MockMeta.auto_primary_key, True)
        self.assertEqual(meta.auto_primary_key, False)

    def test_instance_auto_filters_undefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)

        self.assertEqual(meta.auto_filters, [])

    def test_class_auto_filters_undefined(self):
        self.assertEqual(self.MockMeta.auto_filters, [])

    def test_class_auto_filters_defined(self):
        self.MockMeta.auto_filters = [1, 2, 3]
        self.assertEqual(self.MockMeta.auto_filters, [1, 2, 3])

    def test_instance_auto_filters_defined(self):
        self.MockMeta.auto_filters = [1, 2, 3]
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)

        self.assertEqual(meta.auto_filters, [1, 2, 3])

    def test_class_auto_filters_redefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)
        self.MockMeta.auto_filters = [1, 2, 3]

        self.assertEqual(self.MockMeta.auto_filters, [1, 2, 3])
        self.assertEqual(meta.auto_filters, [])

    def test_instance_auto_filters_redefined(self):
        mock_owner = MockOwner()
        meta = self.MockMeta(_owner=mock_owner)
        meta.auto_filters = [1, 2, 3]

        self.assertEqual(self.MockMeta.auto_filters, [])
        self.assertEqual(meta.auto_filters, [1, 2, 3])


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
