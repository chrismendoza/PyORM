class Index(object):
    declaration_index = 0

    def __init__(self, *args):
        self._fields = []
        self._fields.extend(args)
        self.declaration_index = Index.declaration_index
        Index.declaration_index += 1

class PrimaryKey(Index):
    pass

class UniqueIndex(Index):
    pass

class FullTextIndex(Index):
    pass

class SpatialIndex(Index):
    pass
