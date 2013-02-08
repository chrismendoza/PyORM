import inspect
import unittest

from pyorm.model import MetaModel, Model, RecordProxy, clones, results_loaded
from pyorm.field import Integer
from pyorm.relationship import OneToOne


class MockModel(Model):
    test_ = Integer(length=3, default=0, null=False, unsigned=False)
    testr_ = OneToOne()


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
        self.assertTrue(hasattr(MockModel, 'testr_'))
        self.assertTrue(hasattr(MockModel.testr_, 'bind'))

    def test_relationships_instance(self):
        model = MockModel()
        self.assertFalse(model.__dict__.get('testr_', False))
        self.assertFalse(inspect.isclass(model.r.testr_))

    def test_fields_cls(self):
        self.assertTrue(hasattr(MockModel, 'test_'))
        self.assertTrue(hasattr(MockModel.test_, 'bind'))
    
    def test_fields_instance(self):
        model = MockModel()
        self.assertFalse(model.__dict__.get('test_', False))
        self.assertFalse(inspect.isclass(model.c.test_))


class ModelTestCase(unittest.TestCase):
    def test_copy(self):
        # Returns a new copy of the model with any results in the fields
        pass

    def test_deepcopy(self):
        # Returns an exact clone of the model and all relationships
        pass

    def test_add_field(self):
        model = MockModel()
        model.fish_taco = Integer(length=4, default=0, null=True, unsigned=True)
        self.assertFalse(model.__dict__.get('added_field', False))
        self.assertTrue(hasattr(model.c, 'added_field'))
        self.assertFalse(inspect.isclass(model.c.added_field))

    def test_add_relationship(self):
        model = MockModel()
        model.added_relationship = OneToOne()
        self.assertFalse(model.__dict__.get('added_relationship', False))
        self.assertTrue(hasattr(model.r, 'added_relationship'))
        self.assertFalse(inspect.isclass(model.r.added_relationship))

    def test_owner(self):
        # Get/set the owner on the model and expressions
        pass

    def test_current_idx(self):
        # Get/set index on the model
        pass

    def test_result_loaded(self):
        # Get/set result_loaded property on the model
        pass

    def test_add_field(self):
        # Test adding a field to a model instance (confirm it doesn't bleed
        # through to the class object).
        pass

    def test_add_relationship(self):
        # Test adding a relationship to a model instance (confirm it doesn't
        # bleed through to the class object).
        pass

    def test_fields(self):
        # Test adding basic fields to the requested data set.  If this is the
        # if the requested field is from a relationship it should add the
        # relationship to the eager load list and also request any unique keys
        # for that related model (so the user can re-save the data properly).
        pass

    def test_compound_fields(self):
        # Test adding compound fields, should add a CompoundField object to
        # the model instance object if it doesn't already exist.  If a
        # CompoundField object already exists, just replace the expression
        # and raise a warning.
        #
        # If there is a reference to a relationship that has not yet been
        # added to the eager load group, add it when the compound field is
        # set.
        pass

    def test_filters(self):
        # Test adding a filter. If the expression uses a relationship
        # which has not yet been joined, add it to the eager load set and add
        # the unique columns for that model to the list of data pulled back.
        pass

    def test_having(self):
        # Test adding a `having` parameter. If the expression uses a relationship
        # which has not yet been joined, add it to the eager load set and add
        # the unique columns for that model to the list of data pulled back.
        pass

    def test_order(self):
        # Test adding a `order by` parameter. If the expression uses a relationship
        # which has not yet been joined, add it to the eager load set and add
        # the unique columns for that model to the list of data pulled back.
        pass

    def test_group(self):
        # Test adding a `group by` parameter. If the expression uses a relationship
        # which has not yet been joined, add it to the eager load set and add
        # the unique columns for that model to the list of data pulled back.
        pass

    def test_join(self):
        # Modify a relationship in place (useful for switching between an inner
        # and left/right/outer join type on the fly).
        pass

    def test_map(self):
        # Add a mapping object, and the mapping dict to be used for every iteration.
        pass

    def test_reset_map(self):
        # Should remove the currently set mapping object (if any).
        pass

    def test_clone(self):
        # Tests to see if cloning works. Should work both prior to and after pulling
        # a result set, and should allow for setting an index (if in range).
        pass

    def test_scalar(self):
        # Should trigger a selection of the first value from the first row of data
        # from the model's table which matches the filters applied to this model.
        # Does not throw an error if no filters are set, because it may be the
        # intention of the user to grab a random row from the table.
        #
        # Does throw an error if no results are returned.
        pass

    def test_one(self):
        # Should trigger a selection of the first row of data from the model's
        # table which matches the filters applied to this model.  Does not throw
        # an error if no filters are set, because it may be the intention of the
        # user to grab a random row from the table.
        pass

    def test_get(self):
        # Should trigger a selection of all data from the model's table on the
        # read connection that matches the filters applied to this model.  If
        # no filters are set should raise an exception letting the user know that
        # they should be using Model.all() in these situations
        pass

    def test_all(self):
        # Should trigger a selection of all data from the model's table on the
        # read connection.
        pass

    def test_iter(self):
        # iterates over a model's result data, should return a RecordProxy
        # object for each row.
        pass

    def test_iter_with_map(self):
        # iterates over a model's result data, should return the mapped object
        # on each iteration instead of a RecordProxy object.
        pass

    def test_insert(self):
        # Should trigger a insert on the database connection that this model
        # is set to write to for this model's table.
        pass

    def test_replace(self):
        # Should trigger a replace on the database connection that this model
        # is set to write to for this model's table.
        pass

    def test_update(self):
        # Should trigger a update on the database connection that this model
        # is set to write to for this model's table.
        pass

    def test_delete(self):
        # Should trigger a delete on the database connection that this model
        # is set to write to for this model's table.
        pass

    def test_truncate(self):
        # Should trigger a truncate on the database connection that this model
        # is set to write to for this model's table.
        pass

    def test_create(self):
        # Should trigger a create on the database connection that this model
        # is set to write to.
        pass
