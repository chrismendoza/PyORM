import copy
import unittest

from pyorm.nodelist import NodeList


class TestNodeList(unittest.TestCase):

    def setUp(self):
        t = NodeList()
        self.nodelist = NodeList('test', 'fields', 'fries', 3, 5.00, [], {}, t)
        self.sample_data = ['test', 'fields', 'fries', 3, 5.00, [], {}, t]

    def test_010(self):
        """ NodeList: __init__ works with data passed in."""
        self.assertEqual(type(self.nodelist._node_list), list)
        self.assertEqual(self.nodelist._node_list, self.sample_data)

    def test_011(self):
        """ NodeList: __init__ works with no data passed in. """
        nodelist = NodeList()
        self.assertEqual(type(nodelist._node_list), list)
        self.assertEqual(nodelist._node_list, [])

    def test_020(self):
        """ NodeList: __copy__ returns a new list, but preserves references to old values in the list. """
        # test copying, we need to make sure its an actual copy, not a reference to the original
        nodecopy = copy.copy(self.nodelist)
        self.assertEqual(self.nodelist._node_list, nodecopy._node_list)
        self.assertNotEqual(id(self.nodelist), id(nodecopy))
        self.assertNotEqual(
            id(self.nodelist._node_list), id(nodecopy._node_list))
        for i in range(0, len(self.nodelist)):
            self.assertEqual(
                id(self.nodelist._node_list[i]), id(nodecopy._node_list[i]))

    def test_030(self):
        """ NodeList: __deepcopy__ works as expected, copying objects in the list. """
        nodedeepcopy = copy.deepcopy(self.nodelist)
        self.assertNotEqual(id(self.nodelist), id(nodedeepcopy))
        self.assertNotEqual(
            id(self.nodelist._node_list), id(nodedeepcopy._node_list))
        for i in range(0, len(self.nodelist)):
            # only check dict/list/tuple/NodeList items (string, unicode, float, int all produce
            # the same id() value despite being different objects)
            if isinstance(self.nodelist._node_list[i], (list, tuple, dict, NodeList)):
                self.assertNotEqual(id(self.nodelist._node_list[
                                    i]), id(nodedeepcopy._node_list[i]))

    def test_040(self):
        """ NodeList: __len__ returns the proper length from NodeList._node_list. """
        self.assertEqual(len(self.nodelist), len(self.nodelist._node_list))

    def test_050(self):
        """ NodeList: __getitem__ provides access to all items in its internal list based on the length. """
        for i in range(0, len(self.sample_data)):
            self.assertEqual(self.nodelist[i], self.sample_data[i])

    def test_051(self):
        """ NodeList: __getitem__ raises an IndexError when accessing data outside its maximum length. """
        self.assertRaises(IndexError, self.nodelist.__getitem__, 49)

    def test_060(self):
        """ NodeList: __iter__ Works with data present."""
        for index, value in enumerate(self.nodelist):
            self.assertEqual(value, self.sample_data[index])

    def test_061(self):
        """ NodeList: __iter__ Works with no data present."""
        nodelist = NodeList()
        count = 0
        for index, value in enumerate(nodelist):
            count = index
        self.assertEqual(count, 0)

    def test_070(self):
        """ NodeList: append to NodeList works properly when presented with data """
        self.sample_data.append(['list', 'append'])
        self.assertEqual(self.nodelist.append(
            ['list', 'append'])._node_list, self.sample_data)

    def test_071(self):
        """ NodeList: append to NodeList raises TypeError when supplied no data """
        self.assertRaises(TypeError, self.nodelist.append)

    def test_080(self):
        """ NodeList: extend NodeList with list properly extends the node list. """
        self.sample_data.extend(['list', 'append'])
        self.assertEqual(self.nodelist.extend(
            ['list', 'append'])._node_list, self.sample_data)

    def test_081(self):
        """ NodeList: extend NodeList with NodeList properly extends the node list. """
        self.sample_data.extend(['list', 'append'])
        self.assertEqual(self.nodelist.extend(
            NodeList('list', 'append'))._node_list, self.sample_data)

    def test_082(self):
        """ NodeList: extend NodeList with a non-iterable appends instead. """
        self.sample_data.append(123)
        self.assertEqual(
            self.nodelist.extend(123)._node_list, self.sample_data)

    def test_090(self):
        """ NodeList: insert into NodeList properly inserts into position. """
        self.sample_data.insert(0, 'cheese')
        self.assertEqual(
            self.nodelist.insert(0, 'cheese')._node_list, self.sample_data)

    def test_100(self):
        """ NodeList: remove from NodeList works when provided a correct value."""
        self.sample_data.remove('test')
        self.assertEqual(
            self.nodelist.remove('test')._node_list, self.sample_data)

    def test_101(self):
        """ NodeList: remove from NodeList ignores incorrect values. """
        nodelist = NodeList()
        self.assertEqual(id(nodelist.remove('test')), id(nodelist))

    def test_110(self):
        """ NodeList: pop from NodeList works with keys in range. """
        self.assertEqual(self.nodelist.pop(2), self.sample_data.pop(2))
        self.assertEqual(self.nodelist._node_list, self.sample_data)

    def test_111(self):
        """ NodeList: pop from NodeList works with no key specified. """
        self.assertEqual(self.nodelist.pop(), self.sample_data.pop())
        self.assertEqual(self.nodelist._node_list, self.sample_data)

    def test_112(self):
        """ NodeList: pop from NodeList raises ValueError for keys out of range."""
        self.assertRaises(IndexError, self.nodelist.pop, 4123)

    def test_120(self):
        """ NodeList: __str__ method produces an actual string"""
        self.assertEqual(str(self.nodelist), str(self.sample_data))
