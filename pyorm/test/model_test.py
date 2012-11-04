import inspect
import unittest

from pyorm.model import MetaModel, Model


class MockModel(Model):
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


class ModelTestCase(unittest.TestCase):
    def test_copy(self):
        pass

    def test_deepcopy(self):
        pass

    def test_fields(self):
        pass

    def test_compound_fields(self):
        pass

    def test_filters(self):
        pass
