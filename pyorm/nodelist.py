import copy


class NodeList(object):
    """
        The NodeList class is used for storing a list of values into a list,
        but also for allowing the extend to automatically append non-iterables,
        instead of just blowing up, as well keeping remove from dying when it
        is called on a value that does not exist in the list.

        The original version of the ORM used this sort of structure to modify
        basic functionality of a list, such as .count(), however, since then,
        the helper functions have been moved into their own classes.

        This still may prove useful, at the very least it keeps the basic list
        logic out of the Expression class, and does not require me to extend a
        base python list.

        This is the base model for expression objects.
    """
    def __init__(self, *args):
        if len(args):
            self._node_list = list(args)
        else:
            self._node_list = []

    def __repr__(self):
        """ Define an informative representation of the NodeList object """
        return "<type '{0}' values: {1}>".format(
            type(self),
            ','.join(repr(item) for item in self._node_list)
        )

    def __copy__(self):
        """ return copy of this object """
        return NodeList(*self._node_list[:])

    def __deepcopy__(self, memo):
        return NodeList(*copy.deepcopy(self._node_list))

    def __str__(self):
        """ Define the string output of this object """
        return str(self._node_list)

    def __getitem__(self, key):
        """ Allow retrieval of specific keys from self._node_list using standard [start, stop, step] notation """
        return self._node_list[key]

    def __iter__(self):
        """ Make the Expression object iterable using its argument list (self._node_list) """
        for arg in self._node_list:
            yield arg

    def __len__(self):
        """ Return the number of items in this nodelist """
        return len(self._node_list)

    def append(self, value):
        """ Pass through function for appending expression values """
        self._node_list.append(value)
        return self

    def extend(self, values):
        """ Pass through function for extending expression values """
        if getattr(values, '__getitem__', False) or getattr(values, '__iter__', False):
            self._node_list.extend(values)
        else:
            self.append(values)
        return self

    def insert(self, pos, value):
        """ Pass through function for inserting expression values """
        self._node_list.insert(pos, value)
        return self

    def remove(self, value):
        """ Pass through function for removing values """
        try:
            self._node_list.remove(value)
        except ValueError:
            pass
        return self

    def pop(self, key=False):
        """ Pass through function to pop values and return them """
        if key is False:
            return self._node_list.pop()
        return self._node_list.pop(key)
