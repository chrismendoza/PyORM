from pyorm.exceptions import UnionArgumentTypeError, UnionColumnTypeError, UnionColumnDefinitionError
from pyorm.connection.exceptions import TableMissingError, ColumnMissingError
from pyorm.expression import Expression
from pyorm.model.thinmodel import ThinModel
from pyorm.token import Token
import pyorm.model

class Helper(Expression):
    def __init__(self, *args, **kwargs):
        Expression.__init__(self, *args)
        self.operator(u',')
        self.keywords = kwargs
        self._force_enclose = True

    def tokenize(self):
        tokens = [(Token.Keyword, self.__class__.__name__)]
        tokens.extend(Expression.tokenize(self))
        return tokens

class Values(Helper):
    def __init__(self, *args):
        Helper.__init__(self, *args)
        self._force_enclose = False

    def set_columns(self, *args):
        self._columns = Expression(*args).operator(',')
        self._columns._force_enclose = True

    def tokenize(self):
        tokens = []
        tokens.extend(self._columns.tokenize())
        tokens.extend(Helper.tokenize(self))
        return tokens

class Union(ThinModel):
    def __init__(self, *args):
        ThinModel.__init__(self, *args)
        self.fields = False
        self.models = []
        self.connection = None
        self._order = Expression().operator(',')

        for model in args:
            if issubclass(type(model), pyorm.model.Model):
                self.addModel(model)
            else:
                raise UnionArgumentTypeError

    def __reversed__(self, *args):
        if self._recordset is None:
            self.get()

        return ThinModel.__reversed__(self)

    def __len__(self):
        if self._recordset is None:
            self.get()

        return len(self._recordset)

    def __iter__(self, *args):
        if self._recordset is None:
            self.get()

        return ThinModel.__iter__(self)

    def _query(self, conn, sql, values=[]):
        """
            Send the query to the provided connection, if we get a missing table error, try and create it.
        """
        result = False
        try:
            result = conn.query(sql, values)
            self._debug_object = result.get('debug_object', False)
        except TableMissingError as obj:
            # if the write connection has auto_create_tables set to true
            # create the table, and return no result (since we just created it)
            for table in obj._tables:
                self._create_table(table)
            result = self._query(conn, sql, values)
        except ColumnMissingError:
            pass

        return result

    def addModel(self, model):
        if len(model._standard_fields):
            raise UnionColumnTypeError

        if self.fields is False:
            self.fields = set(model._additional_fields.keys())
            self._lookup_fields = model._lookup_fields

        elif len(self.fields - set(model._additional_fields.keys())):
            raise UnionColumnDefinitionError

        model._add_unique_fields = False
        self.models.append(model)


    def tokenize(self):
        tokens = []

        length = len(self.models)

        for index, model in enumerate(self.models):
            model._properties.subquery = self._properties.subquery
            model._properties.subquery_parent = self._properties.subquery_parent
            model._properties.wrap = False

            tokens.append((Token.Model, model))
            if (length - 1) != index:
                tokens.append((Token.Keyword, self.__class__.__name__))

        if len(self._order):
            tokens.append((Token.Keyword, 'ORDER'))
            tokens.extend(self._order.tokenize())

        return tokens

    def get(self, run_query=True):
        if self.connection is None:
            self.connection = self.models[0]._properties.connection('read')

        if run_query:
            result = self._query(self.connection, *self.connection.dialect.translate(self.tokenize()))
            self._recordset = result['result_set']
            self._parse_record(0)
            return self
        else:
            query, values = self.connection.dialect.translate(self.tokenize())
            self._properties.escaped_values = values
            return query

    def order(self, *args):
        """ Add order by instructions, takes Column or Expression objects """
        self._order.extend(args)
        return self

class Distinct(Helper):
    def __init__(self, *args):
        Helper.__init__(self, *args)
        self._force_enclose = False

class Descending(Helper):
    def __init__(self, *args):
        Helper.__init__(self, *args)
        self._force_enclose = False

    def tokenize(self):
        tokens = Expression.tokenize(self)
        tokens.append((Token.Keyword, self.__class__.__name__))
        return tokens

class Ascending(Helper):
    def __init__(self, *args):
        Helper.__init__(self, *args)
        self._force_enclose = False

    def tokenize(self):
        tokens = Expression.tokenize(self)
        tokens.append((Token.Keyword, self.__class__.__name__))
        return tokens

class Bitwise(Helper):
    def tokenize(self):
        tokens = []
        tokens.extend(Expression.tokenize(self))

        for index, token in enumerate(tokens):
            if token[0] is Token.Operator:
                if token[1] in ('AND', 'OR'):
                    tokens[index] = (Token.Operator, 'BITWISE_{0}'.format(token[1]))

        return tokens

class GroupConcat(Helper):
    def __init__(self, *args, **kwargs):
        Helper.__init__(self, *args, **kwargs)
        if kwargs.get('order', False):
            if type(kwargs['order']) in (list, tuple):
                self.keywords['order'] = Expression(*kwargs['order']).operator(',')
            else:
                self.keywords['order'] = Expression(kwargs['order']).operator(',')
        self.keywords['separator'] = kwargs.get('separator', ',')

    def tokenize(self):
        tokens = Helper.tokenize(self)
        for i, token in enumerate(reversed(tokens)):
            if token[0] is Token.Operator:
                index = (i + 1) * -1;
                break;
        end_op = tokens[index:]
        tokens = tokens[:index]
        if self.keywords.get('order', False):
            tokens.append((Token.Keyword, 'ORDER'))
            tokens.extend(self.keywords['order'].tokenize())

        tokens.extend([(Token.Keyword, 'SEPARATOR'), (Token.Literal, self.keywords['separator'])])
        tokens.extend(end_op)

        return tokens

class Match(Helper):
    def __init__(self, *args, **kwargs):
        Helper.__init__(self, *args, **kwargs)
        self.match = Expression(kwargs.get('against', ''))
        self.keywords['boolean_mode'] = kwargs.get('boolean_mode', False)
        self.keywords['natural_language'] = kwargs.get('natural_language', False)
        self.keywords['query_expand'] = kwargs.get('query_expand', False)

    def tokenize(self):
        tokens = Helper.tokenize(self)
        tokens.append((Token.Keyword, 'AGAINST'))
        tokens.extend(self.match.tokenize())

        if self.keywords['boolean_mode']:
            tokens.insert(-1, (Token.Keyword, 'BOOLEANMODE'))
        elif self.keywords['natural_language']:
            tokens.insert(-1, (Token.Keyword, 'NATURALLANG'))
        if self.keywords['query_expand']:
            tokens.insert(-1, (Token.Keyword, 'QUERYEXPAND'))

        return tokens

class Count(Helper):
    pass

class Sum(Helper):
    pass

class Average(Helper):
    pass

class Minimum(Helper):
    pass

class Maximum(Helper):
    pass

class Concat(Helper):
    pass

class Replace(Helper):
    pass

class If(Helper):
    pass

class Coalesce(Helper):
    pass

class IfNull(Helper):
    pass

class NullIf(Helper):
    pass

class Unix_Timestamp(Helper):
    pass

class From_Unixtime(Helper):
    pass

class Now(Helper):
    pass

class CurrentTimestamp(Helper):
    pass

class Rand(Helper):
    pass
