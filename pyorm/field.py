import datetime
import numbers
import time


class UnboundField(object):
    """
        Uninitialized version of all field objects, which records in what order
        it was initialized.  This is primarily used to ensure each time a new
        Model instance is initialized a new field object is created, rather
        than having to worry about invoking Field.__copy__() and worrying about
        any changes that might have happened to the original instance attached
        to the Model class.
    """
    idx = 0

    def __init__(self, cls, **kwargs):
        self.field_type = cls
        self.kwargs = kwargs
        UnboundField.idx += 1
        self.idx = UnboundField.idx

    def bind(self, name, trans_name, owner):
        kwargs = dict(self.kwargs)
        kwargs.update({'_name': name, '_trans_name': trans_name,
                       '_owner': owner})
        instance = self.field_type(**kwargs)
        instance.idx = self.idx
        instance.unbound_field = self
        setattr(owner.c, name, instance)


class MetaField(type):
    """
        Returns an unbound field if we don't know all the information about
        the field yet.
    """
    def __call__(cls, **kwargs):
        if len({'_trans_name', '_owner', '_name'} & set(kwargs.keys())) == 3:
            instance = cls.__new__(cls)
            instance.__init__(**kwargs)
            return instance
        else:
            return UnboundField(cls, **kwargs)


class Field(object):
    """
        Basic Field object, to be attached to models
    """
    __metaclass__ = MetaField

    @property
    def value(self):
        if self._idx != self.owner.current_idx:
            self._value = self.owner._records[self.owner.current_idx]
            self._value = self.to_python(self._value)
            self._idx = self.owner.current_idx

        return self._value

    @value.setter
    def value(self, val):
        if self._value != val:
            self._changed = True
            self._value = val

    def __init__(self, default=None, null=False, **kwargs):
        self.default = default
        self.null = null
        self._idx = None
        self._changed = False
        self._value = None

    def to_python(self, val):
        return value

    def to_db(self, val):
        return value


class Integer(Field):
    def __init__(self, length=None, unsigned=False, autoincrement=False, **kwargs):
        super(Integer, self).__init__(**kwargs)
        self.length = length
        self.unsigned = unsigned
        self.autoincrement = autoincrement


class TinyInt(Integer):
    pass


class SmallInt(Integer):
    pass


class MediumInt(Integer):
    pass


class BigInt(Integer):
    pass


class UnixTimestamp(Integer):
    def to_python(self, val):
        """
            Attempts to return a datetime object when returning data from
            the database, should throw a TypeError if the conversion fails.
        """
        return datetime.datetime.fromtimestamp(val)

    def to_db(self, val):
        """
            Attempts to convert the object to an int() if possible, except
            when the object happens to be an expression/column/model from
            the ORM, in which case the original value is returned, as that
            indicates it is an expression that the db will need to evaluate
            when the query is actually executed.
        """
        if isinstance(val, numbers.Integral) or hasattr(val, 'token_type'):
            return val
        elif hasattr(val, 'timetuple'):
            return int(time.mktime(val.timetuple()))
        else:
            return int(val)
                


class Decimal(Field):
    def __init__(self, precision=None, scale=None, unsigned=False, **kwargs):
        super(Field, self).__init__(self, **kwargs)
        self.precision = precision
        self.scale = scale
        self.unsigned = unsigned


class Char(Field):
    def __init__(self, length=None, **kwargs):
        super(Field, self).__init__(self, **kwargs)
        self.length = length


class Timestamp(Field):
    def __init__(self, on_update=None, **kwargs):
        super(Field, self).__init__(self, **kwargs)
        self.on_update = on_update
