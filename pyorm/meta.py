import copy
import functools
import weakref


class Meta(type):
    """
        NOTE: name is stupid, sounds like a little caesar's commercial.
    """
    def __getattr__(cls, attr):
        if attr == 'db_table':
            cls.db_table = cls.owner.__name__.lower()
        elif attr == 'verbose_name':
            cls.verbose_name = cls.owner.__name__
        elif attr == 'auto_primary_key':
            cls.auto_primary_key = True
        elif attr == 'auto_filters':
            cls.auto_filters = []
        else:
            raise AttributeError(attr)

        return getattr(cls, attr)

    def __call__(cls, *args, **kwargs):
        instance = cls.__new__(cls)

        # Make sure that all the meta options are copied over to the instance if
        # they are of the correct type, otherwise we assume the user is doing
        # things that will still return the proper data, and doesn't need to be
        # copied.
        instance.owner = weakref.proxy(kwargs['_owner'])
        instance.owner_ref = weakref.ref(kwargs['_owner'])
        del(kwargs['_owner'])

        if isinstance(cls.db_table, basestring):
            instance.db_table = cls.db_table
        else:
            instance.db_table = instance.owner.__class__.__name__

        if isinstance(cls.verbose_name, basestring):
            instance.verbose_name = cls.verbose_name

        if isinstance(cls.auto_primary_key, bool):
            instance.auto_primary_key = cls.auto_primary_key

        if isinstance(cls.auto_filters, (tuple, list)):
            instance.auto_filters = copy.deepcopy(cls.auto_filters)

        instance.__init__(*args, **kwargs)
        return instance
