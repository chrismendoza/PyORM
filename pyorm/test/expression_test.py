import unittest

from pyorm.expression import Expression, Equation, calc_tokens
from pyorm.token import *


class CalcTokensTestCase(unittest.TestCase):
    def test_calc_tokens_new_expr(self):
        expr1 = Expression(1, OP_ADD)
        expr2 = 1

        # calc_tokens should return a new expression containing
        # expr1 and expr2 with OP_SUB as the operator
        new_expr = calc_tokens(expr1, expr2, op=OP_SUB)
        self.assertEqual(new_expr._tokens[0].type, T_EXP)
        self.assertEqual(new_expr._tokens[1], Token(T_OPR, OP_SUB))
        self.assertEqual(new_expr._tokens[2].type, T_LIT)

    def test_calc_tokens_new_expr_right(self):
        expr1 = Expression(1, OP_ADD)
        expr2 = 1

        # Test the same thing as above, but from the right side
        new_expr = calc_tokens(expr2, expr1, op=OP_SUB, right=True)
        self.assertEqual(new_expr._tokens[2].type, T_EXP)
        self.assertEqual(new_expr._tokens[1], Token(T_OPR, OP_SUB))
        self.assertEqual(new_expr._tokens[0].type, T_LIT)

    def test_calc_tokens_append_tokens(self):
        # verify that calc_tokens returns the primary expression
        # with the secondary expression's tokens appended when the
        # operator matches
        expr1 = Expression(1, OP_ADD)
        expr2 = 2

        new_expr = calc_tokens(expr1, expr2, op=OP_ADD)
        self.assertEqual(id(new_expr), expr1)

    def test_calc_tokens_insert_tokens_right(self):
        # verify that calc_tokens returns the primary expression
        # with the secondary expression's tokens inserted at index
        # zero when the operator matches, and the primary 
        # expression is on the right.
        expr1 = Expression(1, OP_ADD)
        expr2 = 2

        new_expr = calc_tokens(expr2, expr1, op=OP_ADD, right=True)
        self.assertEqual(id(new_expr), expr1)
