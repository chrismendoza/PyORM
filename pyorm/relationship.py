import copy
import types

from pyorm.expression import Expression


class Relationship(object):
    declaration_index = 0

    _cache = {}

    @property
    def model(self):
        """
            Tries to retrieve, instantiate and return the model if possible
        """
        if getattr(self, '_model', False) is False:
            if Relationship._cache.get(self._import_path, None) is None:
                try:
                    # first try in the current namespace
                    self._module = __import__(__name__)
                    self._model = getattr(self._module, self._model_name)(
                        _model_name=self._name, _model_parent=self._parent)
                except AttributeError:
                    try:
                        # Try to import the appropriate module
                        self._module = __import__(
                            self._import_path, {}, {}, self._model_name)
                        if getattr(self._module, self._model_name) is types.ModuleType:
                            # if the model name returns a module, use that as the base module
                            self._module = getattr(
                                self._module, self._model_name)
                        # try and instantiate the model
                        Relationship._cache[self._import_path] = self._module
                        self._model = getattr(self._module, self._model_name)(_model_name=self._name, _model_parent=self._parent)
                    except ImportError:
                        raise Exception('Could not locate model `{0}`.'.format(
                            self._model_name))
                    except Exception as error:
                        # TODO: Custom exception type
                        raise Exception('Could not load model `{0}`, reason: {1}'.format(self._model_name, error))
            else:
                self._module = Relationship._cache[self._import_path]
                self._model = getattr(self._module, self._model_name)(
                    _model_name=self._name, _model_parent=self._parent)
        return self._model

    @property
    def conditions(self):
        """
            Returns the conditions as an expression.
        """
        if issubclass(type(self._conditions), Expression):
            return self._conditions
        else:
            return Expression(*self._conditions)

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, parent):
        self._parent = parent
        if self._model is not False:
            self._model._properties.parent = parent

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        self._name = name
        if self._model is not False:
            self._model._properties.name = name

    @property
    def attached_to(self):
        return getattr(self, '_attached_to', {})

    @attached_to.setter
    def attached_to(self, value):
        self._attached_to = value

    def __copy__(self):
        new_relationship = type(self)(self._import_path, self._model_name,
                                      conditions=self._conditions, join=self._join)
        new_relationship._model = self._model
        new_relationship._module = self._module

        return new_relationship

    def __deepcopy__(self, memo):
        new_relationship = type(self)(
            copy.deepcopy(self._import_path),
            copy.deepcopy(self._model_name),
            conditions=copy.deepcopy(self._conditions),
            join=copy.deepcopy(self._join)
        )
        new_relationship._model = copy.deepcopy(self._model)
        new_relationship._module = self._module

        return new_relationship

    def __init__(self, import_path, model_name, conditions=None, join='INNER'):
        """
            Initialize the relationship
        """
        self.declaration_index = Relationship.declaration_index
        Relationship.declaration_index += 1
        self._import_path = import_path
        self._model_name = model_name
        self._eager = False
        if conditions is not None:
            self._conditions = conditions
        else:
            self._conditions = []
        self._join = join
        self._model = False
        self._module = None
        self._name = None
        self._parent = None

    def reset(self, name, parent):
        """
            Reset the module, model, name and parent here, that way a new model is created when
            necessary, instead of keeping extra resources tied up for the remainder of the life
            of this particular relationship (especially important when deleting a parent record)
        """
        self._model = False
        self._module = None
        self._name = name
        self._parent = parent
        self._attached_to = {}


class OneToOne(Relationship):
    pass


class OneToMany(Relationship):
    pass


class ManyToOne(Relationship):
    pass


class ManyToMany(Relationship):
    pass


class ThinRelationship(Relationship):
    pass
