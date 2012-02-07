from pyorm.connection import Connection
import unittest


class DBConfig(object):
    Test = {
        'dialect': 'MySQL',
        'user': 'user',
        'passwd': 'pass',
        'host': 'localhost',
        'port': 3306,
        'db': 'test_db',
        'debug': True,
        'autocommit': True
    }
    default_read_server = 'Test'
    default_write_server = 'Test'

class TestConnection(unittest.TestCase):

    def setUp(self):
        Connection.set_config(DBConfig)

    def test_config(self):
        """ Connection: Connection.set_config() sets the config class properly. """
        self.assertEqual(id(DBConfig), id(Connection._config))

    def test_connection(self):
        """ Connection: Connection.Test.test() is able to get a cursor """
        self.assertTrue(Connection.Test.test())

    def test_close_all(self):
        """ Connection: Connection.close_all() clears the current connections """
        Connection.Test.test()
        Connection.close_all()
        self.assertEqual(Connection._connections, {})
