# used to define the default session used by models when first instantiated.
# this can be overridden in the models by passing a session arguement to the
# model when initialized.
default_session = None


class SessionDirtyException(Exception):
    pass


class Session(object):
    """
        The Session class is used to maintain a set of connections based on a specific
        configuration.  The configuration itself should implement attribute access, and it
        is assumed that the config is actually a class itself.

        The reason it assumes the config is a class, is so that it can pass itself to the
        config's __init__ or __call__, allowing the config to do things like toggle to a
        set of backup servers, and invalidating the connections currently in use.
    """
    @property
    def is_dirty(self):
        """
            Returns whether any of the currently open connections have uncommitted changes.
        """
        dirty = False

        for connection in self.connections:
            if connection.is_dirty:
                dirty = True

        return dirty

    @property
    def config(self):
        """
            Returns the current configuration for this session, returns None if one hasn't
            been specified yet.
        """
        return getattr(self, '_config', None)

    @config.setter
    def config(self, config):
        """
            Attempts to change the config file in use on a session, if the session has
            already been used to push data to the servers, but the transaction has not
            been committed, raises an exception.
        """
        if self.is_dirty:
            raise SessionDirtyException()

        self._config = config(self)

    def __init__(self, config, default=False):
        """
            The session object takes two parameters, the config file to be used,
            and whether or not this session should become the default session. If
            the default session is already set and is marked as dirty, raises an
            exception.
        """
        self.config = config

        if default:
            if not getattr(default_session, 'is_dirty', False):
                # pull in the global default_session var, so we can modify it.  The
                # purpose of this var is to maintain state for multiple models, after
                # the initial declaration, so this actually makes sense here.
                global default_session

                default_session = self

            else:
                raise SessionDirtyException()

    def commit(self):
        """
            Commits any currently uncommitted changes.
        """
        for connection in self.connections:
            if connection.is_dirty:
                connection.commit()

    def rollback(self):
        """
            Rolls back any currently uncommitted changes.
        """
        for connection in self.connections:
            if connection.is_dirty:
                connection.rollback()
