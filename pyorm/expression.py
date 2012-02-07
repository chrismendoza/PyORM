import copy

from pyorm.nodelist import NodeList
from pyorm.token import Token


class Expression(NodeList):
    """
        The Expression class, is used for storing expression values and operators and converting them to
        a string on a Expression.__str__() call.

        The default operator used for expressions is 'AND', so:
            Expression(value1, value2)

        Would output:
            '(value1 AND value2)'

        You can also set the operator for a given Expression using the .operator() method:
            Expression(value1, value2, value3).operator('ADD')

        Would output:
            '(value1 + value2 + value3)'

        The third function of the Expression class provides the ability to use operators directly on an
        Expression instance and another object (even another Expression):
            Expression(value1, value2).operator('ADD') * 3
            Expression(value1, value2).operator('ADD') * Expression(value3, value4).operator('SUB')

        Would output:
            '(value1 + value2) * 3'
            '(value1 + value2) * (value3 - value4)
    """

    def __init__(self, *args):
        """ Initialize the Expression object and its parent (NodeList) """
        NodeList.__init__(self, *args)
        self._operator = 'AND'
        self._alias = None
        self._base_model = None
        self._enclose = True
        self._force_enclose = False
        self._coupled_pair = False
        self._null_assign = False

    def __copy__(self):
        """
            Return a new version of this Expression object, we don't need to store the
            model that this object is attached to on the new object, since the base model
            is set when a query is run anyway.
        """
        new_copy = type(self)(*self._node_list)
        new_copy.operator(self._operator)
        new_copy.set_alias(self._alias)
        new_copy.enclose(self._enclose)
        new_copy._coupled_pair = self._coupled_pair
        return new_copy

    def __deepcopy__(self, memo):
        new_copy = type(self)(*copy.deepcopy(self._node_list))
        new_copy.operator(self._operator)
        new_copy.set_alias(self._alias)
        new_copy.enclose(self._enclose)
        new_copy._coupled_pair = self._coupled_pair
        return new_copy

    def __repr__(self):
        """ Define an informative representation of the Expression object """
        return str(['{0}({1})'.format(Token.gettype(token[0]), token[1]) for token in self.tokenize()])

    def __reversed__(self):
        self._node_list = list(reversed(self._node_list))
        return self

    def __str__(self):
        """
            Convert this Expression derived object into a string representation for use in database calls
        """
        def f(x):
            """
                Mapping method to automatically replace any non-Expression characters with '|pyorm_escape|' when we output the string
            """
            from pyorm.model import Model
            if issubclass(type(x), Expression):
                if x._base_model is None:
                    x.set_base_model(self._base_model)
                return x
            elif issubclass(type(x), Model):
                return x
            else:
                return u'|pyorm_escape|'

        if self._base_model is not None:
            return self._base_model._properties.connection().dialect.format_expression(self)
        else:
            retval = (u' {0} '.format(self._operator)).join(str(item) for item in map(f, self._node_list))
            if self._operator in ('AND', 'OR', 'ADD', 'SUB', 'DIV', 'MUL', 'MOD', 'POW'):
                retval = u'({0})'.format(retval)
            if self._alias is not None:
                retval = u'{0} ALIAS {1}'.format(retval, self._alias)
            return retval

    # Define algebraic associations
    def __and__(self, other):
        """
            If this expression object's modifier is 'AND', and we are dealing with two Expression objects,
            or two objects derived from the Expression class, which share this operator, merge the other
            expression values onto the end of the NodeList.

            If we are dealing with something other than an expression object, and this object's modifier is
            'AND', append the other object to the end of the NodeList

            If we are dealing with a different operator than is currently contained in this Expression derived
            object, return a new instance of this type of object, with the operator set to 'AND'.
        """
        if self._operator in ('AND'):
            if issubclass(type(other), Expression) and other._operator == self._operator:
                self.extend(other)
            else:
                self.append(other)
            return self
        else:
            return Expression(self, other)

    def __rand__(self, other):
        """
            If this expression object's modifier is 'AND', and we are dealing with two Expression objects,
            or two objects derived from the Expression class, which share this operator, merge the other
            expression values into the beginning of the NodeList.

            If we are dealing with something other than an expression object, and this object's modifier is
            'AND', append the other object to the front of the NodeList

            If we are dealing with a different operator than is currently contained in this Expression derived
            object, return a new instance of this type of object, with the operator set to 'AND'.
        """
        if self._operator in ('AND'):
            if issubclass(type(other), Expression) and other._operator == self._operator:
                self[:0] = other
            else:
                self.insert(0, other)
            return self
        else:
            return Expression(other, self)

    def __or__(self, other):
        """
            If this expression object's modifier is 'OR', and we are dealing with two Expression objects,
            or two objects derived from the Expression class, which share this operator, merge the other
            expression values onto the end of the NodeList.

            If we are dealing with something other than an expression object, and this object's modifier is
            'OR', append the other object to the end of the NodeList

            If we are dealing with a different operator than is currently contained in this Expression derived
            object, return a new instance of this type of object, with the operator set to 'OR'.
        """
        if self._operator == 'OR':
            if issubclass(type(other), Expression) and other._operator == self._operator:
                self.extend(other)
            else:
                self.append(other)
            return self
        else:
            return Expression(self, other).operator('OR')

    def __ror__(self, other):
        """
            If this expression object's modifier is 'OR', and we are dealing with two Expression objects,
            or two objects derived from the Expression class, which share this operator, merge the other
            expression values into the beginning of the NodeList.

            If we are dealing with something other than an expression object, and this object's modifier is
            'OR', append the other object to the front of the NodeList

            If we are dealing with a different operator than is currently contained in this Expression derived
            object, return a new instance of this type of object, with the operator set to 'OR'.
        """
        if self._operator == 'OR':
            if issubclass(type(other), Expression) and other._operator == self._operator:
                self[:0] = other
            else:
                self.insert(0, other)
            return self
        else:
            return Expression(other, self).operator('OR')

    def __add__(self, other):
        """
            If this expression object's modifier is 'ADD', and we are dealing with two Expression objects,
            or two objects derived from the Expression class, which share this operator, merge the other
            expression values onto the end of the NodeList.

            If we are dealing with something other than an expression object, and this object's modifier is
            'ADD', append the other object to the end of the NodeList

            If we are dealing with a different operator than is currently contained in this Expression derived
            object, return a new instance of this type of object, with the operator set to 'ADD'.
        """
        if self._operator == 'ADD':
            if issubclass(type(other), Expression) and other._operator == self._operator:
                self.extend(other)
            else:
                self.append(other)
            return self
        else:
            return Expression(self, other).operator('ADD')

    def __radd__(self, other):
        """
            If this expression object's modifier is 'ADD', and we are dealing with two Expression objects,
            or two objects derived from the Expression class, which share this operator, merge the other
            expression values into the beginning of the NodeList.

            If we are dealing with something other than an expression object, and this object's modifier is
            'ADD', append the other object to the front of the NodeList

            If we are dealing with a different operator than is currently contained in this Expression derived
            object, return a new instance of this type of object, with the operator set to 'ADD'.
        """
        if self._operator == 'ADD':
            if issubclass(type(other), Expression) and other._operator == self._operator:
                self[:0] = other
            else:
                self.insert(0, other)
            return self
        else:
            return Expression(other, self).operator('ADD')

    def __sub__(self, other):
        """
            If this expression object's modifier is 'SUB', and we are dealing with two Expression objects,
            or two objects derived from the Expression class, which share this operator, merge the other
            expression values onto the end of the NodeList.

            If we are dealing with something other than an expression object, and this object's modifier is
            'SUB', append the other object to the end of the NodeList

            If we are dealing with a different operator than is currently contained in this Expression derived
            object, return a new instance of this type of object, with the operator set to 'SUB'.
        """
        if self._operator == 'SUB':
            if issubclass(type(other), Expression) and other._operator == self._operator:
                self.extend(other)
            else:
                self.append(other)
            return self
        else:
            return Expression(self, other).operator('SUB')

    def __rsub__(self, other):
        """
            If this expression object's modifier is 'SUB', and we are dealing with two Expression objects,
            or two objects derived from the Expression class, which share this operator, merge the other
            expression values into the beginning of the NodeList.

            If we are dealing with something other than an expression object, and this object's modifier is
            'SUB', append the other object to the front of the NodeList

            If we are dealing with a different operator than is currently contained in this Expression derived
            object, return a new instance of this type of object, with the operator set to 'SUB'.
        """
        if self._operator == 'SUB':
            if issubclass(type(other), Expression) and other._operator == self._operator:
                self[:0] = other
            else:
                self.insert(0, other)
            return self
        else:
            return Expression(other, self).operator('SUB')

    def __mul__(self, other):
        """
            Because of order of operations issues no matter what the operator of this object, or the type of
            the other object, we always want to return a new instance of this type of object, with the 'MUL'
            operator assigned and this object and the object being multiplied as the entries in the NodeList.
        """
        return Expression(self, other).operator('MUL')

    def __rmul__(self, other):
        """
            Because of order of operations issues no matter what the operator of this object, or the type of
            the other object, we always want to return a new instance of this type of object, with the 'MUL'
            operator assigned and this object and the object being multiplied as the entries in the NodeList.

            Because this is a rmul, we return the object with the self and other values swapped.  With some
            operators this would not cause an issue either way, but for some, it does matter.
        """
        return Expression(other, self).operator('MUL')

    def __div__(self, other):
        """
            Because of order of operations issues no matter what the operator of this object, or the type of
            the other object, we always want to return a new instance of this type of object, with the 'DIV'
            operator assigned and this object and the object being divided as the entries in the NodeList.
        """
        return Expression(self, other).operator('DIV')

    def __rdiv__(self, other):
        """
            Because of order of operations issues no matter what the operator of this object, or the type of
            the other object, we always want to return a new instance of this type of object, with the 'DIV'
            operator assigned and this object and the object being divided as the entries in the NodeList.

            Because this is a rdiv, we return the object with the self and other values swapped.  With some
            operators this would not cause an issue either way, but for some, it does matter.
        """
        return Expression(other, self).operator('DIV')

    def __mod__(self, other):
        """
            Because of order of operations issues no matter what the operator of this object, or the type of
            the other object, we always want to return a new instance of this type of object, with the 'MOD'
            operator assigned and this object and the object being compared for the modulo computation as
            the entries in the NodeList.
        """
        return Expression(self, other).operator('MOD')

    def __rmod__(self, other):
        """
            Because of order of operations issues no matter what the operator of this object, or the type of
            the other object, we always want to return a new instance of this type of object, with the 'MOD'
            operator assigned and this object and the object being compared for the modulo computation as
            the entries in the NodeList.

            Because this is a rmod, we return the object with the self and other values swapped.  With some
            operators this would not cause an issue either way, but for some, it does matter.
        """
        return Expression(other, self).operator('MOD')

    def __pow__(self, other):
        """
            Because of order of operations issues no matter what the operator of this object, or the type of
            the other object, we always want to return a new instance of this type of object, with the 'POW'
            operator assigned and this object and the object being compared for the power computation as
            the entries in the NodeList.
        """
        return Expression(self, other).operator('POW')

    def __rpow__(self, other):
        """
            Because of order of operations issues no matter what the operator of this object, or the type of
            the other object, we always want to return a new instance of this type of object, with the 'POW'
            operator assigned and this object and the object being compared for the power computation as
            the entries in the NodeList.

            Because this is a rpow, we return the object with the self and other values swapped.  With some
            operators this would not cause an issue either way, but for some, it does matter.
        """
        return Expression(other, self).operator('POW')

    # Define comparison associations
    def __lt__(self, other):
        """
            Method to return a new instance of this type of object with a 'LT' (<) operator and the two
            values that are being used in this comparison.
        """
        return Expression(self, other).operator('LT')

    def __le__(self, other):
        """
            Method to return a new instance of this type of object with a 'LE' (<=) operator and the two
            values that are being used in this comparison.
        """
        return Expression(self, other).operator('LE')

    def __eq__(self, other):
        """
            Method to return a new instance of this type of object with a 'EQ' (==) operator and the two
            values that are being used in this comparison.
        """
        if other is None:
            return Expression(self, other).operator('NULLEQ')
        return Expression(self, other).operator('EQ')

    def __ne__(self, other):
        """
            Method to return a new instance of this type of object with a 'NE' (!=) operator and the two
            values that are being used in this comparison.
        """
        if other is None:
            return Expression(self, other).operator('NULLNE')
        return Expression(self, other).operator('NE')

    def __ge__(self, other):
        """
            Method to return a new instance of this type of object with a 'GE' (>=) operator and the two
            values that are being used in this comparison.
        """
        return Expression(self, other).operator('GE')

    def __gt__(self, other):
        """
            Method to return a new instance of this type of object with a 'GT' (>) operator and the two
            values that are being used in this comparison.
        """
        return Expression(self, other).operator('GT')

    def startswith(self, other):
        """
            Method to return a new instance of this type of object with a 'STARTSWITH' operator and the two
            values that are being used in this comparison.  For mysql this would be the equivilant of "self LIKE 'other%'".
        """
        return Expression(self, other).operator('STARTSWITH')

    def endswith(self, other):
        """
            Method to return a new instance of this type of object with a 'ENDSWITH' operator and the two
            values that are being used in this comparison.  For mysql this would be the equivilant of "self LIKE '%other'".
        """
        return Expression(self, other).operator('ENDSWITH')

    def contains(self, other):
        """
            Method to return a new instance of this type of object with a 'CONTAINS' operator and the two
            values that are being used in this comparison.  For mysql this would be the equivilant of "self LIKE '%other%'".
        """
        return Expression(self, other).operator('CONTAINS')

    def between(self, start, end):
        """
        """
        return Expression(self, Expression(start, end).operator('AND').enclose(False)).operator('BETWEEN')

    def operator(self, value):
        """
            Method to set the operator from outside this class, defaults to 'AND' for new objects.
        """
        self._operator = value
        return self

    def set_alias(self, alias):
        """
            Set the alias on an expression, this is really only used for additional fields in a query,
            all other field aliases are generated based on the models they are related to
        """
        if isinstance(alias, basestring) or alias is None:
            self._alias = alias
        else:
            raise TypeError(u'Expected type for alias is string, unicode or None, got {0}'.format(type(alias).__name__))
        return self

    def get_alias(self, alias):
        """
            Used to find an expression within a given alias, This only looks in the direct children of this expression.
            Upon locating a valid expression, will go ahead and return the given expression for later use, or False if
            the alias could not be located.

            This method is primarily used when the expression is used as a fieldset.
        """
        if isinstance(alias, basestring):
            for expression in filter(self.filter_expressions, self._node_list):
                if expression._alias == alias:
                    return expression
        else:
            raise TypeError(u'Expected type for alias is string, unicode or None, got {0}'.format(type(alias).__name__))
        return False

    def enclose(self, enclose):
        if type(enclose) is bool:
            self._enclose = enclose
        else:
            raise TypeError("Expected type 'bool', got '{0}'".format(type(enclose).__name__))
        return self

    def tokenize(self):
        from pyorm.column import Column
        from pyorm.model import Model
        from pyorm.model.thinmodel import ThinModel

        enclose = (self._operator in ('AND', 'OR', 'ADD', 'SUB', 'DIV', 'MUL', 'MOD') and self._enclose) or self._force_enclose

        tokens = []

        if enclose:
            tokens.append((Token.Operator, 'LPARENTHESIS'))

        node_end = len(self._node_list) - 1
        op = self._operator
        for index, token in enumerate(self._node_list):
            if index <= node_end and index is not 0:
                if op in ('NULLEQ','NULLNE') and self._null_assign:
                    op = op.replace('NULL', '')
                tokens.append((Token.Operator, op))

            if type(token) is Column:
                tokens.append((Token.Column, token))
            elif issubclass(type(token), Expression):
                tokens.extend(token.tokenize())
            elif issubclass(type(token), (ThinModel)):
                tokens.append((Token.Model, token))
            else:
                tokens.append((Token.Literal, token))

        if enclose:
            tokens.append((Token.Operator, 'RPARENTHESIS'))

        if self._alias is not None:
            tokens.append((Token.Alias, self._alias))

        return tokens

    def auto_eager_loads(self, parent_models=False):
        """
            Returns a list of models that should be eager loaded based
            on the columns referenced in the fields, filters, having, group, order.
        """
        from pyorm.column import Column
        models = {}

        if parent_models:
            models = parent_models

        for item in self._node_list:
            if issubclass(type(item), Column) and len(item._queue) > 1 and not item._scope:
                last_node = models
                for model in item._queue[:-1]:
                    if model not in last_node.keys():
                        last_node[model] = {}
                    last_node = last_node[model]
            elif issubclass(type(item), Expression):
                models = item.auto_eager_loads(models)
        return models

    def columns(self):
        from pyorm.column import Column
        columns = []
        for item in self._node_list:
            if issubclass(type(item), Column):
                columns.append(item)
            elif issubclass(type(item), Expression):
                columns.extend(item.columns())
        return columns

    def replace_column(self, column, replacement):
        from pyorm.column import Column
        for index, item in enumerate(self._node_list):
            if issubclass(type(item), Column):
                if column._queue == item._queue:
                    self._node_list[index] = copy.deepcopy(replacement)
            elif issubclass(type(item), Expression):
                item.replace_column(column, replacement)

        return self

    def filter_expressions(self, x):
        """
            filter any non-Expression based objects
        """
        return issubclass(type(x), Expression)

    def filter_models(self, x):
        """
            filter any non-Model based objects (so that we can pull escaped vars from them)
        """
        from pyorm.model import Model
        return issubclass(type(x), Model)

    def keys(self):
        return [exp._alias for exp in self._node_list if issubclass(type(exp), Expression)]
