import copy
import collections
import functools
import weakref

from pyorm.indexes import MetaIndexes
from pyorm.meta import Meta
from pyorm.expression import Expression
from pyorm.token import *


Mapping = collections.namedtuple('Mapping', ('function', 'key_map'))


class RecordProxy(object):
    """
        The RecordProxy object is used as a simple wrapper around a model,
        which stores the current iteration index and the model it came from.

        Each time an attribute is accessed on RecordProxy, that attribute
        lookup is passed through to the model, but before doing so, RecordProxy
        checks to see if:
        a) has the model has already been cloned?
        b) if it hasn't, is the index on the model different from the index in
           the record?

        If case `b` is true, RecordProxy clones the model object, and sets the
        index on the clone to that of it's internal index.

        This keeps the processing time during iteration to a minimum in most
        cases where the model is just being iterated over as a result set, but
        allows the user to compare values from two different iteration points
        in the same record set.

        This can also be used to allow multiple iterations as multiple starting
        points (hopefully a rare use case).
    """
    __slots__ = ('_model', '_idx', '_cloned')

    def __init__(self, model, idx):
        self._model = weakref.proxy(model)
        self._idx = idx
        self._cloned = False

    def __getattr__(self, attr):
        if not self._cloned and self.idx != self.model.current_idx:
            self.model = self.model._clone()
            self.model.current_idx = self.idx
            self._cloned = True
        return getattr(self.model, attr)


def clones(func):
    """
        Creates a clone of the model the method was passed before actually
        trying to perform the operation, and performs the operation on the
        cloned copy.

        This is done to preserve the state of models while iterating, as well as
        allowing the user to create a base model with some simple filters on it,
        then later create branches of that model based on the original.
    """
    @functools.wraps(func)
    def wrapper(instance, *args, **kwargs):
        new_instance = instance.__class__()
        func(new_instance, *args, **kwargs)
        return new_instance


def results_loaded(func):
    """
        Mark that the object has made an attempt in the past to load a result set.
    """
    @functools.wraps(func)
    def wrapper(instance, *args, **kwargs):
        result = func(instance, *args, **kwargs)
        instance.result_loaded = True
        return result


class Container(object):
    pass


class MetaModel(type):
    def __new__(cls, name, bases, attrs):
        """
            Allows us to pre-populate a list of unbound objects when the model
            is first encountered by the program, so that when the instance is
            later created in __call__, we don't have to determine which objects
            need to be attached to the model every time an instance is created.
        """
        new_class = type.__new__(cls, name, bases, attrs)
        new_class._unbound = []

        for name, item in new_class.__dict__.items():
            if hasattr(item, 'bind'):
                new_class._unbound.append(name)

        indexes = getattr(new_class, 'Indexes', None)

        if indexes is None:
            new_class.Indexes = type('Indexes', (object,), {})
            indexes = new_class.Indexes

        # we add a metaclass here so that when a model is added, it can send itself
        # and have a proxy available when the Index.__init__() method is called. This
        # allows the user to reference the instance in Indexes.__init__() if they
        # choose to do so.
        if not hasattr(indexes, '__metaclass__'):
            new_class.Indexes = MetaIndexes(
                indexes.__name__, indexes.__bases__, dict(indexes.__dict__.items()))

        new_class.Indexes.owner = new_class

        meta = getattr(new_class, 'Meta', None)

        if meta is None:
            new_class.Meta = type('Meta', (object,), {})
            meta = new_class.Meta

        if not hasattr(meta, '__metaclass__'):
            new_class.Meta = Meta(
                meta.__name__, meta.__bases__, dict(meta.__dict__.items()))

        new_class.Meta.owner = new_class
        
        return new_class

    def __call__(cls, *args, **kwargs):
        """
            Runs various pre-init tasks when instantiating a new copy of the
            requested model class.  This helps to ensure that __init__ does not
            need to be overridden by user created models extending the model
            class as we can do all the necessary work here instead.  It also
            ensures that every part of the model is set up before the user gets
            hold of it.

            This does however cause an issue if the user defines a different
            metaclass for one of their models, which would need to then be
            derived from Meta.
        """
        instance = cls.__new__(cls)
        instance.c = Container()
        instance.r = Container()

        # Assigns a parent model to a given object.  This should only be used
        # when creating a new model for a relationship, and as such is prefixed
        # with '_' so that people are discouraged from using it in their code.
        # instance.objects.parent = kwargs.pop('_parent', None)

        # Allows a user to instantiate a model with a session other than the one
        # that is registered as the default.  If this is not done when the
        # model is first instantiated and the session is already dirty, it will
        # make it impossible to change without committing/reverting the session.
        #instance.objects.session = kwargs.pop('session', default_session)

        # Bind actual instances of fields and relationships to the new model
        # instance, so that each model instance has it's own unique copy, and
        # changes to those elements don't pollute the class.

        # This also allows us to automagically pass the name of the unbound
        # object to bound object, so it knows what it is supposed to call itself
        # when it is parsed into sql.
        for name in cls._unbound:

            # If the name the user was using in the db interfered with one of
            # the internal model objects, the user is allowed to suffix the name
            # with '_', so the field 'save' would become 'save_' in the model
            # definition, and referred to as such in the python code, but when
            # the field is actually assigned in the database, it is named 'save'
            # the same can also be done to avoid conflicts with python keywords.
            if name[-1] == '_':
                trans_name = name[:-1]
            else:
                trans_name = name

            # Place the bound version on the instance as a replacement for the
            # unbound version that exists on the class.
            getattr(cls, name).bind(name=name, trans_name=trans_name,
                                    owner=instance)

        # Instantiate the indexes class so that any methods defined on it
        # will work properly (including properties)
        instance.Indexes = cls.Indexes(_owner=instance)

        # NOTE: As with indexes, the Meta class does get instantiated, so it is
        # possible to define an __init__, __new__ or pretty much anything else
        # so properties should work correctly, as should any instance or class
        # method.
        instance.Meta = cls.Meta(_owner=instance)

        # TODO: Move this section to pyorm.meta.Meta
        # if the read or write server are not defined, use the defaults from the
        # session data.  If the session doesn't include a default, blow up.
        for server_type in ('read_server', 'write_server'):
            '''
            server = getattr(instance.Meta, server_type,
                getattr(instance.objects.session, 'default_{0}'.format(server)))

            if isinstance(server, basestring):
                servers = [copy.copy(server), ]
                setattr(instance.Meta, server_type, servers)
            elif isinstance(server, (list, tuple)):
                servers = copy.deepcopy(server)
                setattr(instance.Meta, server_type, servers)
            '''

        instance._fields = Expression(op=OP_COMMA)
        instance._compound_fields = Expression(op=OP_COMMA)
        instance._filters = Expression(op=OP_AND)
        instance._order = Expression(op=OP_COMMA)
        instance._having = Expression(op=OP_AND)
        instance._group = Expression(op=OP_COMMA)
        instance._joined_tables = []
        instance._mapping = None

        instance.__init__(*args, **kwargs)

        return instance


