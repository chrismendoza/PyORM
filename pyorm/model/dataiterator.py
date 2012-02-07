import copy

class DataIterator(object):
    """
        DataIterator

        Allows access to a given list of dicts or dict-like objects as attributes.
        The attributes are determined by what is set in the _lookup_fields property,
        or failing that, what is returned from keys() off the first object in the list.

        Assigning a unique key or set of unique keys will cause the iterator to only
        show records where those keys are not the same as the previous index values.

        Assigning a stop iteration key or set of keys stops iteration over the recordset
        at the point where that key or set of keys are found to be different.
    """

    @property
    def _recordset(self):
        """
            Return the current dataset
        """
        return getattr(self, '_dataset', {})

    @_recordset.setter
    def _recordset(self, data):
        """
            Store a new dataset, resetting the record index
        """
        self._dataset = data
        self._recordindex = None

    @property
    def _recordindex(self):
        """
            Return the current record index
        """
        if getattr(self, '_starting_record_index', None) is None:
            self._starting_record_index = 0
            self._current_record_index = 0

        return self._current_record_index

    @_recordindex.setter
    def _recordindex(self, value):
        if getattr(self, '_starting_record_index', None) is None:
            self._starting_record_index = value

        self._current_record_index = value

    @property
    def _lookup_fields(self):
        """
            Return the fields that need to be added as attributes to this object.
            If no fields have been specified, will use all current fields in the
            dataset.
        """
        if len(self._datafields) == 0 and self._dataset is not None:
            self._datafields = dict([(key, key) for key in self._dataset[0].keys()])
        return self._datafields

    @_lookup_fields.setter
    def _lookup_fields(self, value):
        """
            Sets the value of the datafields variable, should be a dict or dict-like
            object.
        """
        self._datafields = value

    def __init__(self):
        self.reset()

    def __copy__(self, new_copy=False):
        """
            copy this instance
        """
        if new_copy is False:
            new_copy = type(self)()

        new_copy._dataset = self._dataset
        new_copy._recordindex = self._recordindex
        new_copy._datafields = self._datafields

        for field in self._datafields.keys():
            setattr(new_copy, key, getattr(self, key))

        return new_copy

    def __deepcopy__(self, memo, new_copy=False):
        """
            deepcopy this instance
        """
        if new_copy is False:
            new_copy = type(self)()

        new_copy._dataset = copy.deepcopy(self._dataset)
        new_copy._recordindex = copy.deepcopy(self._recordindex)
        new_copy._datafields = copy.deepcopy(self._datafields)

        for field in self._datafields.keys():
            setattr(new_copy, key, copy.deepcopy(getattr(self, key)))

        return new_copy

    def __iter__(self):
        """
            Iterate over a set of rows from the recordset
        """
        if self._recordset:
            uniques = len(self._unique_keys)
            starting_index = self._starting_record_index
            if starting_index is None:
                starting_index = 0

            for index, values in enumerate(self._recordset[starting_index:]):
                true_index = starting_index + index
                if index == 0:
                    self._parse_record(true_index)
                    yield self
                elif index > 0:
                    if len([key for key in self._stop_iter_keys if self._recordset[true_index][key] != self._recordset[true_index - 1][key]]):
                        raise StopIteration

                    if (uniques and len([key for key in self._unique_keys if self._recordset[true_index][key] != self._recordset[true_index - 1][key]])) or not uniques:
                        self._parse_record(true_index)
                        yield self
        else:
            raise StopIteration

    def _parse_record(self, index):
        """
            Set any values found in the recordset that matches this model's name
        """
        if self._recordset:
            self._recordindex = index

            for key, alias in self._lookup_fields.items():
                setattr(self, key, self._recordset[index].get(alias))

    def reset(self):
        """
            Clear the recordset, index, and values, columns used in this recordset
            In addtion it removes the attributes names used in the previous recordset
        """
        for key in getattr(self, '_lookup_fields', {}).keys():
            delattr(self, key)

        self._lookup_fields = {}
        self._unique_keys = []
        self._stop_iter_keys = []

        self._recordindex = None
        self._starting_record_index = None
        self._recordset = None

