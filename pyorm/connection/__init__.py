import time

from pyorm.connection import exceptions
from pyorm.event import Event, event_decorator


class Connection(object):
    _config = None
    _connections = {}

    class __metaclass__(type):
        """
            Connection's metaclass is in place to allow pulling a connection
            directly off of the Connection class, so if 'DB1a' was defined in
            the config, the user would have direct query access using:

            Connection.DB1a.query('''
                SELECT
                    *
                FROM
                    table
                WHERE
                    field1 = %s AND
                    field2 = %s
            ''', (value1, value2))
        """
        def __getattr__(cls, server):
            """
                Return the specified connection, opening a new one if necessary.
            """
            return getattr(Connection(), server, False)

    @classmethod
    def set_config(cls, config):
        """
            Sets the configuration to use
        """
        if config is not None:
            cls._config = config

    @classmethod
    @event_decorator('OpenConnection')
    def open(cls, server):
        """
            Establishes connections to the specified server
        """
        config = getattr(cls._config, server, False)

        if not config:
            raise exceptions.DatabaseNotDefinedError(server)

        dialect = config.get('dialect', False)
        if dialect:
            try:
                mod = __import__('pyorm.connection.{0}'.format(
                    dialect), {}, {}, '{0}Connection'.format(dialect))
                conn = getattr(mod, '{0}Connection'.format(dialect), None)
            except ImportError:
                raise exceptions.DialectNotFoundError(dialect, server)

            tries = 0
            while tries < config.get('attempts', 4):
                tries += 1
                try:
                    cls._connections[server] = conn(**config)
                    break
                except:
                    time.sleep(1)
            else:
                if not cls._connections.get(server):
                    raise exceptions.CouldNotConnectError(server)

        else:
            raise exceptions.DialectNotDefinedError(server)

    @classmethod
    @event_decorator('CloseConnection')
    def close(cls, server):
        """
            Close a given connection
        """
        conn = cls._connections.get(server, None)
        if conn is not None:
            conn.close()
            del(cls._connections[server])

    @classmethod
    def close_all(cls):
        """
            Close all open connections
        """
        for conn in cls._connections.values():
            conn.close()
        cls._connections = {}

    @event_decorator('GetConnection')
    def __getattr__(self, server):
        """
            Return the specified connection, opening a new one if necessary.
        """
        if not server.startswith('__') and self._connections.get(server, None) is None or not self._connections.get(server).test():
            Connection.open(server)

        if self._connections.get(server, None) is not None:
            return self._connections[server]
        else:
            return False