class Model(object):
    __metaclass__ = MetaModel

    @property
    def owner(self):
        pass

    @owner.setter
    def owner(self, val):
        pass

    @property
    def current_idx(self):
        pass

    @current_idx.setter
    def current_idx(self, idx):
        pass

    @property
    def result_loaded(self):
        pass

    @result_loaded.setter
    def result_loaded(self, val):
        pass

    def __copy__(self):
        pass

    def __deepcopy__(self):
        pass

    def __getattr__(self, attr):
        """
            Ease of use functionality:
                Maps Model.field -> Model.c.field.value
                Maps Model.relationship -> Model.r.relationship.model

            Also triggers a .get() to be run when a field or relationship
            is accessed but no result has been returned yet.

            NOTE: This functionality is only used in cases where a descriptor
                  has not been added to the base class when initially parsing
                  the fields/relationships (Fields or relationships added
                  after the class was created, always occurs with compound
                  fields, as we never want to add those to the base class object).
        """
        if hasattr(self.c, attr):
            if not self.result_loaded:
                self.get()
            return getattr(self.c, attr).value
        elif hasattr(self.r, attr):
            if not self.result_loaded:
                self.get()
            return getattr(self.r, attr).model
        else:
            raise AttributeError(attr)


    def __setattr__(self, attr, val):
        """
            Allows the model to have it's bindings (fields, relationships)
            to be added to on the fly.  Useful for adding extra relationships
            after the model has been instantiated.

            This also prevents previously defined relationships from being
            overwritten.  If you need to modify a relationship on the fly, they
            can be accessed via Model.r.rel_name.

            NOTE: This functionality is only used in cases where a descriptor
                  has not been added to the base class when initially parsing
                  the fields/relationships (Fields or relationships added
                  after the class was created).
        """
        if hasattr(val, 'bind'):
            pass
        elif attr not in ('c', 'r') and hasattr(self.c, attr):
            getattr(self.c, attr).value = val
        elif attr not in ('c', 'r') and hasattr(self.r, attr):
            raise Exception('Cannot override relationship with another value')
        else:
            object.__setattr__(self, attr, val)

    def __iter__(self):
        """
            If no records have been pulled back, attempt to pull them back using
            the supplied filters (if any).  If a mapping is available, this will
            return each row using the mapped object.
        """
        if not self.result_loaded:
            self.get()

        for idx, row in enumerate(self._result):
            self.current_idx = idx
            if self._map is not None:
                yield self._map.function(**map.args)
            else:
                yield RecordProxy(model=self, idx=idx)

    @clones
    def fields(self, *fields, **compound_fields):
        """
            Add the fields in args and kwargs to the list of columns to be
            returned by the query.  If this method is invoked, only those fields
            which are requested will be accessible via the model and it's pulled
            relationships.

            The primary and unique fields for the primary model and any joined
            relationships are all automatically requested as well, so that any
            row requested can be updated.

            This is an optimization method, used primarily to reduce the amount
            of data transferred for queries with large data sets, where not all
            rows are necessary.  It also allows the user to push some of the
            calculations to the database server when it is quicker to 
        """
        # TODO: Build out field creation objects (CharField, IntField, etc.)
        # we compute the hashes of the already selected fields, so that we only
        # pull back a single instance of the data.  This prevents us from using
        # more bandwidth than necessary.
        hashed_fields = [hash(field) for field in self._fields]
        for field in fields:
            if hash(arg) not in hashed_fields:
                self._fields.append(arg)

        for key, val in compound_fields.items():
            # If the user redefines an already existing key here, and the
            # they could overwrite their original expression.  Since this
            # could be the intended behavior, we make no assumption on which
            # one they wanted and just replace the old entry.

            # It should be noted that they cannot replace a column defined on
            # this table, and attempting to do so will throw an exception.
            if not (hasattr(self.c, key) or
                    hasattr(self.r, key)) or issubclass(getattr(self.c, key), CompoundField):
                if issubclass(val.__class__, Model):
                    val.parent = self
                setattr(self.c, key, CompoundField(name=key, expression=val))
            else:
                raise('Failed to add field `{0}` item already exists for this model.')

    @clones
    def filters(self, *args):
        for arg in args:
            for token in arg.tokens:
                if token.type == T_COL:
                    pass

    @clones
    def order(self, *args):
        pass

    @clones
    def having(self, *args):
        pass

    @clones
    def group(self, *args):
        pass

    @clones
    def join(self, label=None, model=None, join_type=None, filters=None):
        pass

    @results_loaded
    def scalar(self):
        """
            Returns the first value of the first row based on the filters assigned.
        """
        pass

    @results_loaded
    def one(self):
        """
            Returns a single row based on the filters assigned
        """
        pass

    @results_loaded
    def get(self):
        """
            Returns all results based on the filters assigned
        """
        pass

    @results_loaded
    def all(self):
        """
            Returns all results for the table, regardless of the filters assigned
        """
        pass

    def map(self, func, args):
        """
            Allows the user to return a set of a results using the mapping provided

            Example:
                Model.map(dict, {'test1': C.field1, 'test2': C.relationship.field2})

            would cause iteration over the model to return a dict with the key 'test1'
            being the equivalent of Model.field1, and 'test2' being the equivalent of
            Model.relationship.field2.

            This could be used to make the model return a set of User objects or other
            complex constructs.
        """
        def compile(arg):
            if hasattr(arg, '_path'):
                # This compiles the column path to a partial which can be run on
                # iteration, that way there is no issue with accessing values prior to
                # a Model.get() being performed.
                return functools.partial(functools.reduce, (getattr, arg._path, self))
            else:
                return arg

        args = {key: compile(arg) for key, arg in args.items()}
        self._map = Mapping(func, args)

    def reset_map(self):
        self._map = None

    def insert(self, ignore=False, *rows, **fields):
        """
            Model.insert can be used one of three ways:
                Using the data already set on the fields of Model:
                    Model.insert()

                Using the rows passed to insert multiple rows at once:
                    Model.insert({'field1': data1, 'field2': data2},
                                 {'field1': data3, 'field2': data4})

                Using the fields passed as keyword args to quickly insert data:
                    Model.insert(field1=data1, field2=data2, field3=data3)
        """
        pass

    def replace(self, *rows, **fields):
        """
            Model.replace can be used one of three ways:
                Using the data already set on the fields of Model:
                    Model.replace()

                Using the rows passed to replace multiple rows at once:
                    Model.replace({'field1': data1, 'field2': data2},
                                 {'field1': data3, 'field2': data4})

                Using the fields passed as keyword args to quickly replace data:
                    Model.replace(field1=data1, field2=data2, field3=data3)
        """
        pass

    def update(self):
        pass

    def delete(self, cascade=False):
        pass

    def truncate(self):
        pass

    def create(self):
        pass
