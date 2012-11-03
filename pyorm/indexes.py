import weakref


class MetaIndexes(type):
    """
        Metaclass for Indexes objects on models which is added to existing Indexes
        definitions on Model.__new__().  This handles collection of unbound objects,
        as well as the binding when the Indexes class for that model is instantiated.
    """
    def __getattribute__(cls, attr):
        """
            Return the given unbound index class.  If the _unbound list has not
            yet been generated, we generate it here (which also sets the translated
            name on the unbound object).
        """
        def generate_unbound(cls):
            cls._unbound = []

            for name, item in cls.__dict__.items():
                if hasattr(item, 'bind'):
                    cls._unbound.append(name)

                    if name[-1] == '_':
                        trans_name = name[:-1]
                    else:
                        trans_name = name

                    item.name = trans_name

            return cls._unbound

        try:
            if attr == '_unbound':
                # push the defined indexes into a list on the model the first time
                # the _unbound object is accessed.
                try:
                    return type.__getattribute__(cls, '_unbound')
                except AttributeError:
                    return generate_unbound(cls)
            else:
                try:
                    type.__getattribute__(cls, '_unbound')
                except AttributeError:
                    generate_unbound(cls)

                return type.__getattribute__(cls, attr)
        except AttributeError:
            raise AttributeError(attr)

    def __call__(cls, *args, **kwargs):
        """
            This handles binding each of the Index objects as a new instance
            at the time when the Indexes class is instantiated.  This insures
            that they are available when Indexes.__init__() is called (if it
            exists).
        """
        instance = cls.__new__(cls)
        instance._owner = weakref.proxy(kwargs['_owner'])
        instance._owner_ref = weakref.ref(kwargs['_owner'])
        del(kwargs['_owner'])

        for name in cls._unbound:
            if name[-1] == '_':
                trans_name = name[:-1]
            else:
                trans_name = name

            setattr(instance, name, getattr(instance, name).bind(
                name=trans_name, owner=kwargs.get('_owner', None)))

        instance.__init__(*args, **kwargs)
        return instance
