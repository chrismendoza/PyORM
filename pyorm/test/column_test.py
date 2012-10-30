import unittest, weakref, copy

from pyorm.column import Column
from pyorm.expression import Expression, Equation
from pyorm.token import *


class MockOwner(object):
    def __hash__(self):
        return 1


class ColumnTestCase(unittest.TestCase):
    def test_path(self):
        """
            Test to verify that a new column creates a new
            path chain based on the attributes accessed.
        """
        col = Column.test.column.chain
        self.assertEqual(col._path, ['test','column','chain'])

    def test_alias(self):
        """
            Tests that an alias can be applied, and re-applied
        """
        col = Column.test.field

        col.set_alias('fish')
        self.assertEqual(col._alias, 'fish')
        self.assertEqual(col.get_alias(), 'fish')

        col.set_alias('cheese')
        self.assertEqual(col._alias, 'cheese')
        self.assertEqual(col.get_alias(), 'cheese')

    def test_scope(self):
        """
            Test setting scope both on Column initialization and
            after column initialization.
        """
        col = Column(scope='parent').test.field
        self.assertEqual(col._scope, 'parent')
        self.assertEqual(col.get_scope(), 'parent')

        col.set_scope('normal')
        self.assertEqual(col._scope, 'normal')
        self.assertEqual(col.get_scope(), 'normal')

    def test_owner(self):
        """
            Verify that the owner is saved as a weak reference proxy
            to the original object.
        """
        col = Column.test.field
        mock_owner = MockOwner()
        col.owner = mock_owner

        self.assertEqual(col._owner, weakref.proxy(mock_owner))
        self.assertEqual(col.owner, weakref.proxy(mock_owner))
        self.assertEqual(id(col._owner_ref()), id(mock_owner))

    def test_copy(self):
        """
            Tests the creation of a copy
        """
        mock_owner = MockOwner()
        col = Column(scope='parent').test.field
        col.set_alias('cheese')
        col.owner = mock_owner

        col_copy = copy.copy(col)

        self.assertNotEqual(id(col), id(col_copy))
        self.assertEqual(id(col._owner), id(col_copy._owner))
        

    def test_deepcopy(self):
        """
            Tests the creation of a deep copy (which is the same as
            a copy for column objects, due to the use of weakref.proxy()
            for the owner).
        """
        mock_owner = MockOwner()
        col = Column(scope='parent').test.field
        col.set_alias('cheese')
        col.owner = mock_owner

        col_copy = copy.copy(col)

        self.assertNotEqual(id(col), id(col_copy))
        self.assertEqual(id(col._owner), id(col_copy._owner))

    def test_hash(self):
        """
            Checks to see if the has of two objects with the same options
            hash to the same value, and that two column objects that do
            not share all of the same objects hash to different values
        """
        mock_owner = MockOwner()
        col = Column(scope='parent').test.field
        col.set_alias('fish')
        col.owner = mock_owner

        mock_owner2 = MockOwner()
        col2 = Column(scope='parent').test.field
        col2.set_alias('fish')
        col2.owner = mock_owner2

        self.assertEqual(hash(col), hash(col2))

        mock_owner3 = MockOwner()
        col3 = Column(scope='parent').test.field
        col3.set_alias('cheese')
        col3.owner = mock_owner

        self.assertNotEqual(hash(col), hash(col3))

    def test_and(self):
        exp = Column.test & 1
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_AND)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

    def test_rand(self):
        exp = 1 & Column.test
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_AND)
        self.assertEqual(exp._tokens[-1].type, T_COL)
        self.assertEqual(exp._tokens[0].type, T_LIT)

    def test_or(self):
        exp = Column.test | 1
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_OR)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

    def test_ror(self):
        exp = 1 | Column.test
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_OR)
        self.assertEqual(exp._tokens[-1].type, T_COL)
        self.assertEqual(exp._tokens[0].type, T_LIT)

    def test_add(self):
        exp = Column.test + 1
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_ADD)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

    def test_radd(self):
        exp = 1 + Column.test
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_ADD)
        self.assertEqual(exp._tokens[-1].type, T_COL)
        self.assertEqual(exp._tokens[0].type, T_LIT)

    def test_sub(self):
        exp = Column.test - 1
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_SUB)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

    def test_rsub(self):
        exp = 1 - Column.test
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_SUB)
        self.assertEqual(exp._tokens[-1].type, T_COL)
        self.assertEqual(exp._tokens[0].type, T_LIT)

    def test_mul(self):
        exp = Column.test * 1
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_MUL)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

    def test_rmul(self):
        exp = 1 * Column.test
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_MUL)
        self.assertEqual(exp._tokens[-1].type, T_COL)
        self.assertEqual(exp._tokens[0].type, T_LIT)

    def test_div(self):
        exp = Column.test / 1
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_DIV)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

    def test_rdiv(self):
        exp = 1 / Column.test
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_DIV)
        self.assertEqual(exp._tokens[-1].type, T_COL)
        self.assertEqual(exp._tokens[0].type, T_LIT)

    def test_mod(self):
        exp = Column.test % 1
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_MOD)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

    def test_rmod(self):
        exp = 1 % Column.test
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_MOD)
        self.assertEqual(exp._tokens[-1].type, T_COL)
        self.assertEqual(exp._tokens[0].type, T_LIT)

    def test_pow(self):
        exp = Column.test ** 1
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_POW)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

    def test_rpow(self):
        exp = 1 ** Column.test
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_POW)
        self.assertEqual(exp._tokens[-1].type, T_COL)
        self.assertEqual(exp._tokens[0].type, T_LIT)

    def test_ne(self):
        exp = Column.test != 1
        self.assertEqual(type(exp), Equation)
        self.assertEqual(exp.op, OP_NE)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

        exp = Column.test != None
        self.assertEqual(type(exp), Equation)
        self.assertEqual(exp.op, OP_NULLNE)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

        exp = Column.test != Column.fish
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_NE)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_COL)

    def test_ne(self):
        exp = Column.test == 1
        self.assertEqual(type(exp), Equation)
        self.assertEqual(exp.op, OP_EQ)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

        exp = Column.test == None
        self.assertEqual(type(exp), Equation)
        self.assertEqual(exp.op, OP_NULLEQ)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

        exp = Column.test == Column.fish
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_EQ)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_COL)

    def test_lt(self):
        exp = Column.test < 1
        self.assertEqual(type(exp), Equation)
        self.assertEqual(exp.op, OP_LT)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

        exp = Column.test < Column.fish
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_LT)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_COL)

    def test_le(self):
        exp = Column.test <= 1
        self.assertEqual(type(exp), Equation)
        self.assertEqual(exp.op, OP_LE)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

        exp = Column.test <= Column.fish
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_LE)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_COL)

    def test_ge(self):
        exp = Column.test >= 1
        self.assertEqual(type(exp), Equation)
        self.assertEqual(exp.op, OP_GE)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

        exp = Column.test >= Column.fish
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_GE)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_COL)

    def test_gt(self):
        exp = Column.test > 1
        self.assertEqual(type(exp), Equation)
        self.assertEqual(exp.op, OP_GT)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_LIT)

        exp = Column.test > Column.fish
        self.assertEqual(type(exp), Expression)
        self.assertEqual(exp.op, OP_GT)
        self.assertEqual(exp._tokens[0].type, T_COL)
        self.assertEqual(exp._tokens[-1].type, T_COL)
