class Prop(object):
    @property
    def name(self):
        """ Get the name of the model """
        return getattr(self, '_name', self.model.__class__.__name__)

    @name.setter
    def name(self, name):
        """ Allows setting an arbitrary model name on a model, handy for relationships, where the model has an alias """
        if name:
            if isinstance(name, basestring):
                self._name = name
            else:
                raise TypeError(u'Expected a string or unicode when setting model name, got type: {0}.'.format(type(name).__name__))
        else:
            self._name = self.model.__class__.__name__

        self._tree = None
        self._column_chain = None

    @name.deleter
    def name(self):
        """ Resets the name of the model """
        self._name = self.model.__class__.__name__

    @property
    def parent(self):
        """ Return the parent model """
        return getattr(self, '_parent', None)

    @parent.setter
    def parent(self, model):
        """ Sets the parent of this model, used in the case that the model is the child (related model) of another model """
        # this must be imported here to avoid issues with circular imports
        from pyorm.model import Model

        if issubclass(type(model), Model):
            self._parent = model
        elif model is None or model is False:
            self._parent = None
        else:
            raise TypeError(u'Expected a model, got type: {0}.'.format(type(model).__name__))

        self._tree = None
        self._column_chain = None

    @parent.deleter
    def parent(self):
        """ Resets the parent model and the model tree if the parent has changed """
        self._parent = None
        self._tree = None
        self._column_chain = None

    @property
    def tree(self):
        """
            Returns a list of tuples in [(model_name, table_name, model_object), (model_name, table_name, model_object)] form.

            To prevent unnecessary recursion, parent.setter and parent.deleter reset self._tree to None so that the tree will
            be rebuilt when accessed.  This allows us to still return the tree on demand, but not bother with it until it is
            actually asked for, and also not regenerate the tree each time it is requested.
        """
        if getattr(self, '_tree', None) is None:
            self._tree = []

            if self.parent is not None and not self.subquery:
                self._tree.extend(self.parent._properties.tree)

            self._tree.append((self.name, self.model.Meta.table, self.model))

        return self._tree

    @property
    def column_chain(self):
        """
            Returns the model name chain for use with columns in this model's expressions
        """
        if self._column_chain is None:
            self._column_chain = [model[0] for model in self.tree]

        return self._column_chain

    @property
    def subquery(self):
        """ If the _subquery variable exists, return its value, or return 'False' """
        if len(self.tree) > 1:
            return self.tree[0][2]._properties.subquery
        else:
            return getattr(self, '_subquery', False)

    @subquery.setter
    def subquery(self, boolean):
        """ Set the subquery property to a boolean value """
        if type(boolean) is bool:
            self._subquery = boolean
        else:
            raise TypeError

    @subquery.deleter
    def subquery(self):
        """ Resets the subquery status of the model """
        self._subquery = False

    @property
    def subquery_parent(self):
        """ If the _subquery variable exists, return its value, or return 'False' """
        return getattr(self, '_subquery_parent', False)

    @subquery_parent.setter
    def subquery_parent(self, model):
        """ Set the subquery_parent property to a Model """
        from pyorm.model import Model

        if issubclass(type(model), Model):
            self._subquery_parent = model
        elif model is None or model is False:
            self._subquery_parent = None
        else:
            raise TypeError(u'Expected a model, got type: {0}.'.format(type(model).__name__))

    @subquery_parent.deleter
    def subquery_parent(self):
        """ Resets the subquery status of the model """
        self._subquery_parent = False

    def connection(self, mode=None):
        """ Returns a connection of the type stored in mode """
        if mode:
            self.mode = mode
        if getattr(self.model.Meta, '{0}_server'.format(self.mode), False):
            conn = getattr(self.model._connection, getattr(self.model.Meta, '{0}_server'.format(self.mode)))
        else:
            conn = getattr(self.model._connection, getattr(self.model._connection._config, 'default_{0}_server'.format(self.mode)))
        return conn

    @property
    def mode(self):
        if len(self.tree) == 1:
            return getattr(self, '_mode', 'read')
        else:
            return self.tree[0][2]._properties.mode

    @mode.setter
    def mode(self, mode):
        if len(self.tree) == 1:
            self._mode = mode
        else:
            self.tree[0][2]._properties.mode = mode

    @mode.deleter
    def mode(self, mode):
        if len(self.tree) == 1:
            self._mode = 'read'
        else:
            self.tree[0][2]._properties.mode = 'read'

    @property
    def escaped_values(self):
        return getattr(self, '_escaped_values', [])

    @escaped_values.setter
    def escaped_values(self, values):
        self._escaped_values = values

    @escaped_values.deleter
    def escaped_values(self):
        self._escaped_values = []

    @property
    def include_regular_fields(self):
        return getattr(self, '_include_regular_fields', False)

    @include_regular_fields.setter
    def include_regular_fields(self, value):
        self._include_regular_fields = value

    def __init__(self, model):
        """ initialize the model properties """
        self.model = model
        self.wrap = True

