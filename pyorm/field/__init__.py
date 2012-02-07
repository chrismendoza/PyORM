import datetime
import json
import numbers
import pickle
import cPickle
import time

from pyorm.exceptions import IntegerConversionError, DatabaseColumnTypeMismatchError
from pyorm.expression import Expression


class Field(object):
    declaration_index = 0

    def __init__(self, default=None, null=False, primary_key=False, autoincrement=False):
        self.default = default
        self.null = null
        self.primary_key = primary_key
        self.autoincrement = autoincrement
        self.declaration_index = Field.declaration_index
        Field.declaration_index += 1

    def to_python(self, value):
        return value

    def to_db(self, value):
        return value


class Integer(Field):
    field_type = 'INT'
    def __init__(self, length=None, unsigned=True, autoincrement=False, **kwargs):
        Field.__init__(self, **kwargs)
        self.unsigned = unsigned
        self.autoincrement = autoincrement
        self.length = length

    def to_python(self, value):
        try:
            return int(value)
        except:
            if issubclass(type(value), Expression) or value is None:
                return value
            else:
                raise IntegerConversionError(self.name, type(value))

    def to_db(self, value):
        try:
            return int(value)
        except:
            if issubclass(type(value), Expression) or value is None:
                return value
            else:
                raise IntegerConversionError(self.name, type(value))

class TinyInt(Integer):
    field_type = 'TINYINT'


class SmallInt(Integer):
    field_type = 'SMALLINT'


class MediumInt(Integer):
    field_type = 'MEDIUMINT'


class BigInt(Integer):
    field_type = 'BIGINT'


class UnixTimestamp(Integer):

    def to_python(self, value):
        if isinstance(value, numbers.Integral):
            return datetime.datetime.fromtimestamp(value)
        else:
            raise DatabaseColumnTypeMismatchError(self.name, int, type(value))

    def to_db(self, value):
        if isinstance(value, (datetime.date, datetime.datetime)):
            return int(time.mktime(value.timetuple()))
        elif isinstance(value, numbers.Integral):
            return value
        else:
            try:
                return int(value)
            except:
                if issubclass(type(value), Expression) or value is None:
                    return value
                else:
                    raise IntegerConversionError(self.name, type(value))


class Decimal(Field):
    field_type = 'DECIMAL'
    def __init__(self, precision=8, scale=2, unsigned=True, **kwargs):
        Field.__init__(self, **kwargs)
        self.precision = precision
        self.scale = scale
        self.unsigned = unsigned


class Double(Decimal):
    field_type = 'DOUBLE'


class Float(Decimal):
    field_type = 'FLOAT'
    pass


class Text(Field):
    field_type = 'TEXT'


class TinyText(Field):
    field_type = 'TINYTEXT'


class MediumText(Field):
    field_type = 'MEDIUMTEXT'


class LongText(Field):
    field_type = 'LONGTEXT'


class Char(Field):
    field_type = 'CHAR'
    def __init__(self, length=None, **kwargs):
        Field.__init__(self, **kwargs)
        self.length = length


class VarChar(Char):
    field_type = 'VARCHAR'


class Date(Field):
    field_type = 'DATE'
    def to_db(self, value):
        if value is None:
            return u'0000-00-00'
        return value


class Time(Field):
    field_type = 'TIME'
    def to_db(self, value):
        if value is None:
            return u'00:00:00'
        return value


class TimeStamp(Field):
    field_type = 'TIMESTAMP'
    def to_db(self, value):
        if value is None:
            return u'0000-00-00 00:00:00'
        return value


class DateTime(Field):
    field_type = 'DATETIME'
    def to_db(self, value):
        if value is None:
            return u'0000-00-00 00:00:00'
        return value


class Blob(Field):
    field_type = 'BLOB'


class TinyBlob(Field):
    field_type = 'TINYBLOB'


class MediumBlob(Field):
    field_type = 'MEDIUMBLOB'


class LongBlob(Field):
    field_type = 'LONGBLOB'


class VarBinary(Field):
    field_type = 'VARBINARY'


class Enum(Field):
    field_type = 'ENUM'

    def __init__(self, *values, **kwargs):
        Field.__init__(self, **kwargs)
        self.values = Expression(*values).operator(',')

    def tokenize(self):
        tokens = [(Token.Keyword, self.__class__.__name__)]
        tokens.extend(self.values.tokenize())
        return tokens


class Pickle(Text):
    def to_python(self, value):
        if value in ('', u'', None):
            return None
        elif isinstance(value, basestring):
            try:
                return pickle.loads(value.encode('latin1'))
            except ValueError:
                # maybe cPickle was used?
                return cPickle.loads(value.encode('latin1'))
        else:
            return value

    def to_db(self, value):
        if value in ('', u'', None):
            return u''
        return pickle.dumps(value)


class JSON(Text):
    def to_python(self, value):
        return json.loads(value)

    def to_db(self, value):
        return json.dumps(value)
