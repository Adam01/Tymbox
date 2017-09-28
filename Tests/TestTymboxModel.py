import datetime
import unittest
from PyQt5.QtCore import Qt

from Models.Tymbox.TymboxModel import TymboxModel, TymboxEvent, TymboxTaskTimePreference, TymboxModelColumns
from Utils.LogHelper import LogLevel


class TestTymboxModel(unittest.TestCase):
    def test_construct(self):
        model = TymboxModel()
        model._register_columns()

    def test_insert_tasks(self):
        model = TymboxModel()
        model.set_log_level(LogLevel.ExtraDebug)
        model._register_columns()

        midnight = int(datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        model.set_start_time(midnight)
        model.set_duration(3*60*60)

        model.insert_task("Test Task", midnight + 60*60*1, 60*30, TymboxTaskTimePreference.preferred, midnight+60*60*1)

        self.assertEqual(1, model.rowCount())

        model.insert_task("Test Task 2", midnight + 60*60*2, 60 * 45, TymboxTaskTimePreference.preferred, midnight + 60 * 60 * 2)

        self.assertEqual(2, model.rowCount())

        self.assertEqual(midnight + 60*60*1, model.data(model.index(0, TymboxModelColumns.start_time), Qt.EditRole))
        self.assertEqual(midnight + 60*60*2, model.data(model.index(1, TymboxModelColumns.start_time), Qt.EditRole))

        self.assertEqual(midnight + 60*60*1 + 60*30, model.data(model.index(0, TymboxModelColumns.end_time), Qt.EditRole))
        self.assertEqual(midnight + 60 * 60 * 2 + 60 * 45, model.data(model.index(1, TymboxModelColumns.end_time), Qt.EditRole))

        model.remove_task(0)

        self.assertEqual(1, model.rowCount())
        self.assertEqual(midnight + 60 * 60 * 2, model.data(model.index(0, TymboxModelColumns.start_time), Qt.EditRole))
        self.assertEqual(midnight + 60 * 60 * 2 + 60 * 45, model.data(model.index(0, TymboxModelColumns.end_time), Qt.EditRole))

if __name__ == '__main__':
    unittest.main()
