import copy

from pyorm.model.prop import Prop
from pyorm.field import Field


class ThinModel(object):
    def __init__(self, *args, **kwargs):
        self._properties = Prop(self)
        self._properties.name = kwargs.get(u'_model_name', False)
        self._properties.parent = kwargs.get(u'_model_parent', False)
        self.reset()

    def __getattr__(self, name):
        if name in self._values.keys():
            return copy.deepcopy(self._values[name])
        elif name is 'Meta':
            class Meta(object):
                table = ''

            self.Meta = Meta()
            self.Meta.table = self._properties.name
            return self.Meta
        elif name is 'Fields':

            class Fields(object):
                def __init__(self):
                    class ThinFieldList(object):
                        def __contains__(self, name):
                            return True

                    self._field_list = ThinFieldList()

                def __getattr__(self, name):
                    return Field()

            self.Fields = Fields()
            return self.Fields
        else:
            raise AttributeError

    def __reversed__(self):
        """
            Allow for the use of reversed(Model)
        """
        if self._recordset:
            for index in reversed([i[0] for i in enumerate(self._recordset)]):
                self._parse_record(index)
                yield self
        else:
            raise StopIteration

    def __iter__(self):
        """
            Iterate over a set of rows from the database
        """
        if self._recordset:
            for index, value in enumerate(self._recordset):
                self._parse_record(index)
                yield self
        else:
            raise StopIteration

    def __eq__(self, other):
        try:
            if len(set(self._unique_columns()) ^ set(other._unique_columns())) or len(self._unique_columns()) == 0:
                return False
            else:
                uniques = self._unique_columns()
                for key in uniques:
                    if self._old_values[key] != other._old_values[key]:
                        return False
        except:
            return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def _unique_columns(self):
        return []

    def _parse_record(self, index):
        """
            Parses the record that matches the passed index and sets the values
            onto the _values and _old_values dicts so they can be used later.

            This also passes any values that pertain to related models on to that
            model as a recordset, then calling that related model's _parse_record()
            method, allowing the items to be passed on down the chain further if
            necessary.
        """
        if self._recordset:
            self._recordindex = index
            self._values = {}
            self._old_values = {}

            model_chain = '.'.join(self._properties.column_chain)
            for key in set(self._lookup_fields):
                try:
                    val = self._recordset[index].get('{0}.{1}'.format(
                        model_chain, key), self._recordset[index].get(key))
                    self._values[key] = val
                    self._old_values[key] = val
                except:
                    pass

    def reset(self):
        self._recordset = None
        self._recordindex = None
        self._values = {}
        self._old_values = {}
        self._lookup_fields = []

    def as_dict(self):
        """
            Returns the model represented as a dict
        """
        return dict(self._values)

    def as_list_of_dicts(self):
        """
            Returns the entire result set of the base model as a list of dicts.
        """
        return [row.as_dict() for row in self]
