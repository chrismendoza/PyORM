from pyorm.expression import Expression
from pyorm.token import Token
import unittest


class TestExpression(unittest.TestCase):
    """ Expression Unit Tests """
    def setUp(self):
        self.algebraic_operators = [
            ('AND', '&'),
            ('OR', '|'),
            ('ADD', '+'),
            ('SUB', '-'),
            ('DIV', '/'),
            ('MUL', '*'),
            ('MOD', '%'),
            ('POW', '**')
        ]
        self.comparison_operators = [
            ('EQ', '=='),
            ('NE', '!='),
            ('LT', '<'),
            ('GT', '>'),
            ('LE', '<='),
            ('GE', '>=')
        ]
        self.special_operators = [
            ('STARTSWITH', 'startswith'),
            ('CONTAINS', 'contains'),
            ('ENDSWITH', 'endswith')
        ]
        self.none_operators = [
            ('NULLEQ', '=='),
            ('NULLNE', '!=')
        ]

        from pyorm.model import Model
        from pyorm.field import Field

        class TestModel(Model):
            class Fields(object):
                test = Field()

        self.testmodel = TestModel()

    def test_010(self):
        """ Expression: __init__ works properly with no arguments."""
        exp = Expression()
        self.assertEqual(exp._operator, 'AND')
        self.assertEqual(exp._alias, None)
        self.assertEqual(exp._base_model, None)
        self.assertTrue(exp._enclose)
        self.assertFalse(exp._coupled_pair)

    def test_011(self):
        """ Expression: __init__ works properly with arguments."""
        exp = Expression(3, 4, 5)
        self.assertEqual(exp._operator, 'AND')
        self.assertEqual(exp._alias, None)
        self.assertEqual(exp._base_model, None)
        self.assertTrue(exp._enclose)
        self.assertFalse(exp._coupled_pair)
        self.assertEqual(exp._node_list, [3, 4, 5])

    def test_020(self):
        """ Expression: algebraic operators return the expected expressions."""
        for operator_name, operator in self.algebraic_operators:
            exp = eval(
                'Expression(3).operator(\'AND\') {0} 5'.format(operator))
            self.assertEqual(exp._operator, operator_name)
            self.assertEqual(
                exp._node_list, [Expression(3).operator('AND'), 5])

    def test_021(self):
        """ Expression: reverse algebraic operators return the expected expressions."""
        for operator_name, operator in self.algebraic_operators:
            exp = eval(
                '5 {0} Expression(3).operator(\'AND\')'.format(operator))
            self.assertEqual(exp._operator, operator_name)
            self.assertEqual(
                exp._node_list, [5, Expression(3).operator('AND')])

    def test_030(self):
        """ Expression: Comparison Operators return the expected expressions."""
        for operator_name, operator in self.comparison_operators:
            exp = eval(
                'Expression(3).operator(\'AND\') {0} 5'.format(operator))
            self.assertEqual(exp._operator, operator_name)
            self.assertEqual(
                exp._node_list, [Expression(3).operator('AND'), 5])

    def test_040(self):
        """ Expression: Special Operators return the expected expressions. """
        for operator_name, operator in self.special_operators:
            exp = eval('Expression(3).operator(\'AND\').{0}(\'testing\')'.format(operator))
            self.assertEqual(exp._operator, operator_name)
            self.assertEqual(
                exp._node_list, [Expression(3).operator('AND'), 'testing'])

    def test_050(self):
        """ Expression: None Comparison Operators return the expected expressions."""
        for operator_name, operator in self.none_operators:
            exp = eval(
                'Expression(3).operator(\'AND\') {0} None'.format(operator))
            self.assertEqual(exp._operator, operator_name)
            self.assertEqual(
                exp._node_list, [Expression(3).operator('AND'), None])

    def test_060(self):
        """ Expression: set_alias works with strings. """
        exp = Expression('test', 'cheese', 'fish')
        exp.set_alias('testing')
        self.assertEqual(exp._alias, 'testing')

    def test_061(self):
        """ Expression: set_alias works with unicode. """
        exp = Expression('test', 'cheese', 'fish')
        exp.set_alias(u'testing')
        self.assertEqual(exp._alias, u'testing')

    def test_062(self):
        """ Expression: set_alias works with None. """
        exp = Expression('test', 'cheese', 'fish')
        exp._alias = u'testing'
        exp.set_alias(None)
        self.assertEqual(exp._alias, None)

    def test_063(self):
        """ Expression: set_alias raises a type error on anything but str, unicode and None. """
        exp = Expression('test', 'cheese', 'fish')
        self.assertRaises(TypeError, exp.set_alias, 1)

    def test_070(self):
        """ Expression: get_alias works with strings."""
        exp = Expression(
            'test', Expression('cheese').set_alias('fries'), 'fish')
        exp.set_alias('testing')
        self.assertTrue(exp.get_alias('fries'))

    def test_071(self):
        """ Expression: get_alias works with unicode. """
        exp = Expression(
            'test', Expression('cheese').set_alias(u'fries'), 'fish')
        exp.set_alias(u'testing')
        self.assertTrue(exp.get_alias(u'fries'))

    def test_072(self):
        """ Expression: get_alias raises a type error on anything but str, unicode. """
        exp = Expression('test', 'cheese', 'fish')
        exp.set_alias(u'testing')
        self.assertRaises(TypeError, exp.get_alias, 1)

    def test_080(self):
        """ Expression: enclose properly sets to False when False is passed."""
        exp = Expression('test', 'cheese', 'fish')
        exp.enclose(False)
        self.assertFalse(exp._enclose)

    def test_081(self):
        """ Expression: enclose properly sets to True when True is passed."""
        exp = Expression('test', 'cheese', 'fish')
        exp._enclose = False
        exp.enclose(True)
        self.assertTrue(exp._enclose)

    def test_082(self):
        """ Expression: enclose raises an TypeError when enclose() is passed a non-bool."""
        exp = Expression('test', 'cheese', 'fish')
        self.assertRaises(TypeError, exp.enclose, 'fries')

    def test_090(self):
        """ Expression: tokenize returns a correct string of tokens """
        exp = Expression('outer', Expression(
            'test', 'cheese', 'fish').operator('ADD')).operator('SUB')
        self.assertEqual(
            exp.tokenize(),
            [
                (Token.Operator, 'LPARENTHESIS'),
                (Token.Literal, 'outer'),
                (Token.Operator, 'SUB'),
                (Token.Operator, 'LPARENTHESIS'),
                (Token.Literal, 'test'),
                (Token.Operator, 'ADD'),
                (Token.Literal, 'cheese'),
                (Token.Operator, 'ADD'),
                (Token.Literal, 'fish'),
                (Token.Operator, 'RPARENTHESIS'),
                (Token.Operator, 'RPARENTHESIS'),
            ]
        )

    def test_110(self):
        """ Expression: auto_eager_loads returns a unique and complete list of models to be imported."""
        from pyorm.column import Column
        exp = Column.test.field1 + Column.test2.field1 + \
            Column.test2.subtest.field1
        models = exp.auto_eager_loads()
        self.assertEqual(models, {'test': {}, 'test2': {'subtest': {}}})

    def test_130(self):
        """ Expression: __str__ is returning a properly formatted, escaped string. """
        exp = Expression('test', 'cheese', 'fish')
        self.assertEqual(str(
            exp), "(|pyorm_escape| AND |pyorm_escape| AND |pyorm_escape|)")

        exp = Expression('test', 'cheese', 'fish').operator('EQ')
        self.assertEqual(
            str(exp), "|pyorm_escape| EQ |pyorm_escape| EQ |pyorm_escape|")

        exp = Expression('test', 'cheese', 'fish').set_alias('test')
        self.assertEqual(str(exp), "(|pyorm_escape| AND |pyorm_escape| AND |pyorm_escape|) ALIAS test")
