import inspect
import unittest

from pyorm.model import MetaModel


class MockModel(object):
    __metaclass__ = MetaModel

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
