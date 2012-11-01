import unittest

from pyorm.expression import Expression, Equation, calc_tokens
from pyorm.token import *


class MockOwner(object):
    def __hash__(self):
        return 1


class CalcTokensTestCase(unittest.TestCase):
    def test_calc_tokens_new_expr(self):
        expr1 = Expression(1, 2, op=OP_ADD)
        expr2 = 1

        # calc_tokens should return a new expression containing
        # expr1 and expr2 with OP_SUB as the operator
        new_expr = calc_tokens(expr1, expr2, op=OP_SUB)
        self.assertEqual(new_expr._tokens[0].type, T_EXP)
        self.assertEqual(new_expr._tokens[1], Token(T_OPR, OP_SUB))
        self.assertEqual(new_expr._tokens[2].type, T_LIT)
        self.assertNotEqual(id(new_expr), id(expr1))

    def test_calc_tokens_new_expr_right(self):
        expr1 = Expression(1, 2, op=OP_ADD)
        expr2 = 1

        # Test the same thing as above, but from the right side
        new_expr = calc_tokens(expr2, expr1, op=OP_SUB, right=True)
        self.assertEqual(new_expr._tokens[2].type, T_EXP)
        self.assertEqual(new_expr._tokens[1], Token(T_OPR, OP_SUB))
        self.assertEqual(new_expr._tokens[0].type, T_LIT)
        self.assertNotEqual(id(new_expr), id(expr1))

    def test_calc_tokens_append_tokens(self):
        # verify that calc_tokens returns the primary expression
        # with the secondary expression's tokens appended when the
        # operator matches
        expr1 = Expression(1, 2, op=OP_ADD)
        expr2 = 2

        new_expr = calc_tokens(expr1, expr2, op=OP_ADD)
        self.assertEqual(id(new_expr), id(expr1))

    def test_calc_tokens_insert_tokens_right(self):
        # verify that calc_tokens returns the primary expression
        # with the secondary expression's tokens inserted at index
        # zero when the operator matches, and the primary 
        # expression is on the right.
        expr1 = Expression(1, 2, op=OP_ADD)
        expr2 = 2

        new_expr = calc_tokens(expr2, expr1, op=OP_ADD, right=True)
        self.assertEqual(id(new_expr), id(expr1))


class ExpressionTestCase(unittest.TestCase):
    def test_literals(self):
        expr = Expression(1, 3, 2, 4, op=OP_SUB)
        self.assertEqual(expr, [1, 3, 2, 4])

    def test_nested_literals(self):
        expr1 = Expression(2, 3, 4, op=OP_SUB)
        expr2 = Expression(1, expr1, 5, 6, op=OP_ADD)
        self.assertEqual(expr2.literals, [1, 2, 3, 4, 5, 6])

