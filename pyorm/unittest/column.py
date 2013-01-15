from pyorm.column import Column
import copy
import unittest


class TestColumn(unittest.TestCase):

    def setUp(self):
        pass

    def test_010(self):
        """ Column: __init__ properly set up when using class attribute accessor. """
        column = Column.relationship1.relationship2.relationship3.field
        self.assertEqual(column._queue, ['relationship1',
                         'relationship2', 'relationship3', 'field'])

    def test_011(self):
        """ Column: __init__ properly set up when using __init__ directly. """
        column = Column(
            ['relationship1', 'relationship2', 'relationship3'], 'field')
        self.assertEqual(column._queue, ['relationship1',
                         'relationship2', 'relationship3', 'field'])

    def test_012(self):
        """ Column: __init__ properly set up when using __init__ directly with no relations. """
        column = Column(False, 'field')
        self.assertEqual(column._queue, ['field'])

    def test_020(self):
        """ Column: __init__ properly set up when using class attribute accessor and parent scope. """
        column = Column(
            scope='parent').relationship1.relationship2.relationship3.field
        self.assertEqual(column._queue, ['relationship1',
                         'relationship2', 'relationship3', 'field'])
        self.assertTrue(column._scope)

    def test_021(self):
        """ Column: __init__ properly set up when using __init__ directly with parent scope. """
        column = Column(['relationship1', 'relationship2',
                        'relationship3'], 'field', 'parent')
        self.assertEqual(column._queue, ['relationship1',
                         'relationship2', 'relationship3', 'field'])

    def test_030(self):
        """ Column: __copy__ makes a correct copy of a column object """
        column = Column.relationship1.relationship2.relationship3.field
        columncopy = copy.copy(column)

        self.assertEqual(column._queue, columncopy._queue)
        self.assertEqual(column._scope, columncopy._scope)
        self.assertNotEqual(id(column._queue), id(columncopy._queue))

    def test_040(self):
        """ Column: Comparison operators between a column instance and any non-model/non-expression return a coupled pair."""
        for op in ('==', '!=', '<=', '>=', '<', '>'):
            exp = eval('5 {0} Column.test.field'.format(op))
            self.assertTrue(exp._coupled_pair)
            exp = eval('Column.test.field {0} 5'.format(op))
            self.assertTrue(exp._coupled_pair)

    def test_050(self):
        """ Column: __str__ method prints generic format correctly"""
        column = Column.relationship1.relationship2.relationship3.field
        self.assertEqual(
            str(column), 'relationship1.relationship2.relationship3.field')
