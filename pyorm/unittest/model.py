from pyorm.connection import Connection
from pyorm.model import Model
from pyorm.field import Field
from pyorm.column import Column as C
import unittest

class DBConfig(object):
    Test = {
        'dialect': 'MySQL',
        'user': 'user',
        'passwd': 'pass',
        'host': 'localhost',
        'port': 3306,
        'db': 'test_db',
        'debug': True,
        'autocommit': True
    }
    default_read_server = 'Test'
    default_write_server = 'Test'

class TestModel(unittest.TestCase):

    def setUp(self):
        Connection.set_config(DBConfig)

        class TestParentModel(Model):
            class Fields(object):
                testparentfield = Field()

            class Meta(object):
                table = 'test_parent_model'

        class TestModel(Model):
            class Fields(object):
                testfield = Field()
                testfield2 = Field()

            class Meta(object):
                table = 'testing_model'

        self.parenttestmodel = TestParentModel()
        self.testmodel = TestModel(_model_name='test_model_name', _model_parent=self.parenttestmodel)

    def test_001(self):
        """ Model: Prop.name returns the correct name for the model """
        self.assertEqual(self.testmodel._properties.name, 'test_model_name')

    def test_002(self):
        """ Model: Prop.name assignment of a non-basestring causes a TypeError """
        self.assertRaises(TypeError, self.testmodel._properties.name, 3)

    def test_003(self):
        """ Model: Prop.name deletion resets the name to the model's class name """
        del(self.testmodel._properties.name)
        self.assertEqual(self.testmodel._properties.name, 'TestModel')

    def test_010(self):
        """ Model: Prop.parent contains the correct parent model """
        self.assertEqual(self.testmodel._properties.parent.__class__.__name__, 'TestParentModel')

    def test_011(self):
        """ Model: Prop.parent assignment does not work with non-models (with the exception of None/False) """
        self.assertRaises(TypeError, self.testmodel._properties.parent, 'test')

    def test_012(self):
        """ Model: Prop.parent assignment works with None/False """
        try:
            self.testmodel._properties.parent = False
            self.testmodel._properties.parent = None
        except:
            self.assertTrue(False)

    def test_013(self):
        """ Model: Prop.parent deletion resets the column_chain and tree values as well """
        del(self.testmodel._properties.parent)
        self.assertEqual(self.testmodel._properties.parent, None)
        self.assertEqual(self.testmodel._properties.tree, [('test_model_name', 'testing_model', self.testmodel)])
        self.assertEqual(self.testmodel._properties.column_chain, ['test_model_name'])

    def test_020(self):
        """ Model: Prop.tree returns a valid set """
        self.assertEqual(self.testmodel._properties.tree, [('TestParentModel', 'test_parent_model', self.parenttestmodel), ('test_model_name', 'testing_model', self.testmodel)])

    def test_030(self):
        """ Model: Prop.column_chain returns a valid set """
        self.assertEqual(self.testmodel._properties.column_chain, ['TestParentModel', 'test_model_name'])

    def test_040(self):
        """ Model: Prop.subquery is being set properly on subquery models """

        class TestSubqueryModel(Model):
            class Fields(object):
                testparam = Field()

            class Meta(object):
                table = 'test_subquery_table'

        self.testmodel.fields(
            test_subquery=TestSubqueryModel().fields(
                C.testparam == 3
            )
        ).get(False)

        subquery = self.testmodel._additional_fields.get_alias('test_subquery')
        self.assertEqual(subquery[0]._properties.subquery, True)

    def test_041(self):
        """ Model: Prop.subquery assignment only allows bool types """
        self.assertRaises(TypeError, self.testmodel._properties.subquery, 3)

    def test_042(self):
        """ Model: Prop.subquery deletion returns the subquery flag to false """
        self.testmodel._properties.subquery = True
        del(self.testmodel._properties.subquery)
        self.assertEqual(self.testmodel._properties.subquery, False)

    def test_050(self):
        """ Model: Prop.subquery_parent is being set properly on subquery models """
        class TestSubqueryModel(Model):
            class Fields(object):
                testparam = Field()

            class Meta(object):
                table = 'test_subquery_table'

        self.testmodel.fields(
            test_subquery=TestSubqueryModel().fields(
                C.testparam == 3
            )
        ).get(False)

        subquery = self.testmodel._additional_fields.get_alias('test_subquery')
        self.assertEqual(subquery[0]._properties.subquery_parent, self.testmodel)

    def test_051(self):
        """ Model: Prop.subquery_parent assignment only allows Model types or None/False"""
        self.assertRaises(TypeError, self.testmodel._properties.subquery, 3)

    def test_052(self):
        """ Model: Prop.subquery_parent assignment works with None/False """
        try:
            self.testmodel._properties.subquery_parent = False
            self.testmodel._properties.subquery_parent = None
        except:
            self.assertTrue(False)

    def test_053(self):
        """ Model: Prop.subquery_parent deletion returns the subquery_parent property to False """
        class TestSubqueryModel(Model):
            class Fields(object):
                testparam = Field()

            class Meta(object):
                table = 'test_subquery_table'

        self.testmodel.fields(
            test_subquery=TestSubqueryModel().fields(
                C.testparam == 3
            )
        ).get(False)

        subquery = self.testmodel._additional_fields.get_alias('test_subquery')

        del(subquery[0]._properties.subquery_parent)
        self.assertEqual(subquery[0]._properties.subquery_parent, False)

    def test_060(self):
        """ Model: Prop.connection() returns a proper connection """
        self.assertEqual(self.testmodel._properties.connection('read'), Connection.Test)
        self.assertEqual(self.testmodel._properties.connection('write'), Connection.Test)

    def test_061(self):
        """ Model: Prop.connection(mode) sets the proper mode """
        self.testmodel._properties.connection('read')
        self.assertEqual(self.testmodel._properties.mode, 'read')
        self.testmodel._properties.connection('write')
        self.assertEqual(self.testmodel._properties.mode, 'write')

    def test_070(self):
        """ Model: Prop.mode returns the mode from the base model (when accessing from a child model) """
        self.parenttestmodel._properties.mode = 'write'
        self.assertEqual(self.testmodel._properties.mode, 'write')

    def test_080(self):
        """ Model: Prop.escaped_values contains all literals used in a query after doing a .get(False) on the model """
        class TestSubqueryModel(Model):
            class Fields(object):
                testparam = Field()

            class Meta(object):
                table = 'test_subquery_table'

        self.testmodel.fields(
            test_subquery=TestSubqueryModel().fields(
                C.testparam == 3
            )
        ).get(False)

        self.assertEqual(self.testmodel._properties.escaped_values, [3])

    def test_081(self):
        """ Model: Prop.escaped_values deletion resets it to [] """
        class TestSubqueryModel(Model):
            class Fields(object):
                testparam = Field()

            class Meta(object):
                table = 'test_subquery_table'

        self.testmodel.fields(
            test_subquery=TestSubqueryModel().fields(
                C.testparam == 3
            )
        ).get(False)

        del(self.testmodel._properties.escaped_values)
        self.assertEqual(self.testmodel._properties.escaped_values, [])
