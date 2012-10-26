import collections, weakref, copy


#Token types
T_LIT = 0
T_COL = 1
T_OPR = 2
T_KWD = 3
T_HLP = 4
T_MOD = 5
T_EXP = 6
T_EQU = 7

# Operator types
OP_ADD = 0
OP_SUB = 1
OP_MUL = 2
OP_DIV = 3
OP_MOD = 4
OP_POW = 5

OP_AND = 6
OP_OR  = 7

OP_NE  = 8
OP_LT  = 9
OP_LE  = 10
OP_EQ  = 11
OP_GE  = 12
OP_GT  = 13

OP_NULLNE = 14
OP_NULLEQ = 15

OP_SW  = 16
OP_EW  = 17
OP_CT  = 18
OP_BT  = 19

OP_OPAR = 20
OP_CPAR = 21


Token = collections.namedtuple('Token', ('type', 'value'))


def calc_tokens(expr1, expr2, op, right=False):
    """
        This function is used to condense the repeated code from the OP_ADD, OP_SUB, OP_OR,
        and OP_AND expression types, since it's the same code for each of these operations.

        This function combines the values from two expressions when they share the same operator
        type.  If the two expressions do not share the same operator type a new expression is
        returned with expression1 & expression2 as the componenets of the new expression.
    """
    if right:
        # This is used for operations coming from the right (__rand__, __radd__, etc.)
        if expr1.op == op:
            expr1._tokens[:0] = [
                Token(getattr(expr2, 'token_type', T_LIT), expr2), Token(T_OPR, op)]
            return expr1
        else:
            return Expression(expr2, expr1, op=op)
    else:
        if expr1.op == op:
            if getattr(expr2, 'token_type', None) == T_EXP and expr1.op == expr2.op:
                if len(expr1._tokens) and len(expr2._tokens):
                    expr1._tokens.extend([Token(T_OPR, op)] + expr2._tokens)
                elif len(expr2._tokens):
                    expr1._tokens.extend(expr2._tokens)
            else:
                if len(expr1._tokens):
                    expr1._tokens.extend([
                        Token(T_OPR, op), Token(getattr(expr2, 'token_type', T_LIT), expr2)])
                else:
                    expr1._tokens.append(Token(getattr(expr2, 'token_type', T_LIT), expr2))

            return expr1
        else:
            return Expression(expr1, expr2, op=op)


