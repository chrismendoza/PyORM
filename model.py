import copy

from functools import wraps

from orm import session


def clones(func):
    """
        Creates a clone of the model the method was passed before actually
        trying to perform the operation, and performs the operation on the
        cloned copy.

        This is done to preserve the state of models while iterating, as well as
        allowing the user to create a base model with some simple filters on it,
        then later create branches of that model based on the original.
    """
    @wraps(func)
    def wrapper(instance, *args, **kwargs):
        new_instance = type(instance)(
            _parent=instance.objects.parent, session=instance.objects.session)

        return func(new_instance, *args, **kwargs)

class Manager(object):
    """
        Container responsible for managing the session for a model instance,
        as well as storing all the relevant information regarding the current
        state of the model.
    """
    @property
    def session(self):
        """
            If no session has been set on the model previously, go ahead and
            grab the default session, otherwise, just return the current one.
        """
        if not hasattr(self, '_session'):
            self._session = session.default_session

        return self._session

    @session.setter
    def session(self, new_session):
        """
            Try to replace the current session object with a new one.  Useful if
            you want to read data from one session and insert into another, for
            example if two separate configs are in use at the same time, a new
            session can be started with the new config, so that data can be
            transferred from one session to the other, with as little hassle as
            possible.
        """
        if self._session.is_dirty:
            Exception(
                'Tried to change the current session for model {model} before '
                'previous transaction was committed or reverted.'.format(
                    model=self.model.Meta.verbose_name))
        else:
            self._session = new_session

    def __len__(self):
        pass

    def __iter__(self):
        pass

    def __reversed__(self):
        pass

    def __init__(self, model):
        self.model = model

        self._primary_fields = []
        self._generated_fields = []
        self._filters = []
        self._grouping = []
        self._having = []
        self._ordering = []

    # request
    @clones
    def fields(self, *columns, **compound_columns):
        """
            PyORM supports two types of field assignments, columns, and compound
            columns.  Columns are indicators of which fields should be pulled
            back from the table, and are useful for limiting the amount of data
            pulled back for an individual query (for example if you had a table
            containing a bunch of binary data, with a name and id for each, but
            only wanted to grab the name of a particular id, telling the ORM to
            pull only the name and id back would probably speed up your lookup).

            Adding a normal column is done like so:
                SampleModel.fields(C.field_name)

            NOTE: Adding any column as a normal column automatically forces the
            ORM to only pull back that field, and any other normal/compound
            columns specified before the query, any other column data will not
            be available in the result set returned.  When data is requested
            that was not in the original query, a warning is raised.

            In addition, PyORM supports the idea of compound columns, which are
            columns which can be any combination of constant and column data, or
            expressions containing both.  These are useful when you want to
            utilize the ORM's processing power to compute a custom field from
            other available data.

            Adding a compound column can be done either of these ways:
                # each row returned will have a custom key equal to test
                SampleModel.fields(custom='test')

                # each row returned will have a custom key equal to (f1 * f2)
                SampleModel.fields(custom=(C.f1 * C.f2))

            NOTE: Each call to Model.fields() clones the original instance.
        """
        pass

    @clones
    def filter(self, *expressions, **django_expressions):
        """
            PyORM filters are defined by passing expressions to the filter
            method.  This allows the ORM to support complex queries when needed
            without needing to import a bunch of odd functions (except in the
            case of actual database functions).

            NOTE: Each call to Model.filter() adds to any other filters set
            before it, but also returns a new copy of the model instance being
            filtered upon.

            Adding a filter looks like:
                SampleModel.filter(C.field1 == 'value1')

            Adding a filter with relationships:
                SampleModel.filter(C.relationship1.field1 == 'value1')
        """
        pass

    @clones
    def group(self, *groupings):
        pass

    @clones
    def having(self, *having):
        pass

    @clones
    def order(self, *ordering):
        pass

    # actions
    def save(self):
        pass

    def insert(self, *rows, **columns):
        pass

    def replace(self, *rows, **columns):
        pass

    def merge(self, *rows, **columns):
        pass

    def update(self, **columns):
        pass

    @clones
    def delete(self, cascade=False):
        pass

    @clones
    def get(self):
        pass

    @clones
    def all(self):
        pass

    def create(self):
        pass

    def drop(self):
        pass

    def alter(self):
        pass

    def truncate(self):
        pass


