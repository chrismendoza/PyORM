import weakref, copy

from pyorm.token import *
from pyorm.expression import Expression, Equation


class Column(object):
    """
        The Column class, used to reference fields on the given model
        columns can be referenced in the following ways:

            field on the primary model:
                Column.field

            field on a relation of the primary model:
                Column.relation.field

            field on a relation through another relation off the primary model:
                Column.relation1.relation2.field

        When comparisons and operations are done against a column, they return Expressions/Equations.

            for example:
                Column.field == 3

            Would be the same as saying:
                Equation(Column.field, 3, op=OP_EQ)

            while:
                (Column.field * 4) == Column.field2

            would be the equivilant of:
                Expression(
                    Expression(Column.field, 4, op=OP_MUL),
                    Column.field2, op=OP_EQ)
    """

    __slots__ = ('_path', 'token_type', '_alias', '_owner', '_owner_ref', '_scope')

    class __metaclass__(type):
        def __getattr__(cls, attr):
            """
                When a user tries to access a non-existent attribute off the Column
                class, a new Column is created, and the attribute name added to the stack.
            """
            return Column(path=[attr], scope=False)

    token_type = T_COL

    @property
    def owner(self):
        return getattr(self, '_owner', None)

    @owner.setter
    def owner(self, value):
        if value is not None:
            self._owner = weakref.proxy(value)
            self._owner_ref = weakref.ref(value)

    def __init__(self, path=None, scope=False):
        if type(path) in (tuple, list):
            self._path = list(path)
        else:
            self._path = []

        self._alias = None
        self._scope = scope

    def __copy__(self):
        instance = self.__class__(self._path[:], scope=self.scope)
        instance._owner = self._owner
        instance._alias = self._alias

        return instance

    def __deepcopy__(self):
        instance = self.__copy__()
        memo[id(self)] = instance
        return instance

    def __getattr__(self, attr):
        """
            add the requested path to the stack, then return this column
            object.  The dot syntax is a bit slower, but the ease of use
            seems worth it.
        """
        self._path.append(attr)
        return self

    def __and__(self, other):
        return Expression(self, other, op=OP_AND)

    def __rand__(self, other):
        return Expression(other, self, op=OP_AND)

    def __or__(self, other):
        return Expression(self, other, op=OP_OR)

    def __ror__(self, other):
        return Expression(other, self, op=OP_OR)

    def __add__(self, other):
        return Expression(self, other, op=OP_ADD)

    def __radd__(self, other):
        return Expression(other, self, op=OP_ADD)

    def __sub__(self, other):
        return Expression(self, other, op=OP_SUB)

    def __rsub__(self, other):
        return Expression(other, self, op=OP_SUB)

    def __mul__(self, other):
        return Expression(self, other, op=OP_MUL)

    def __rmul__(self, other):
        return Expression(other, self, op=OP_MUL)

    def __div__(self, other):
        return Expression(self, other, op=OP_DIV)

    def __rdiv__(self, other):
        return Expression(other, self, op=OP_DIV)

    def __mod__(self, other):
        return Expression(self, other, op=OP_MOD)

    def __rmod__(self, other):
        return Expression(other, self, op=OP_MOD)

    def __pow__(self, other):
        return Expression(self, other, op=OP_POW)

    def __rpow__(self, other):
        return Expression(other, self, op=OP_POW)

    def __ne__(self, other):
        if other is None:
            return Expression(self, other, op=OP_NULLNE)
        elif getattr(other, 'token_type', None) is None:
            return Equation(self, other, op=OP_NE)

        return Expression(self, other, op=OP_NE)

    def __lt__(self, other):
        if getattr(other, 'token_type', None) is None:
            return Equation(self, other, op=OP_LT)

        return Expression(self, other, op=OP_LT)

    def __le__(self, other):
        if getattr(other, 'token_type', None) is None:
            return Equation(self, other, op=OP_LE)

        return Expression(self, other, op=OP_LE)

    def __eq__(self, other):
        if other is None:
            return Equation(self, other, op=OP_NULLEQ)
        elif getattr(other, 'token_type', None) is None:
            return Equation(self, other, op=OP_EQ)

        return Expression(self, other, op=OP_EQ)

    def __ge__(self, other):
        if getattr(other, 'token_type', None) is None:
            return Equation(self, other, op=OP_GE)

        return Expression(self, other, op=OP_GE)

    def __gt__(self, other):
        if getattr(other, 'token_type', None) is None:
            return Equation(self, other, op=OP_GT)

        return Expression(self, other, op=OP_GT)

    def __hash__(self):
        return hash(tuple(self._path + [self._alias, self._scope, self._owner_ref()]))

    def set_alias(self, alias):
        self._alias = alias

    def get_alias(self):
        return self._alias

    def set_scope(self, scope):
        self._scope = scope

    def get_scope(self):
        return self._scope
