import copy

from pyorm.expression import Expression


class Column(Expression):
    """
        The Column class, used to reference fields on the given model
        columns can be referenced in the following ways:

            field on the primary model:
                Column.field

            field on a relation of the primary model:
                Column.relation.field

            field on a relation through another relation off the primary model:
                Column.relation1.relation2.field

        Columns are derived from expressions, and as such, they are capable
        of being used in expressions and creating expressions when comparisons are
        done against them.

            for example:
                Column.field == 3
                (Column.field * 4) == Column.field2
            would be the equivilant of (respectively):
                Expression(Column.field, 3).operator('EQ')
                Expression(Expression(Column.field, 4)
                           .operator('MUL'), Column.field2).operator('EQ')

        for other expression examples
    """
    class __metaclass__(type):
        """ if the user tries to access an attribute of the Column class directly, add it to the stack """
        def __getattr__(cls, attr):
            return Column(queue=False, attr=attr, scope=False)

    def __copy__(self):
        """
            Return a new version of this Column object, we don't need to store the
            model that this object is attached to on the new object, since the base model
            is set when a query is run anyway.
        """
        new_copy = Column(self._queue[:-1], self._queue[-1])
        new_copy._scope = self._scope
        return new_copy

    def __deepcopy__(self, memo):
        """
            Since Column objects store no other types of objects, and instead
            return an expression, there is no need to return anything additional
            for deepcopy.
        """
        return self.__copy__()

    def __init__(self, queue=False, attr='', scope=False):
        """ Initialize the column object """
        Expression.__init__(self)
        self._operator = 'column'
        self._queue = []

        if queue:
            self._queue.extend(queue)
        if attr:
            self._queue.append(attr)
        if scope == 'parent':
            self._scope = True
        else:
            self._scope = False

    def __getattr__(self, attr):
        """ user tried to get a new attribute add it to the stack and return the object """
        self._queue.append(attr)
        return self

    def __str__(self):
        """ return the string representation of this column """
        if self._base_model is not None and self._base_model._properties.connection().dialect:
            self._base_model.eager_load(self._queue[:-1])
            return self._base_model._properties.connection().dialect.format_column(self)
        return u'.'.join(self._queue)

    def __repr__(self):
        return u"<type '{0}' alias: {1} column: {2}>".format(
            type(self),
            self._alias,
            u'.'.join(self._queue)
        )

    def __coupled_pair(func):
        """
            Tests a given function to see if we are comparing the current
            object to an expression or model object, if not, we need to parse
            the value using the associated fields Field.to_python() and
            Field.to_database() methods, where appropriate.
        """
        def wrapper(self, other):
            expression = func(self, other)

            from pyorm.model import Model
            if not issubclass(type(other), Expression) and not issubclass(type(other), Model):
                expression._coupled_pair = True

            return expression
        return wrapper

    @__coupled_pair
    def __eq__(self, other):
        return Expression.__eq__(self, other)

    @__coupled_pair
    def __ne__(self, other):
        return Expression.__ne__(self, other)

    @__coupled_pair
    def __lt__(self, other):
        return Expression.__lt__(self, other)

    @__coupled_pair
    def __gt__(self, other):
        return Expression.__gt__(self, other)

    @__coupled_pair
    def __le__(self, other):
        return Expression.__le__(self, other)

    @__coupled_pair
    def __ge__(self, other):
        return Expression.__ge__(self, other)