class Meta(type):
    def __new__(cls, name, bases, attrs):
        """
            Allows us to pre-populate a list of unbound objects when the model
            is first encountered by the program, so that when the instance is
            later created in __call__, we don't have to determine which objects
            need to be attached to the model.
        """
        new_class = type.__(cls, name, bases, attrs)
        new_class._unbound = []

        # record the fields and relationships defined on the model
        for name, item in new_class.__dict__.items():
            if hasattr(item, bind):
                new_class._unbound.append(name)

        indexes = getattr(new_class, 'Indexes', None)

        # record the indexes defined on the model
        if indexes is not None:
            indexes._unbound = []

            for name, item in indexes.__dict__.items():
                if hasattr(item, bind):
                    indexes._unbound.append(name)

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
        instance.objects = Manager(model=instance)

        # Assigns a parent model to a given object.  This should only be used
        # when creating a new model for a relationship, and as such is prefixed
        # with '_' so that people are discouraged from using it in their code.
        instance.objects.parent = kwargs.pop('_parent', None)

        # Allows a user to instantiate a model with a session other than the one
        # that is registered as the default.  If this is not done when the
        # model is first instantiated and the session is already dirty, it will
        # make it impossible to change without committing/reverting the session.
        instance.objects.session = kwargs.pop('session', default_session)

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

        indexes = getattr(cls, 'Indexes', None)

        if indexes is not None:
            # Instantiate the indexes class so that any methods defined on it
            # will work properly (including properties)
            instance.Indexes = indexes()
        else:
            instance.Indexes = type('Indexes', (object,), {})()
            instance.Indexes._unbound = []

        instance.Indexes.model = instance

        for name in instance.Indexes._unbound:
            if name[-1] == '_':
                trans_name = name[:-1]
            else:
                trans_name = name

            setattr(indexes, name,
                getattr(indexes, name).bind(name=trans_name, owner=instance))

        # Make sure that all the meta options are copied over to the instance if
        # they are of the correct type, otherwise we assume the user is doing
        # things that will still return the proper data, and doesn't need to be
        # copied.

        # NOTE: As with indexes, the Meta class does get instantiated, so it is
        # possible to define an __init__, __new__ or pretty much anything else
        # so properties should work correctly, as should any instance or class
        # method.
        meta = getattr(cls, Meta, None)

        if meta is not None:
            instance.Meta = meta()
        else:
            instance.Meta = type('Meta', (object,), {})()

        instance.Meta.model = instance

        db_table = getattr(meta, 'db_table', cls.__name__.lower())
        if isinstance(db_table, basestring):
            instance.Meta.db_table = copy.copy(db_table)

        verbose_name = getattr(meta, 'verbose_name', cls.__name__)
        if isinstance(verbose_name, basestring):
            instance.Meta.verbose_name = copy.copy(verbose_name)

        auto_primary_key = getattr(meta, 'auto_primary_key', True)
        if isinstance(auto_primary_key, bool):
            instance.Meta.auto_primary_key = copy.copy(auto_primary_key)

        # if the read or write server are not defined, use the defaults from the
        # session data.  If the session doesn't include a default, blow up.
        for server_type in ('read_server', 'write_server'):
            server = getattr(meta, server_type,
                getattr(instance.objects.session, 'default_{0}'.format(server)))

            if isinstance(server, basestring):
                servers = [copy.copy(server),]
                setattr(instance.Meta, server_type, servers)
            elif isinstance(server, (list, tuple)):
                servers = copy.deepcopy(server)
                setattr(instance.Meta, server_type, servers)

        auto_filters = getattr(meta, 'auto_filters', [])
        if isinstance(auto_filters, (tuple, list)):
            instance.Meta.auto_filters = auto_filters

        instance.__init__(*args, **kwargs)

        return instance


