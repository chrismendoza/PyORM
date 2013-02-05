import inspect
import unittest

from pyorm.model import MetaModel, Model, RecordProxy, clones, results_loaded


class MockModel(Model):
    pass


class PropertiesTestCase(unittest.TestCase):
    def test_clones(self):
        pass

    def test_results_loaded(self):
        pass

    def test_mapping_tuple(self):
        pass

    def test_container(self):
        pass


class RecordProxyTestCase(unittest.TestCase):
    def test_init(self):
        pass

    def test_getattr_same_idx(self):
        pass

    def test_getattr_different_idx(self):
        pass


class MetaModelTestCase(unittest.TestCase):
    def test_metamodel_cls_indexes(self):
        self.assertTrue(hasattr(MockModel, 'Indexes'))

    def test_metamodel_cls_meta(self):
        self.assertTrue(hasattr(MockModel, 'Meta'))

    def test_metamodel_instance_indexes(self):
        model = MockModel()
        self.assertTrue(hasattr(model, 'Indexes'))
        self.assertFalse(inspect.isclass(model.Indexes))

    def test_metamodel_instance_meta(self):
        model = MockModel()
        self.assertTrue(hasattr(model, 'Meta'))
        self.assertFalse(inspect.isclass(model.Meta))

    def test_relationships_cls(self):
        pass

    def test_relationships_instance(self):
        pass

    def test_fields_cls(self):
        pass
    
    def test_fields_instance(self):
        pass

    def test_add_field(self):
        pass


class ModelTestCase(unittest.TestCase):
    def test_copy(self):
        pass

    def test_deepcopy(self):
        pass

    def test_owner(self):
        pass

    def test_current_idx(self):
        pass

    def test_result_loaded(self):
        pass

    def test_add_field(self):
        pass

    def test_add_relationship(self):
        pass

    def test_fields(self):
        pass

    def test_compound_fields(self):
        pass

    def test_filters(self):
        pass

    def test_having(self):
        pass

    def test_order(self):
        pass

    def test_group(self):
        pass

    def test_map(self):
        pass

    def test_reset_map(self):
        pass

    def test_clone(self):
        pass

    def test_scalar(self):
        pass

    def test_one(self):
        pass

    def test_get(self):
        pass

    def test_all(self):
        pass

    def test_iter(self):
        pass

    def test_iter_with_map(self):
        pass

    def test_insert(self):
        pass

    def test_replace(self):
        pass

    def test_update(self):
        pass

    def test_delete(self):
        pass

    def test_truncate(self):
        pass

    def test_create(self):
        pass
