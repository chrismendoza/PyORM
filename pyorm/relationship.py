class UnboundRelationship(object):
    idx = 0

    def __init__(self, cls, **kwargs):
        self.field_type = cls
        self.kwargs = kwargs
        UnboundRelationship.idx += 1
        self.idx = UnboundRelationship.idx

    def bind(self, name, trans_name, owner):
        kwargs = dict(self.kwargs)
        kwargs.update({'_name': name, '_trans_name': trans_name,
                       '_owner': owner})
        instance = self.field_type(**kwargs)
        instance.idx = self.idx
        instance.unbound_field = self
        setattr(owner.r, name, instance)


class MetaRelationship(type):
    """
        Returns an unbound relationhsip if we don't know all the information
        about the field yet.
    """
    def __call__(cls, **kwargs):
        if len({'_trans_name', '_owner', '_name'} & set(kwargs.keys())) == 3:
            instance = cls.__new__(cls)
            instance.__init__(**kwargs)
            return instance
        else:
            return UnboundRelationship(cls, **kwargs)


class Relationship(object):
    __metaclass__ = MetaRelationship

    def __init__(self, model=None, import_dir=None, expression=None, **kwargs):
        pass


class OneToOne(Relationship):
    pass
