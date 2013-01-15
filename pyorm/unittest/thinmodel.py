import unittest

from pyorm.model.thinmodel import ThinModel
# really didnt want to import this, but its needed for testing _model_parent
from pyorm.model import Model
from pyorm.field import Field


class DummyObject(Model):
    class Fields(object):
        test = Field()


class TestThinModel(unittest.TestCase):
    def setUp(self):
        self.thinmodel = ThinModel(
            _model_name='test_name', _model_parent=DummyObject())

    def test_010(self):
        """ ThinModel: __init__ properly sets up the model object. """
        self.assertEqual(self.thinmodel._properties.__class__.__name__, 'Prop')
        self.assertEqual(self.thinmodel._properties.name, 'test_name')
        self.assertEqual(type(self.thinmodel._properties.parent), DummyObject)

    def test_020(self):
        """ ThinModel: reset() properly sets up the _recordset, _recordindex, _values, _old_values attributes. """
        self.thinmodel.reset()

        self.assertEqual(getattr(self.thinmodel, '_recordset', False), None)
        self.assertEqual(getattr(self.thinmodel, '_recordindex', False), None)
        self.assertEqual(getattr(self.thinmodel, '_values', False), {})
        self.assertEqual(getattr(self.thinmodel, '_old_values', False), {})

    def test_030(self):
        """ ThinModel: _unique_columns() returns an empty list """
        self.assertEqual(self.thinmodel._unique_columns(), [])

    def test_040(self):
        """ ThinModel: __getattr__ returns Meta and Field objects"""
        self.assertEqual(self.thinmodel.Fields.__class__.__name__, 'Fields')
        self.assertEqual(self.thinmodel.Meta.__class__.__name__, 'Meta')

    def test_041(self):
        """ ThinModel: __getattr__ Raises an attribute error when trying to access a value not in self._values and not Meta, Fields """
        self.assertRaises(AttributeError, getattr, self.thinmodel, 'fish')

    def test_050(self):
        """ ThinModel: Fields.column_name returns a generic Field() object when queried """
        self.assertEqual(
            self.thinmodel.Fields.test.__class__.__name__, 'Field')

    def test_051(self):
        """ ThinModel: Fields._field_list always returns true when checking for a column """
        self.assertTrue('cheese' in self.thinmodel.Fields._field_list)

    def test_052(self):
        """ ThinModel: Meta.table returns the name of the model who owns it """
        self.assertEqual(self.thinmodel.Meta.table, 'test_name')

    def test_060(self):
        """ ThinModel: _parse_record sets the correct values based on the index passed """
        self.thinmodel._recordset = [
            {'DummyObject.test_name.field1': 0, 'DummyObject.test_name.field2':
                'teststring', 'DummyObject.parentfield': 'parentfield'},
            {'DummyObject.test_name.field1': 1, 'DummyObject.test_name.field2':
                'teststring2', 'DummyObject.parentfield': 'parentfield'}
        ]
        for index, row in enumerate(self.thinmodel._recordset):
            self.thinmodel._parse_record(index)
            self.assertEqual(index, self.thinmodel._recordindex)
            # parse_record should filter out 'DummyObject.parentfield' from each row
            self.assertEqual(len(self.thinmodel._values), 2)
            for column in self.thinmodel._values.keys():
                self.assertEqual(row['{0}.{1}'.format('.'.join(self.thinmodel._properties.column_chain), column)], self.thinmodel._values[column])

    def test_070(self):
        """ ThinModel: __iter__ correctly iterates through the records """
        self.thinmodel._recordset = [
            {'DummyObject.test_name.field1': 0, 'DummyObject.test_name.field2':
                'teststring', 'DummyObject.parentfield': 'parentfield'},
            {'DummyObject.test_name.field1': 1, 'DummyObject.test_name.field2':
                'teststring2', 'DummyObject.parentfield': 'parentfield'}
        ]

        for obj in self.thinmodel:
            self.assertEqual(len(obj._values), 2)
            for column in obj._values.keys():
                self.assertEqual(obj._recordset[obj._recordindex]['{0}.{1}'.format('.'.join(obj._properties.column_chain), column)], obj._values[column])

    def test_080(self):
        """ ThinModel: __reversed__ correctly iterates through the records """
        self.thinmodel._recordset = [
            {'DummyObject.test_name.field1': 0, 'DummyObject.test_name.field2':
                'teststring', 'DummyObject.parentfield': 'parentfield'},
            {'DummyObject.test_name.field1': 1, 'DummyObject.test_name.field2':
                'teststring2', 'DummyObject.parentfield': 'parentfield'}
        ]

        for obj in reversed(self.thinmodel):
            self.assertEqual(len(obj._values), 2)
            for column in obj._values.keys():
                self.assertEqual(obj._recordset[obj._recordindex]['{0}.{1}'.format('.'.join(obj._properties.column_chain), column)], obj._values[column])
