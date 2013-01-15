class DatabaseNotDefinedError(Exception):
    def __init__(self, database):
        Exception.__init__(
            self, u'The connection `{0}` is not defined.'.format(database))


class BadConfigError(Exception):
    def __init__(self, database):
        Exception.__init__(self, u'The connection object `{0}` must be a dictionary or subclass of a dictionary.'.format(database))


class DialectNotDefinedError(Exception):
    def __init__(self, database):
        Exception.__init__(self, u'The dialect is not defined for connection `{0}`'.format(database))


class DialectNotFoundError(Exception):
    def __init__(self, dialect, database):
        Exception.__init__(self, u'The dialect `{0}` could not be found for connection `{1}`.'.format(dialect, database))


class CouldNotConnectError(Exception):
    def __init__(self, database):
        Exception.__init__(self, u'The connection to `{0}` could not be established.'.format(database))


class TableMissingError(Exception):
    def __init__(self, tables):
        self._tables = tables
        Exception.__init__(self, u'The table(s) `{0}` could not be located.'.format('`,`'.join(self._tables)))


class ColumnMissingError(Exception):
    pass


class TableCreationError(Exception):
    def __init__(self, model_name, errstr):
        Exception.__init__(self, u'Failed to create table `{0}`, reason was: {1}.'.format(model_name, errstr))