class Expression(object):
    """
        The Expression class, is used for storing expression values and operators and converting
        them to a set of tokens for both the connection dialect to turn into a sql statement, as
        well as a hashable set of values, so that any sql generated can be cached for later use.

        The default operator used for expressions is 'AND', so:
            Expression(value1, value2)

        Would output:
            '(value1 AND value2)'

        You can also set the operator for a given Expression using the `op` keyword param:
            Expression(value1, value2, value3, op=OP_ADD)

        Would output:
            '(value1 + value2 + value3)'

        The third function of the Expression class provides the ability to use operators directly on an
        Expression instance and another object (even another Expression):
            Expression(value1, value2, op=OP_ADD) * 3
            Expression(value1, value2, op=OP_ADD) * Expression(value3, value4, op=OP_SUB)

        Would output:
            '(value1 + value2) * 3'
            '(value1 + value2) * (value3 - value4)
        Stores an expression in the form of a list of tokens, which are converted
        to SQL by the database dialect.  The tokens are also used when looking up
        pre-generated sql from the cache.
    """
    __slots__ = ('op', '_tokens', 'token_type', 'alias', '_owner')

    # If a user ever wants to create a different implementation of
    # the expression class, all they need to do is include this token_type
    # declaration, and the ORM will treat it as such.
    token_type = T_EXP

    @property
    def literals(self):
        literals = []
        for token in self._tokens:
            if token.type == T_LIT:
                literals.append(token.value)
            elif token.type in (T_EXP, T_HLP, T_MOD, T_EQU):
                literals.extend(token.value.literals)

        return literals

    @property
    def tokens(self):
        tokens = []
        for token in self._tokens:
            if token.type in (T_EXP, T_HLP, T_MOD, T_EQU):
                tokens.extend(token.value.tokens)
            else:
                tokens.append(token)

        #if self.op in (OP_MUL, OP_DIV, OP_MOD, OP_POW, OP_ADD, OP_SUB, OP_OR, OP_AND):
        tokens.insert(0, Token(T_OPR, OP_OPAR))
        tokens.append(Token(T_OPR, OP_CPAR))

        return tokens

    @property
    def owner(self):
        return getattr(self, '_owner', None)

    @owner.setter
    def owner(self, value):
        if value is not None:
            self._owner = weakref.proxy(value)

        for token in self._tokens:
            if token.type in (T_EXP, T_HLP, T_MOD, T_EQU):
                token.value.owner = value

    def __init__(self, *args, **kwargs):
        self.op = kwargs.get('op', OP_AND)
        self._tokens = []
        self.alias = kwargs.get('alias', None)

        # if arguments were passed, we need to load & tokenize them here
        # adding an operator token between each arg as we go
        if len(args):
            max_idx = len(args) - 1

            for idx, arg in enumerate(args):
                if hasattr(arg, 'token_type'):
                    self._tokens.append(Token(arg.token_type, arg))
                else:
                    self._tokens.append(Token(T_LIT, arg))

                if idx != max_idx:
                    self._tokens.append(Token(T_OPR, self.op))

    def __copy__(self):
        instance = self.__class__(op=self.op)
        instance._tokens = self._tokens[:]
        return instance

    def __deepcopy__(self, memo):
        instance = self.__class__(op=self.op)
        memo[id(self)] = instance
        instance._tokens = copy.deepcopy(self._tokens)

        # Alias should always be a string/unicode object, so we shouldn't need to deep copy it.
        instance.alias = self.alias
        instance._owner = self._owner

        return instance

    def __and__(self, other):
        return calc_tokens(self, other, op=OP_AND)

    def __rand__(self, other):
        return calc_tokens(self, other, op=OP_AND, right=True)

    def __or__(self, other):
        return calc_tokens(self, other, op=OP_OR)

    def __ror__(self, other):
        return calc_tokens(self, other, op=OP_OR, right=True)

    def __add__(self, other):
        return calc_tokens(self, other, op=OP_ADD)

    def __radd__(self, other):
        return calc_tokens(self, other, op=OP_ADD, right=True)

    def __sub__(self, other):
        return calc_tokens(self, other, op=OP_SUB)

    def __rsub__(self, other):
        return calc_tokens(self, other, op=OP_SUB, right=True)

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

        return Expression(self, other, op=OP_NE)

    def __lt__(self, other):
        return Expression(self, other, op=OP_LT)

    def __le__(self, other):
        return Expression(self, other, op=OP_LE)

    def __eq__(self, other):
        if other is None:
            return Expression(self, other, op=OP_NULLEQ)

        return Expression(self, other, op=OP_EQ)

    def __ge__(self, other):
        return Expression(self, other, op=OP_GE)

    def __gt__(self, other):
        return Expression(self, other, op=OP_GT)

    def __hash__(self):
        return hash((self.alias, tuple([
            'literal' if token.type == T_LIT else token for token in self.tokens])))


class Equation(Expression):
    """
        Equation objects are very similar to Expression objects, with the only difference
        being that Equation objects are only equations between a Column and a literal value.

        These interactions are separated out so that the literal may be converted using the
        column's to_db() method.

        A model assignment is needed in order to ensure that the actual field is available
        and the Field.to_db() method is accessable. if the Field.to_db() method is unavailable,
        the raw literal is returned.
    """
    token_type = T_EQU

    @property
    def literals(self):
        literal = super(Equation, self).literals[0]

        if self.owner is not None:
            column = self._tokens[0].value
            model = self.owner
            field = None

            try:
                if len(column.path) > 1:
                    for step in column.path[:-1]:
                        model = getattr(model.relationships, step).model

                field = getattr(model, column.path[-1])

                if type(literal) in (tuple, set, frozenset, list):
                    literal = [field.cls.to_db(i) for i in literal]
                else:
                    literal = field.cls.to_db(literal)

            except AttributeError:
                # We couldn't find the to_db method or the field at all. In these cases, just
                # return the raw value. NOTE: I may want to re-think this and actually throw
                # an error if the relationship or column referenced could not be found in the
                # list of defined relationships (especially now that relationships can be added
                # on an as needed basis).
                pass

        return [literal]


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

    __slots__ = ('_path', 'token_type', '_alias', '_owner', '_scope')

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

    @owner.getter
    def owner(self, value):
        if value is not None:
            self._owner = weakref.proxy(value)

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
        instance = self.__class__()
        memo[id(self)] = instance

        instance._path = copy.deepcopy(self._path)
        instance._scope = self._scope
        instance._alias = self._alias
        instance._owner = self._owner

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
        return hash(tuple(self._path + [self._alias, self._scope]))

    def set_alias(self, alias):
        self._alias = alias

    def get_alias(self):
        return self._alias

    def set_scope(self, scope):
        self._scope = scope

    def get_scope(self):
        return self._scope
