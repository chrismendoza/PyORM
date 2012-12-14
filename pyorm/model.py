import copy
import functools
import weakref

from pyorm.indexes import MetaIndexes
from pyorm.meta import Meta
from pyorm.expression import Expression
from pyorm.token import *


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
        #instance.objects = Manager(model=instance)

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
            setattr(instance, name,
                    getattr(cls, name).bind(name=trans_name, owner=instance))

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
        instance.__init__(*args, **kwargs)

        return instance


class Model(object):
    __metaclass__ = MetaModel

    def __copy__(self):
        pass

    def __deepcopy__(self):
        pass

    @clones
    def fields(self, *args, **kwargs):
        # TODO: Build out field creation objects (CharField, IntField, etc.)
        # we compute the hashes of the already selected fields, so that we only
        # pull back a single instance of the data.  This prevents us from using
        # more bandwidth than necessary.
        hashed_fields = [hash(field) for field in fields]
        for arg in args:
            if hash(arg) not in hashed_fields:
                self._fields.append(arg)

        for key, val in kwargs.items():
            # If the user redefines an already existing key here, and the
            # they could overwrite their original expression.  Since this
            # could be the intended behavior, we make no assumption on which
            # one they wanted and just replace the old entry.

            # It should be noted that they cannot replace a column defined on
            # this table, and attempting to do so will throw an exception.
            self._compound_fields[key] = val

    @clones
    def filters(self, *args):
        for arg in args:
            pass

