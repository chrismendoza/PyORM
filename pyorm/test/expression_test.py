import copy
import unittest

from pyorm.column import Column
from pyorm.expression import Expression, Equation, calc_tokens
from pyorm.token import *


class MockGeneric(object):
    pass


class MockOwner(object):
    def __init__(self, hash_value=None):
        self._hash = hash_value if hash_value is not None else 1

    def __hash__(self):
        return self._hash


class MockField(object):
    @classmethod
    def to_db(cls, value):
        return hash(value)


class MockUnbound(object):
    cls = MockField


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

    def test_tokens(self):
        expr1 = Expression(1, 2, 3, op=OP_ADD)
        self.assertEqual(expr1._tokens, [
                Token(T_LIT, 1),
                Token(T_OPR, OP_ADD),
                Token(T_LIT, 2),
                Token(T_OPR, OP_ADD),
                Token(T_LIT, 3)
            ])

    def test_owner(self):
        expr2 = Expression('test', 'fish', op=OP_SUB)
        expr1 = Expression(1, 2, expr2, op=OP_ADD)
        mock_owner = MockOwner()

        expr1.owner = mock_owner
        self.assertEqual(id(expr1._owner_ref()), id(expr2._owner_ref()))
    
    def test_copy(self):
        expr = Expression(1, 2, 3, Expression(1, 3, 4), op=OP_SUB)
        mock_owner = MockOwner()
        expr.owner = mock_owner
        expr_copy = copy.copy(expr)

        self.assertNotEqual(id(expr), id(expr_copy))
        self.assertNotEqual(id(expr._tokens), id(expr_copy._tokens))
        self.assertEqual(
            [id(t) for t in expr._tokens],
            [id(t) for t in expr_copy._tokens])
        self.assertEqual(expr.alias, expr_copy.alias)
        self.assertEqual(id(expr._owner_ref()), id(expr_copy._owner_ref()))

    def test_deepcopy(self):
        expr = Expression(1, 2, 3, Expression(1, 3, 4), op=OP_SUB)
        mock_owner = MockOwner()
        expr.owner = mock_owner
        expr_copy = copy.deepcopy(expr)

        self.assertNotEqual(id(expr), id(expr_copy))
        self.assertNotEqual(id(expr._tokens), id(expr_copy._tokens))
        self.assertNotEqual(
            [id(t) for t in expr._tokens],
            [id(t) for t in expr_copy._tokens])
        self.assertEqual(expr._tokens, expr_copy._tokens)
        self.assertEqual(expr.alias, expr_copy.alias)
        self.assertEqual(id(expr._owner_ref()), id(expr_copy._owner_ref()))

    def test_mul(self):
        expr = Expression(1, 2, op=OP_ADD) * 4
        self.assertEqual(expr._tokens[0].type, T_EXP)
        self.assertEqual(expr._tokens[-1].type, T_LIT)

    def test_rmul(self):
        expr = 4 / Expression(1, 2, op=OP_ADD)
        self.assertEqual(expr._tokens[0].type, T_LIT)
        self.assertEqual(expr._tokens[-1].type, T_EXP)

    def test_div(self):
        expr = Expression(1, 2, op=OP_ADD) * 4
        self.assertEqual(expr._tokens[0].type, T_EXP)
        self.assertEqual(expr._tokens[-1].type, T_LIT)

    def test_rdiv(self):
        expr = 4 / Expression(1, 2, op=OP_ADD)
        self.assertEqual(expr._tokens[0].type, T_LIT)
        self.assertEqual(expr._tokens[-1].type, T_EXP)

    def test_mod(self):
        expr = Expression(1, 2, op=OP_ADD) % 4
        self.assertEqual(expr._tokens[0].type, T_EXP)
        self.assertEqual(expr._tokens[-1].type, T_LIT)

    def test_rmod(self):
        expr = 4 % Expression(1, 2, op=OP_ADD)
        self.assertEqual(expr._tokens[0].type, T_LIT)
        self.assertEqual(expr._tokens[-1].type, T_EXP)

    def test_pow(self):
        expr = Expression(1, 2, op=OP_ADD) ** 4
        self.assertEqual(expr._tokens[0].type, T_EXP)
        self.assertEqual(expr._tokens[-1].type, T_LIT)

    def test_rpow(self):
        expr = 4 ** Expression(1, 2, op=OP_ADD)
        self.assertEqual(expr._tokens[0].type, T_LIT)
        self.assertEqual(expr._tokens[-1].type, T_EXP)

    def test_ne(self):
        expr = Expression(1, 2, op=OP_ADD) != None
        self.assertEqual(expr.op, OP_NULLNE)

        expr = Expression(1, 2, op=OP_ADD) != 3
        self.assertEqual(expr.op, OP_NE)

    def test_eq(self):
        expr = Expression(1, 2, op=OP_ADD) == None
        self.assertEqual(expr.op, OP_NULLEQ)

        expr = Expression(1, 2, op=OP_ADD) == 3
        self.assertEqual(expr.op, OP_EQ)

    def test_lt(self):
        expr = Expression(1, 2, op=OP_ADD) < 3
        self.assertEqual(expr.op, OP_LT)

    def test_le(self):
        expr = Expression(1, 2, op=OP_ADD) <= 3
        self.assertEqual(expr.op, OP_LE)

    def test_ge(self):
        expr = Expression(1, 2, op=OP_ADD) > 3
        self.assertEqual(expr.op, OP_GT)

    def test_gt(self):
        expr = Expression(1, 2, op=OP_ADD) >= 3
        self.assertEqual(expr.op, OP_GE)

    def test_hash(self):
        expr1 = Expression(1, 2, op=OP_ADD)
        expr2 = Expression(1, 2, op=OP_ADD)
        expr3 = Expression(1, 2, op=OP_SUB)

        mock_owner1 = MockOwner(hash_value=3)
        mock_owner2 = MockOwner(hash_value=2)

        self.assertEqual(hash(expr1), hash(expr2))
        self.assertNotEqual(hash(expr1), hash(expr3))

        expr1.owner = mock_owner1
        expr2.owner = mock_owner1

        self.assertEqual(hash(expr1), hash(expr2))

        expr2.owner = mock_owner2
        self.assertNotEqual(hash(expr1), hash(expr2))


class EquationTestCase(unittest.TestCase):
    def test_literals(self):
        mock_owner = MockOwner()
        mock_owner.relationships = MockGeneric()
        mock_owner.relationships.relationship = MockGeneric()
        mock_owner.relationships.relationship.model = MockGeneric()
        mock_owner.relationships.relationship.model.field = MockUnbound()

        # if there is no owner, equation should return the raw value
        equation = Column.relationship.field == 'test'
        self.assertEqual(equation.literals, ['test'])

        # if there is an owner, the equation should return the value
        # as calculated by the field's to_db() method (if it can be found)
        equation.owner = mock_owner
        self.assertEqual(equation.literals, [hash('test')])