class Model(object):
    """
        The model class keeps track of what filters have been applied, which
        fields have been requested, as well as any groupings that may have been
        applied.

        This is also responsible for performing save, insert, replace, update,
        delete, get, all, create, drop, alter, and truncate operations.

        class SampleModel(Model):
            # If a primary key is defined, then we use that as the primary key.
            # If no primary key is defined, The model will build one called
            # 'id', unless `auto_primary_key = False` is specified in the Meta
            # information.  This allows the user to build their application
            # without necessarily worrying about the underlying database
            # structure (though they should be concerned with it if they have
            # any hopes for the thing to scale), while also allowing the
            # flexibility of alternate primary key names, multi-value primary
            # keys and tables with no primary key, when deemed appropriate.
            primary_key = Integer(primary=True)

            # define a general field.  Fields will automatically store their
            # name as the attribute `name` off of the field attribute on the
            # model instance.
            code = Integer(default=0)
            status = Integer(default=0)

            # Builds a field called relationship1_id on the SampleModel table,
            # and uses that field to map to Sample2ndModel.id (or whatever the
            # primary key is).  This is the default behavior when no filters are
            # defined on a relationship.
            relationship1 = OneToMany(Sample2ndModel)

            # Uses the filters provided to gather the related Sample2ndModel
            # results does not build an actual field on the model, so any
            # mappings have to be done by hand. This should be used when dealing
            # with a legacy database, or in the case that multiple fields are
            # mapped across a pair of tables.
            relationship2 = OneToMany(
                Sample2ndModel, filter=[C.field1 == C.relationship2.extra_id])

            # Relationships can refer to models not in the current namespace as
            # well by providing the name of the model as the first argument, and
            # the import path via the import_from keyword arguement.  This is
            # also useful when trying to avoid circular imports, and can be used
            # with filters as well.

            # This method of importing can also be used to limit the models
            # that are imported when the SampleModel is loaded, as importing
            # SampleModel would cause Sample2ndModel to be imported, as well as
            # any other models which are connected to Sample2ndModel.
            relationship3 = OneToMany(
                'Sample2ndModel', import_from='path.to.model')

            Indexes:
                # define an index on the model, if unique is set to True, the
                # ORM creates a unique index in the database (when supported).
                index1 = Index(fields=('code', 'status'), unique=True)

            Meta:
                # The table name in the database.
                db_table = 'sample_model'

                # human readable version of the name
                verbose_name = 'Sample Model'

                # Specify that if this model doesn't have a primary_key defined,
                # that it should not attempt to automatically create one.
                auto_primary_key = False

                # Defines a list of read and write servers that this model is
                # attached to.  If a list/tuple of servers are assigned, the
                # model will randomly pick which one it reads/writes to.

                # NOTE:
                # If the session is using transactions and a write has been
                # done but not committed, the model will use the same server for
                # both read and write, regardless of the rules specified below
                # until the transaction has actually been committed or reverted.
                write_server = 'read_server'
                read_server = 'write_server'

                # The model will automatically apply auto filters whenever a
                # query is run.  Auto filters can be either a list of filters or
                # a property which returns a list of filters.  In the second
                # case, the model instance is available via self.model.

                # Auto filters are useful in situations where you need to
                # enforce certain permissions at the model level, so that the
                # application code doesn't need to know about it, and it doesn't
                # end up getting missed when someone is using the model.
                auto_filters = [C.status == 1]

    """
    __metaclass__ = Meta

    def __getattr__(self, attr):
        try:
            return getattr(self.objects, attr)
        except AttributeError:
            # since the error was actually caused when the user tried to call
            # attr off of the model rather than off the Manager, raise that way.
            raise AttributeError(attr)
