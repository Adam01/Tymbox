import unittest
from enum import IntEnum

from PyQt5.QtCore import Qt

from ExtendableItemModel import ExtendableItemModel, ItemModelDataSetType


class TestExtendableItemModel(unittest.TestCase):
    def test_construct(self):
        model = ExtendableItemModel()

    def test_add_columns_list(self):
        model = ExtendableItemModel()
        data = [[1,2,3],[4,5,6],[7,8,9]]

        data_set = model.add_data_set("TestDS", data, ItemModelDataSetType.List, False)
        model.add_column(0, "Testing", data_set, 0)

        self.assertEqual(data[0][0], model.get_data_set_column_value(model.index(0,0)))
        self.assertEqual(data[1][0], model.get_data_set_column_value(model.index(1,0)))
        self.assertEqual(data[2][0], model.get_data_set_column_value(model.index(2,0)))

        self.assertRaises(Exception, model.get_data_set_column_value, model.index(0,1))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(1,1))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(2,1))

        self.assertRaises(Exception, model.get_data_set_column_value, model.index(0, 2))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(1, 2))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(2, 2))


    def test_add_columns_dict(self):
        model = ExtendableItemModel()
        data = [dict(a=1,b=2,c=3), dict(a=4,b=5,c=6), dict(a=7,b=8,c=9)]

        data_set = model.add_data_set("TestDS", data, ItemModelDataSetType.Dict, False)
        model.add_column(0, "Testing", data_set, "a")

        self.assertEqual(data[0]["a"], model.get_data_set_column_value(model.index(0,0)))
        self.assertEqual(data[1]["a"], model.get_data_set_column_value(model.index(1,0)))
        self.assertEqual(data[2]["a"], model.get_data_set_column_value(model.index(2,0)))

        self.assertRaises(Exception, model.get_data_set_column_value, model.index(0,1))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(1,1))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(2,1))

        self.assertRaises(Exception, model.get_data_set_column_value, model.index(0, 2))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(1, 2))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(2, 2))

    def test_add_columns_obj(self):
        model = ExtendableItemModel()
        class Obj:
            def __init__(self, a, b, c):
                self.a = a
                self.b = b
                self.c = c

        data = [Obj(1,2,3), Obj(4,5,6), Obj(7,8,9)]

        data_set = model.add_data_set("TestDS", data, ItemModelDataSetType.Obj, False)
        model.add_column(0, "Testing", data_set, "a")

        self.assertEqual(data[0].a, model.get_data_set_column_value(model.index(0,0)))
        self.assertEqual(data[1].a, model.get_data_set_column_value(model.index(1,0)))
        self.assertEqual(data[2].a, model.get_data_set_column_value(model.index(2,0)))

        self.assertRaises(Exception, model.get_data_set_column_value, model.index(0,1))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(1,1))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(2,1))

        self.assertRaises(Exception, model.get_data_set_column_value, model.index(0, 2))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(1, 2))
        self.assertRaises(Exception, model.get_data_set_column_value, model.index(2, 2))

    def test_add_multiple_columns(self):
        class Columns(IntEnum):
            a = 0
            b = 1
            c = 2

        model = ExtendableItemModel()
        data = [dict(a=1, b=2, c=3), dict(a=4, b=5, c=6), dict(a=7, b=8, c=9)]

        data_set = model.add_data_set("TestDS", data, ItemModelDataSetType.Dict, False)
        model.add_columns(Columns, data_set)

        self.assertEqual(data[0]["a"], model.get_data_set_column_value(model.index(0, 0)))
        self.assertEqual(data[1]["a"], model.get_data_set_column_value(model.index(1, 0)))
        self.assertEqual(data[2]["a"], model.get_data_set_column_value(model.index(2, 0)))

        self.assertEqual(data[0]["b"], model.get_data_set_column_value(model.index(0, 1)))
        self.assertEqual(data[1]["b"], model.get_data_set_column_value(model.index(1, 1)))
        self.assertEqual(data[2]["b"], model.get_data_set_column_value(model.index(2, 1)))

        self.assertEqual(data[0]["c"], model.get_data_set_column_value(model.index(0, 2)))
        self.assertEqual(data[1]["c"], model.get_data_set_column_value(model.index(1, 2)))
        self.assertEqual(data[2]["c"], model.get_data_set_column_value(model.index(2, 2)))


    def test_data(self):
        model = ExtendableItemModel()
        class Obj:
            def __init__(self, a, b, c):
                self.a = a
                self.b = b
                self.c = c

        data_list = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        data_dict = [dict(a=11, b=12, c=13), dict(a=14, b=15, c=16), dict(a=17, b=18, c=19)]
        data_obj = [Obj(21,22,23), Obj(24,25,26), Obj(27,28,29)]

        data_set_list = model.add_data_set("TestDS1", data_list, ItemModelDataSetType.List, False)
        data_set_dict = model.add_data_set("TestDS2", data_dict, ItemModelDataSetType.Dict, False)
        data_set_obj = model.add_data_set("TestDS2", data_obj, ItemModelDataSetType.Obj, False)

        model.add_column(0, "Testing List", data_set_list, 0)
        model.add_column(1, "Testing Dict", data_set_dict, "b")
        model.add_column(2, "Testing Obj", data_set_obj, "c")

        self.assertEqual(3, model.rowCount())

        self.assertEqual(data_list[0][0], model.data(model.index(0,0)))
        self.assertEqual(data_list[1][0], model.data(model.index(1,0)))
        self.assertEqual(data_list[2][0], model.data(model.index(2,0)))

        self.assertEqual(data_dict[0]["b"], model.data(model.index(0, 1)))
        self.assertEqual(data_dict[1]["b"], model.data(model.index(1, 1)))
        self.assertEqual(data_dict[2]["b"], model.data(model.index(2, 1)))

        self.assertEqual(data_obj[0].c, model.data(model.index(0, 2)))
        self.assertEqual(data_obj[1].c, model.data(model.index(1, 2)))
        self.assertEqual(data_obj[2].c, model.data(model.index(2, 2)))

    def test_managed_data_set_insert(self):
        data_list = []
        model = ExtendableItemModel()
        data_set_list = model.add_data_set("TestDS", data_list, ItemModelDataSetType.List, True)
        model.add_column(0, "Testing", data_set_list, 0)
        model.insertRow(0)
        model.insertRow(1)
        model.insertRow(2)

        self.assertEqual(3, len(data_list))
        self.assertEqual(3, model.rowCount())
        self.assertEqual(None, model.data(model.index(0, 0)))
        self.assertEqual(None, model.data(model.index(1, 0)))
        self.assertEqual(None, model.data(model.index(2, 0)))

        self.assertRaises(Exception, model.data, model.index(3, 0))
        self.assertRaises(Exception, model.data, model.index(0, 1))

    def test_managed_data_set_remove(self):
        data_list = [[5,1],[4,2],[3,3],[2,4],[1,5]]
        model = ExtendableItemModel()
        data_set_list = model.add_data_set("TestDS", data_list, ItemModelDataSetType.List, True)
        model.add_column(0, "Testing", data_set_list, 0)

        self.assertEqual(5, model.rowCount())

        model.removeRow(3)
        model.removeRow(2)
        model.removeRow(0)

        self.assertEqual(2, len(data_list))
        self.assertEqual(2, model.rowCount())

        self.assertEqual(4, model.data(model.index(0, 0)))
        self.assertEqual(1, model.data(model.index(1, 0)))

        self.assertRaises(Exception, model.data, model.index(2, 0))
        self.assertRaises(Exception, model.data, model.index(0, 1))

    def test_header_data(self):
        class Columns(IntEnum):
            a = 0
            b = 1
            c = 2

        model = ExtendableItemModel()
        data = []

        data_set = model.add_data_set("TestDS", data, ItemModelDataSetType.Dict, False)
        model.add_columns(Columns, data_set)
        model.add_column(3, "Test1", data_set, 0)
        model.add_column(4, "Test2", data_set, 0)

        self.assertEqual(5, model.columnCount())

        self.assertEqual("a", model.headerData(0, Qt.Horizontal))
        self.assertEqual("b", model.headerData(1, Qt.Horizontal))
        self.assertEqual("c", model.headerData(2, Qt.Horizontal))
        self.assertEqual("Test1", model.headerData(3, Qt.Horizontal))
        self.assertEqual("Test2", model.headerData(4, Qt.Horizontal))

if __name__ == '__main__':
    unittest.main()
