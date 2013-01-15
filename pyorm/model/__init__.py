import copy
import operator
import warnings

from pyorm.field import Field
from pyorm.column import Column
from pyorm.connection import Connection
from pyorm.exceptions import (
    ColumnNotInResultError,
    RelationshipsImmutableError,
    RelationshipChainError,
    RelationshipLoadError,
    DynamicThinModelCreationError,
    MultiRowInsertDataError,
    RecordNotLoadedError,
    NullAssignmentError
)
from pyorm.expression import Expression
from pyorm.helpers import Values
from pyorm.exceptions import FieldError
from pyorm.token import Token
from pyorm.connection.exceptions import TableMissingError, ColumnMissingError
from pyorm.model.metamodel import MetaModel
from pyorm.model.thinmodel import ThinModel
from pyorm.relationship import Relationship, ThinRelationship, OneToMany, ManyToMany


class Model(ThinModel):
    """
        Model Class
    """
    __metaclass__ = MetaModel

    _connection = Connection()

    def __init__(self, *args, **kwargs):
        """ Set up the Model object instance """
        ThinModel.__init__(self, *args, **kwargs)
        self._debug_object = False
        self._affected_rows = 0
        self.reset()

    def __copy__(self):
        """
            Create a new version of this type of model, setting all internal values to
            references of the current model's attributes of the same name/type
        """
        new_copy = type(self)()
        for prop in ('subquery', 'mode', 'escaped_values'):
            setattr(
                new_copy._properties, prop, getattr(self._properties, prop))
        for expression_type in ('_standard_fields', '_additional_fields', '_filter', '_group', '_having', '_order'):
            setattr(new_copy, expression_type, getattr(self, expression_type))
        for value in ('_values', '_old_values', '_recordset', '_recordindex'):
            setattr(new_copy, value, getattr(self, value))
        return new_copy

    def __deepcopy__(self, memo):
        """
            Deepcopy this model, making an exactly duplicate and copy over all internal properties
        """
        new_copy = type(self)()
        for prop in ('subquery', 'mode', 'escaped_values'):
            setattr(new_copy._properties, prop, copy.deepcopy(
                getattr(self._properties, prop)))
        for expression_type in ('_standard_fields', '_additional_fields', '_filter', '_group', '_having', '_order'):
            setattr(new_copy, expression_type, copy.deepcopy(
                getattr(self, expression_type)))
        for value in ('_values', '_old_values', '_recordset', '_recordindex'):
            setattr(new_copy, value, copy.deepcopy(getattr(self, value)))
        return new_copy

    def __len__(self):
        """
            Return the number of rows that the query returned.  Fire the query if the model has
            nothing in it, and has filters.
        """
        if self._recordset is None and not (self._conditions_altered or self._fields_altered):
            pass
        elif self._conditions_altered or self._fields_altered or self._recordset is None:
            self.get()

        try:
            return len(self._recordset)
        except:
            return 0

    def __getattr__(self, name):
        """
            This allows for accessing fields and relations directly off of a model.  If the name can be
            found in the Model._values dict, and no new filters or fields have been added since that
            data has been pulled, just return that value.

            If additional filters or fields have been added to the model and the name requested can be found
            in either the additional fields expression or in the defined fields repull the record, so that we
            access the correct data before returning it to the user.

            If the name cannot be found in the fields, try and look up any relationships that might match that
            name, returning the relationship if found.

            If none of the above produce a result, raise an Exception.

            Example (given relationship 'test_rel' and field 'test_field'):

                TestModel.test_field #returns the value of that field
                TestModel.test_rel #returns the model associated with that relationship
        """
        if name in self._values.keys() and not (self._conditions_altered == True or self._fields_altered == True):
            # Fetch the value from this model
            val = self._values.get(name)

            if name in self.Fields._field_list:
                val = getattr(self.Fields, name).to_python(val)

            return copy.deepcopy(val)

        elif ((self._conditions_altered == True or self._fields_altered == True) and
             (self._additional_fields.get_alias(name) or name in self.Fields._field_list)):
            # The conditions of this model have been altered, try and fetch it,
            # and return the value if there is one.

            if self._recordset is None or (self._conditions_altered == True or self._fields_altered == True):
                self.get()

            # if we still don't have a record, just return None
            if self._recordset is None:
                return None

            val = self._values.get(name, False)

            if name not in self._values.keys() and name in self.Fields._field_list and len(self._recordset) > 0:
                raise ColumnNotInResultError(name, self.__class__.__name__)

            if name in self.Fields._field_list and len(self._recordset) > 0:
                val = getattr(self.Fields, name).to_python(val)

            return copy.deepcopy(val)

        elif name in self.Fields._field_list and len(self) == 0:
            try:
                return copy.copy(getattr(self.Fields, name).default)
            except AttributeError:
                return None

        elif name in self.Relationships._relationship_list or name in self.Relationships._thin_relationship_list:
            # check the relationship list first, since that is a quick lookup, then if that fails
            # look for the relationship using getattr(), just in case there was a ThinRelationship defined.
            # They also cannot access relationships off a model with no values (unless they have specified filters
            # before trying to access the relationship).

            # if the conditions have been changed, try and fetch this model
            if self._conditions_altered == True:
                self.get()
            elif self._recordset is None:
                raise RecordNotLoadedError

            relationship = getattr(self.Relationships, name)

            # if the model for the relationship hasn't been created yet, trigger its creation
            if relationship._model is False:
                relationship.model

            lookup_list = map(lambda x: '{0}.{1}'.format('.'.join(relationship._model._properties.column_chain), x), relationship._model._lookup_fields)

            if self._recordindex is None:
                lookup_intersection = []
            else:
                lookup_intersection = set(lookup_list) & set(
                    self._recordset[self._recordindex].keys())

            current_record = self._recordset[
                self._recordindex] if self._recordindex is not None else {}

            if (relationship.attached_to != current_record or relationship._model._recordset is None) and len(lookup_intersection):
                relationship.attached_to = current_record
                relationship._model._recordset = [current_record]
                relationship._model._parse_record(0)
                relationship._model._conditions_altered = False

            if relationship.attached_to != current_record or relationship._model._recordset is None:
                if type(relationship) is not ThinRelationship:
                    relationship._model.reset()
                    conditions = copy.deepcopy(relationship.conditions)

                    # Replace all occurances of this model's field within the relationship conditions with
                    # the actual pulled values from this model.
                    for field, val in self._values.items():
                        conditions.replace_column(
                            Column(False, field), copy.deepcopy(val))

                    # Replace all the relationship columns with new columns that point directly to the
                    # related model (so it does not try and eager load a model with its own relationship name.
                    for fieldname, field in relationship._model.Fields.__dict__.items():
                        if issubclass(type(field), Field):
                            conditions.replace_column(Column([relationship.name], fieldname), Column(False, fieldname))

                    relationship._model._filter &= conditions
                    relationship._model._conditions_altered = True

                relationship.attached_to = current_record

            return relationship.model
        else:
            raise ColumnNotInResultError(name, self.__class__.__name__)

    def __setattr__(self, name, value):
        """
            Allows for setting values on to fields, and disallow any changes directly to relationships,
            also allows a passthru for setting other values on this model.

            If the field is not currently loaded (
                the user specified fields or the conditions have changed,
            repull the data from the table, preserving any changes that have been made prior to pulling the
            new record.

            In the event that new filters have been added, any changes the user has made will be ignored.

            If none of the above produce a result, raise an Exception.

            Example (given relationship 'test_rel' and field 'test_field'):

                TestModel.test_field = value #works
                TestModel.test_rel = value #raises an exception
                TestModel.some_other_property = 'cheese' #works
        """
        if name in self.Fields._field_list:
            if len(self._old_values) and not (self._conditions_altered or self._fields_altered) and name not in self._old_values.keys():
                raise ColumnNotInResultError(name, self.__class__.__name__)

            if self._conditions_altered or self._fields_altered:
                # Something was changed repull and wipe out their changes because the user was dumb.
                self.get()

            self._values[name] = getattr(self.Fields, name).to_db(value)
        elif name in self.Relationships._relationship_list or name in self.Relationships._thin_relationship_list:
            raise RelationshipsImmutableError(name, self.__class__.__name__)
        else:
            object.__setattr__(self, name, value)

    def __getitem__(self, limit):
        """
            Allows for setting a starting point and limit to the number of rows returned
        """
        if isinstance(limit, (int, long)):
            limit = (0, limit)
        elif isinstance(limit, slice):
            if limit.start is not None and limit.stop is not None:
                limit = (limit.start, limit.stop)
            elif limit.stop is not None:
                limit = (0, limit.stop)

        if (self._limit is None or (limit[0] == self._limit[0] and limit[1] <= self._limit[1])) and \
                not (self._conditions_altered or self._fields_altered) and self._recordset is not None:
            # The conditions and fields have not been altered since the last query, and the limit requested
            # is within the limit used to pull back those records.  In this case, just update the recordset
            # based on the limit provided.
            self._recordindex = 0
            self._recordset = self._recordset[:limit[1]]
            self._limit = limit
        elif limit != self._limit:
            self._limit = limit
            self._conditions_altered = True
        return self

    def __reversed__(self):
        if (self._conditions_altered or self._fields_altered) or self._recordset is None:
            self.get()

        return ThinModel.__reversed__(self)

    def __iter__(self):
        if (self._conditions_altered or self._fields_altered) or self._recordset is None:
            self.get()

        return ThinModel.__iter__(self)

    def _check_column(self, column, add_fields=False):
        """
            This checks the given column to see if it is attached to a OneToMany or ManyToMany relationship,
            if it is, then it raises an exception.

            Because of the nature of a OneToMany or ManyToMany relationship, pulling it back with this model
            would more than likely result in multiple copies of the same record for this model.  Since would
            not be a desired behavior in most cases, this limits the user to only using OneToOne or ManyToOne
            relationships to eager load data from.
        """
        base = self
        for index, rel in enumerate(column._queue[:-1]):
            if not rel in base.Relationships._relationship_list:

                if len(column._queue[:-1]) == 1:
                    if rel not in base.Relationships._thin_relationship_list:
                        # create a Relationship and ThinModel instance by this name
                        setattr(
                            base.Relationships, rel, ThinRelationship('', ''))
                        new_relationship = getattr(base.Relationships, rel)
                        new_relationship._model = ThinModel()
                        new_relationship.name = rel
                        new_relationship.parent = self
                        base.Relationships._thin_relationship_list.append(rel)
                        base = getattr(base.Relationships, rel)
                else:
                    raise RelationshipChainError(
                        '.'.join(column._queue[:-1]), self.__class__.__name__)
            else:
                base = getattr(base.Relationships, rel).model

        if add_fields:
            base._lookup_fields.append(column._queue[-1])

    def _prepare_expressions(self):
        """
            Update the base model and eager loads for the model and all expressions.

            This sets this model as the owner for the next query that is run from this model, allowing the
            dialect to parse the expressions in the context of this model.  This also gets all the related
            models to be eager loaded and sets them into the self._eager_load dict.
        """
        models = copy.deepcopy(self._eager_load)
        for attr in ('_standard_fields', '_additional_fields', '_filter', '_group', '_having', '_order'):
            expression = getattr(self, attr)
            models = expression.auto_eager_loads(models)
            if attr not in ('_standard_fields', '_additional_fields'):
                tokens = expression.tokenize()
                for column in (token[1] for token in tokens if token[0] is Token.Column):
                    self._check_column(column)

        if self._properties.name in models.keys():
            self._eager_load = models[self._properties.name]
        else:
            self._eager_load = models
        return self

    def _dict_tree_iterator(self, dict_tree, base_path=None):
        """
            convert a dict tree to a list of directories
            Example:
                {
                    'test': {
                        'fish': {},
                        'fries': {
                            'bunny': {}
                        }
                    }
                }

            would be converted into:
            [
                ['test'],
                ['test', 'fish'],
                ['test', 'fries'],
                ['test', 'fries', 'bunny']
            ]
        """
        dict_list = []
        for path, subtree in dict_tree.items():
            if type(base_path) is list:
                new_path = base_path[:]
                new_path.append(path)
                dict_list.append(new_path)
            else:
                new_path = [path, ]
                dict_list.append(new_path)

            if len(subtree):
                dict_list.extend(self._dict_tree_iterator(subtree, new_path))

        return dict_list

    def _get_rel_from_path(self, path):
        """
            Using a list path, returns a related model
        """
        model = self
        for rel in path:
            try:
                model = getattr(model.Relationships, rel, False).model
            except AttributeError:
                return None
        return model

    def _create_table(self, table):
        """ Create the requested table if we can locate it in the models relationships """
        conn = self._properties.connection('write')
        if conn._auto_create_tables:
            model = self._find_table(table)
            if model is not False and type(model) is not ThinModel:
                conn.create_table(model)
            else:
                raise DynamicThinModelCreationError(model._properties.name)

    def _find_table(self, table):
        """ Finds the closest relationship or subquery that is attached to this model """
        if self.Meta.table == table:
            return self
        else:
            for path in self._dict_tree_iterator(self._eager_load):
                rel = self._get_rel_from_path(path)
                if rel is not None:
                    if rel.Meta.table == table:
                        return rel

        for expression in ('_standard_fields', '_additional_fields', '_filter', '_having', '_group', '_order'):
            tokens = [token for token in getattr(
                self, expression).tokenize() if token[0] is Token.Model]
            for token in tokens:
                if token[1].Meta.table == table:
                    return token[1]

        return False

    def _unique_columns(self):
        """
            Returns a list of the UniqueIndex/PrimaryKey fields for this model
        """
        unique_fields = []
        if self._add_unique_fields and not self._properties.subquery:

            for name in self.Indexes._unique_columns:
                unique_fields.append(Column(False, name))

            for path in self._dict_tree_iterator(self._eager_load):
                rel = self._get_rel_from_path(path)
                if rel is not None and type(rel) is not ThinModel:
                    for name in rel.Indexes._unique_columns:
                        unique_fields.append(Column(path, name))

        return unique_fields

    def _query(self, conn, sql, values=[]):
        """
            Send the query to the provided connection, if we get a missing table error, try and create it.
        """
        result = False
        self._operation_successful = False
        try:
            result = conn.query(sql, values)
            self._affected_rows = result.get('count', 0)
            self._debug_object = result.get('debug_object', False)
            if result is not False:
                self._operation_successful = True
        except TableMissingError as obj:
            # if the write connection has auto_create_tables set to true
            # create the table, and return no result (since we just created it)
            if conn._auto_create_tables:
                for table in obj._tables:
                    self._create_table(table)
                result = self._query(conn, sql, values)
            else:
                raise TableMissingError(obj._tables)
        except ColumnMissingError:
            pass

        self._standard_fields = Expression().operator(',')
        self._additional_fields = Expression().operator(',')

        return result

    def _update_values(self, insert_id=False, add_defaults=False):
        """
            Following a successful save/insert/update/replace, copy the _values dict into the _old_values
            dict.
        """
        if insert_id:
            ai_field = None
            for name in self.Fields._field_list:
                if getattr(self.Fields, name).autoincrement:
                    ai_field = name
                    if not add_defaults:
                        break
                elif add_defaults and name not in self._values:
                    self._values[name] = getattr(self.Fields, name).default

            self._values[ai_field] = insert_id

        self._old_values = {}
        self._old_values = copy.deepcopy(self._values)

    def _prepare_new_records(self, *args, **kwargs):
        """
            Prep the self._standard_fields for insert/replace, args are used for
            multi row , while kwargs are used for single row inserts/replaces.

            In the case of single row inserts/replaces the individual columns and
            their associated values are set into the self._standard_fields Expression
            while multi row inserts/replaces use helpers.Values as the first argument
            in the self._standard_fields Expression.

            This allows the dialect to properly format either one, without making
            the insert/replace code anymore bloated than it actually has to be.
        """

        # TODO: Clean this mess up
        # clear out the fields to be set, so that we can set them to the new values
        self._standard_fields._node_list = []
        self._additional_fields._node_list = []

        if len(args) or len(kwargs):
            # The user defined either a row(kwargs) or set of rows(args) that
            # needs to be inserted, reset the module before we proceed.
            self.reset()
            defaults = {}

            # Insert the fields into a defaults dict, for later reference
            for name in self.Fields._field_list:
                defaults[name] = getattr(self.Fields, name).default

            relationship = getattr(getattr(self._properties.parent, 'Relationships', None), self._properties.name, None)

            if relationship is not None:
                conditions = copy.deepcopy(relationship._conditions)

                # The conditions could be a list of conditions or a single expression.  For single
                # Expressions, we want to only use the expression if is an equality check.  Otherwise
                # we ignore it and use the defaults.
                if issubclass(type(conditions), Expression) and conditions._operator == 'EQ':
                    if len(conditions._node_list[0]) == 1:
                        conditions._node_list = reversed(conditions._node_list)

                    for col in conditions.columns():
                        if len(col._queue) == 1 and getattr(self._properties.parent, col._queue[-1], False) is not False:
                            conditions.replace_column(col, self._properties.parent._values[col._queue[-1]])

                    for col in conditions.columns():
                        conditions.replace_column(
                            col, Column(False, col._queue[-1]))

                    defaults[conditions._node_list[0]
                             ._queue[-1]] = Expression(*condition._node_list[1:])

                else:
                    # Lists of conditions need to be looped over, and we only want to use the equality conditions to pull values from
                    # the parent model and use them to fill values on the saved model.
                    conditions = [condition if len(condition._node_list[0]) > 1 else reversed(condition) for condition in conditions if condition._operator == 'EQ']
                    for condition in conditions:
                        for col in condition.columns():
                            if len(col._queue) == 1 and getattr(self._properties.parent, col._queue[-1], False) is not False:
                                condition.replace_column(col, self._properties.parent._values[col._queue[-1]])

                        for col in condition.columns():
                            condition.replace_column(
                                col, Column(False, col._queue[-1]))

                        defaults[condition._node_list[0]._queue[
                            -1]] = Expression(*condition._node_list[1:])

            if len(kwargs):
                # A single row was provided, use the data provided in the kwargs. If that field was not provided, set the value from
                # the defaults.  The if statement below does not include fields if they are set as an auto increment, or they do not
                # actually exist in the field list defined on the model.
                for field_name, value in defaults.items():
                    if not field_name not in self.Fields._field_list:
                        self._values[field_name] = getattr(self.Fields, field_name).to_db(kwargs.get(field_name, value))

            elif len(args):
                # Multiple rows provided, iterate over them and create a valueset
                recordset = []
                valueset = Values()
                columns = defaults.keys()
                column_args = []

                for column in columns:
                    column_args.append(Column(False, column))

                valueset.set_columns(*column_args)

                new_args = []
                for row in args:
                    if type(row) is dict:
                        values = Expression().operator(',')
                        values._force_enclose = True
                        new_row = {}
                        for column in columns:
                            values.append(row.get(column, defaults[column]))
                            new_row[column] = getattr(self.Fields, column).to_db(row.get(column, defaults[column]))

                        new_args.append(new_row)
                        valueset.append(values)
                    else:
                        raise MultiRowInsertDataError(type(row))

                self._recordset = new_args
                self._standard_fields.append(valueset)

        if len(kwargs) or not len(args):
            # set the new values as items to be set
            for name in self.Fields._field_list:
                if name in self._values.keys():
                    if not getattr(self.Fields, name).null and self._values[name] is None:
                        pass
                    else:
                        new_col = Column(False, name) == self._values[name]
                        if self._values[name] is None:
                            new_col._null_assign = True
                        self._standard_fields.append(new_col)

    def _prepare_update(self, **kwargs):
        """
            Check to see there is a record loaded, if not, raise an exception. Load the original data into
            the filters and check to see if any fields have changed.

            If fields have changed, return True, so that the update will run, otherwise, return False so
            the model will just return itself.
        """
        # clear out the fields to be set, so that we can set them to the new values
        self._standard_fields._node_list = []
        self._additional_fields._node_list = []

        if not len(self._old_values) and not len(kwargs.keys()):
            raise RecordNotLoadedError

        if len(kwargs.keys()):
            # allow mass updates when update is passed a list of kwargs
            for name in self.Fields._field_list:
                if name in kwargs:
                    new_col = Column(False, name) == kwargs[name]
                    self._standard_fields.append(new_col)

        elif len(self._old_values):
            # If there were unique columns defined on the model, use those as the fields to match
            # against, since they are always pulled back.  Otherwise, we depend on all the fields
            # being available, (in order to be on the cautious side of things).
            field_set = self.Indexes._unique_columns
            if not len(field_set):
                field_set = self.Fields._field_list

            for name in self.Fields._field_list:
                if (name in self._old_values.keys() and self._old_values[name] != self._values[name]) or \
                        (name in self._values.keys() and name not in self._old_values.keys()):
                    # set any values that have changed into the new standard fields expression, so they
                    # can be properly changed in the database.
                    new_col = Column(False, name) == self._values[name]
                    if self._values[name] is None:
                        if getattr(self.Fields, name).null:
                            new_col._null_assign = True
                        else:
                            raise NullAssignmentError(name)

                    self._standard_fields.append(new_col)

            self._filter = Expression().enclose(False)
            for k in self._old_values.keys():
                # set the original record values as the filters to be matched when we update
                if k in field_set:
                    self._filter.append(
                        Column(False, k) == self._old_values[k])

        elif self._old_values.keys() != self._values.keys():
            diffkeys = set(self._values.keys()) - set(self._old_values.keys())
            raise ColumnNotInResultError(diffkeys[0], self.__class__.__name__)

        return len(self._standard_fields) > 0

    def _prepare_delete(self):
        """
            Reset the filters here, and load the original values as filters, to make sure we
            delete the correct record.  If there is no record currently loaded, check to see
            if there are filters that are new.  If so, perform a blind delete, if not then we
            raise an exception, because we don't want to do a delete all via pyORM (If that is
            their intention, they can write the sql directly using the connection).
        """
        if not len(self._old_values):
            if not (len(self._filter) and self._conditions_altered):
                raise RecordNotLoadedError
        else:
            self._filter = Expression().enclose(False)

            # If there were unique columns defined on the model, use those as the fields to match
            # against, since they are always pulled back.  Otherwise, we depend on all the fields
            # being available, (in order to be on the cautious side of things).
            field_set = self.Indexes._unique_columns
            if not len(field_set):
                field_set = self.Fields._field_list

            for k in self._old_values.keys():
                # set the original record values as the filters to be matched when we update
                if k in field_set:
                    self._filter.append(
                        Column(False, k) == self._old_values[k])

    def get(self, run_query=True):
        """
            Get row(s) from the database, setting run_query to False will return the
            query to be run, rather than actually running the query on the database.

            If no fields have been defined, it will use all fields defined for this model,
            otherwise, it will use whatever the user has defined.

            It will however make additions to the fields that are pulled back based on
            the primary keys and unique indexes that exist on the model (and any related
            models that we are pulling data from, so that if any update is performed, that
            update will use the primary keys and unique keys as a lookup to perform it).
        """
        self._recordset = None
        self._recordindex = None
        self._prepare_expressions()
        conn = self._properties.connection('read')

        if (not (len(self._standard_fields) + len(self._additional_fields))) or self._properties.include_regular_fields:
            # add fields from this model
            self.fields(
                *[Column(False, name) for name in self.Fields._field_list])

            # add fields from eager loaded relationships
            for path in self._dict_tree_iterator(self._eager_load):
                rel = self._get_rel_from_path(path)
                if rel is not None:
                    try:
                        self.fields(*[Column(
                            path, name) for name in rel.Fields._field_list])
                    except TypeError:
                        # ignore it since the field list was not iterable
                        pass

        elif self._add_unique_fields and not self._properties.subquery:
            self.fields(*self._unique_columns())

        decoded = conn.dialect.select(self)
        if not self._properties.subquery and run_query:
            result = self._query(conn, *decoded)

            self._conditions_altered = False
            self._fields_altered = False

            if isinstance(result, dict):
                self._recordset = result.get('result_set', None)
                if self._recordset is not None:
                    self._parse_record(0)
            else:
                self.reset()
            return self
        else:
            # Since we have to return a string here, store the escaped values on the
            # model properties so that we can access them at a later time without having
            # to re-parse the model into the connection's dialect.
            self._properties.escaped_values = decoded[1]
            return decoded[0]

    def save(self, *args, **kwargs):
        """
            The args and kwargs allow for passing a list of dicts to save on the model

            Example:
                # Saves whatever is currently on the model
                Model.save()

                # Saves the values in the dictionary, shortcut to setting
                # the values individually then doing Model.save()
                # but it does require the values to be an insert
                Model.save(field1=val1, field2=val2, field3=val3)

                # Save multiple new rows to the database (batch save), this only works for new rows.
                Model.save(
                    {field1: val1, field2: val2, field3: val3},
                    {field1: val4, field2: val5, field3: val6},
                    {field1: val7, field2: val8, field3: val9}
                )
        """
        self._operation_successful = False
        unique_non_none = [key for key in self.Indexes._unique_columns if self._old_values.get(key, None) is not None]
        if len(unique_non_none) and self._old_values != self._values:
            #record was changed, perform the update
            self.update()
        elif not len(unique_non_none) and (len(self._values) or len(args) or len(kwargs)):
            # insert a new record
            self.insert(*args, **kwargs)

        return self._operation_successful

    def insert(self, *args, **kwargs):
        """
            Run an insert, if no args or kwargs are provided, it will run the insert
            using the values defined in self._values, otherwise uses the values from
            either the args or kwargs. Note that replacing multiple rows does not return
            an iterable set, because there is no perfect method for determining what the
            new row ids would be (the DBAPI only allows for returning the first insert id).

            Example:
                # Saves whatever is currently on the model
                Model.insert()

                # Saves the values in the dictionary, shortcut to setting
                # the values individually then doing Model.save()
                # but it does require the values to be an insert
                Model.insert(field1=val1, field2=val2, field3=val3)

                # Save multiple new rows to the database (batch save), this only works for new rows.
                Model.insert(
                    {field1: val1, field2: val2, field3: val3},
                    {field1: val4, field2: val5, field3: val6},
                    {field1: val7, field2: val8, field3: val9}
                )
        """
        success = False
        self._prepare_new_records(*args, **kwargs)
        self._prepare_expressions()
        conn = self._properties.connection('write')
        result = self._query(conn, *conn.dialect.insert(self))
        success = self._operation_successful

        if result is not False:
            if len(args) > 1:
                self.reset()
            else:
                self._update_values(result['insert_id'], add_defaults=True)
                self._recordset = [dict(map(lambda x: ('{0}.{1}'.format('.'.join(self._properties.column_chain), x[0]), x[1]), self._values.items()))]
                self._recordindex = 0
        return success

    def replace(self, *args, **kwargs):
        """
            The args and kwargs allow for passing a list of dicts to save on the model. Note
            that replacing multiple rows does not return an iterable set, because there is no
            perfect method for determining which rows would get new ids versus which rows
            replaced old ids.  Instead, replacing multiple rows returns a newly reset model.

            Example:
                # Saves whatever is currently on the model
                Model.replace()

                # Saves the values in the dictionary, shortcut to setting
                # the values individually then doing Model.replace()
                Model.replace(field1=val1, field2=val2, field3=val3)

                # Save multiple new rows to the database (batch replace).
                Model.replace(
                    {field1: val1, field2: val2, field3: val3},
                    {field1: val4, field2: val5, field3: val6},
                    {field1: val7, field2: val8, field3: val9}
                )
        """
        success = False
        self._prepare_new_records(*args, **kwargs)
        self._prepare_expressions()
        conn = self._properties.connection('write')
        result = self._query(conn, *conn.dialect.replace(self))
        success = self._operation_successful

        if result is not False:
            if len(args) > 0:
                self.reset()
            else:
                self._update_values(result['insert_id'], add_defaults=True)
                try:
                    # Assume that there is a recordset already in place.  If the recordset is None or False here,
                    # it will bomb out with a TypeError, in which case we need to treat this the same way we would
                    # an insert.
                    self._recordset[self._recordindex].update(dict(map(lambda x: ('{0}.{1}'.format('.'.join(self._properties.column_chain), x[0]), x[1]), self._values.items())))
                except TypeError:
                    self._recordset = [dict(map(lambda x: ('{0}.{1}'.format('.'.join(self._properties.column_chain), x[0]), x[1]), self._values.items()))]
                    self._recordindex = 0
        return success

    def update(self, run_query=True, return_affected_rows=False, **kwargs):
        """
            Run an update, based on the record currently in the model.  If the user explicitly calls this
            and there is not a record loaded, raises an exception.

            Normally returns whether or not the operation was successful.  However, if
            `return_affected_rows` is specified, a tuple consisting of (operation_successful, affected_rows)
            is returned.
        """
        if self._prepare_update(**kwargs):
            self._prepare_expressions()
            affected_rows = 0

            conn = self._properties.connection('write')
            decoded = conn.dialect.update(self)

            if run_query and self._query(conn, *decoded) is not False:
                affected_rows = self._affected_rows

                if len(kwargs.keys()):
                    self.reset()
                else:
                    self._update_values()
                    self._recordset[self._recordindex].update(dict(map(lambda x: ('{0}.{1}'.format('.'.join(self._properties.column_chain), x[0]), x[1]), self._values.items())))
            elif not run_query:
                self._properties.escaped_values = decoded[1]
                return decoded[0]

        if return_affected_rows:
            return (self._operation_successful, affected_rows)
        else:
            return self._operation_successful

    def delete(self):
        """
            Delete the currently loaded record, if no record is loaded into the model, raise an exception
        """
        self._prepare_delete()
        self._prepare_expressions()
        conn = self._properties.connection('write')
        self._query(conn, *conn.dialect.delete(self))
        success = self._operation_successful
        self.reset()
        return success

    def fields(self, *args, **kwargs):
        """
            Define the fields using *args for model and relation fields, while using *kwargs for user created fields,
            since those fields need both an expression to describe them and a name to access them by.

            This also will alter the state of self._fields_altered to reflect the fact that columns/expressions have
            been added to the expression.

            This method raises a FieldError when it encounters a user created field that exists in one of the following:
                self - which would mean it is an attribute on the model itself
                self.Fields - the field already exists as a field of the model, thus would cause confusion if we allowed it
                self.Relationships - To prevent a field accessor from overwriting the accessor for a relation
        """
        if len(args) or len(kwargs):
            self._fields_altered = True

        for index, arg in enumerate(args):
            if type(arg) is Column:
                self._check_column(arg, add_fields=True)
                arg.set_alias(u'.'.join(arg._queue))
            elif not issubclass(type(arg), Expression):
                arg.pop(index)

        self._standard_fields.extend(args)

        for field_name, field in kwargs.items():
            if getattr(self.Fields, field_name, False) or \
                getattr(self.Relationships, field_name, False) or \
                    self._additional_fields.get_alias(field_name):
                raise FieldError(field_name)

            # occasionally it makes sense to return a constant value as an additional field.  This comes in handy when dealing
            # with unions, when both queries may not contain the same fields all the time, and it may make sense to return where
            # the actual result came from (for instance when dealing with two different tables that return the same set of fields)
            if issubclass(type(field), Column):
                self._check_column(field)
                self._additional_fields.append(
                    Expression(field).set_alias(field_name).operator(','))
            elif issubclass(type(field), Expression):
                for item in field.columns():
                    self._check_column(item)
                self._additional_fields.append(field.set_alias(field_name))
            else:
                self._additional_fields.append(
                    Expression(field).set_alias(field_name).operator(','))

            self._lookup_fields.append(field_name)

        return self

    def filter(self, *args):
        """ Add filters the user passes, takes Expression objects """
        self._filter &= Expression(*args)
        self._conditions_altered = True
        return self

    def group(self, *args):
        """ Add group by instructions, takes Column, Expression objects or basestring """
        self._group.extend(args)
        self._conditions_altered = True
        return self

    def having(self, *args):
        """ Add having instructions, takes Column, Expression objects or basestring"""
        self._having.extend(args)
        self._conditions_altered = True
        return self

    def order(self, *args):
        """ Add order by instructions, takes Column or Expression objects """
        self._order.extend(args)
        self._conditions_altered = True
        return self

    def reset(self):
        """
            Resets the model to its default state, defines/redefines the instance variables.
        """
        ThinModel.reset(self)
        for sql_section in ('standard_fields', 'additional_fields', 'group', 'having', 'order'):
            setattr(
                self, u'_{0}'.format(sql_section), Expression().operator(','))

        self._filter = Expression().enclose(False)
        self._eager_load = {}
        self._lookup_fields = []
        self._fields_altered = False
        self._conditions_altered = False
        self._add_unique_fields = True
        self._operation_successful = False
        self._limit = None
        self._affected_rows = 0

        # Since relationships are unique to the model instance, we set them as instance vars here
        self.Relationships = type('Relationships', (object,), {})()
        self.Relationships._relationship_list = type(
            self).Relationships._relationship_list
        self.Relationships._thin_relationship_list = []

        for name in self.Relationships._relationship_list:
            relationship = copy.deepcopy(
                getattr(type(self).Relationships, name))
            relationship.reset(name, self)
            setattr(self.Relationships, name, relationship)

        # meta values also need to be unique to the instance, so when reset is called, copy the values
        # this enables loading values from one database and storing them on another, using the same model
        # definition.  We only copy the dict the first time the model is reset (on __init__) so that any
        # values the user changes after initialization gets preserved.
        if id(self.Meta.__dict__) == id(self.__class__.Meta.__dict__):
            self.Meta = type('Meta', (object,), {})()
            for option in ('read_server', 'write_server', 'engine', 'charset', 'union', 'table'):
                if hasattr(type(self).Meta, option):
                    setattr(self.Meta, option,
                            copy.copy(getattr(type(self).Meta, option)))

        return self

    def join(self, path, join_type='inner', conditions=None):
        """
            Allows the user to explicitly specify the join type, for example:

            # specify that the relationship 'model2' off the current model
            # should be left joined and eager loaded.
            Model.join('model2', 'left')

            # specify that the relationship 'model3' should be eager loaded as
            # a left join off model2 (model2's join type will be preserved).
            Model.join('model2.model3', 'left')
        """
        expanded_path = '.model.'.join(['Relationships.{0}'.format(
            relationship) for relationship in path.split('.')]).split('.')
        relationship = reduce(getattr, expanded_path, self)
        relationship._join = join_type.upper()
        if conditions is not None:
            relationship._conditions.extend(conditions)
        return self

    def eager_load(self, *args):
        """
            Set the args as an eager load or set of eager loads.
        """
        for arg in args:
            if isinstance(arg, basestring):
                arg = arg.split('.')

            if type(arg) in (tuple, list) and len(arg):
                last_node = self._eager_load
                for model in arg:
                    if model not in last_node.keys():
                        last_node[model] = {}
                    last_node = last_node[model]

        return self

    def change_server(self, write_server=None, read_server=None):
        """
            Allows the user to change which server the model is targeting.
            Automatically resets the model, clearing out any data currently loaded,
            so that there is no chance that loading data -> changing the server ->
            saving data would cause data corruption or overwriting the wrong data
            to occur.
        """
        self.reset()

        if write_server:
            self.Meta.write_server = write_server

        if read_server:
            self.Meta.read_server = read_server

    def as_dict(self):
        """
            Returns the base model represented as a dict (only works when a record is loaded)
        """
        items = {}
        for field in self._values:
            if '.' not in field:
                items[field] = self._values[field]

        return dict(items)
