from pyorm.token import Token
import unittest

class TestToken(unittest.TestCase):
    def test_001(self):
        """ Token: __getattr__ returns the correct value for the given name """
        for index, token in enumerate(Token.tokens):
            self.assertEqual(getattr(Token, token), index)

    def test_002(self):
        """ Token: gettype() returns the correct token name """
        for index, token in enumerate(Token.tokens):
            self.assertEqual(Token.gettype(index), token)
