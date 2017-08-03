import datetime
import unittest

from Models.Tymbox.TymboxModel import TymboxModel, TymboxEvent, TymboxTaskTimePreference, TymboxModelColumns


class TestTymboxModel(unittest.TestCase):
    def test_construct(self):
        model = TymboxModel()

    def test_insert_tasks(self):
        model = TymboxModel()

        midnight = datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        model.set_start_time(int(midnight))
        model.set_duration(180)

        event = TymboxEvent()
        event.name = "Test Task"
        event.duration = 30

        # These are sequential traits, handled from the sequential model
        event.time_preference = TymboxTaskTimePreference.preferred
        event.preference_value = midnight + 60*60*1

        # Explicitly set schedules
        event.start_time = midnight + 60*60*1
        event.end_time   = midnight + 60*60*1 + 60*30

        model.insert_task(0, event)

        self.assertEqual(1, model.rowCount())

        event = TymboxEvent()
        event.name = "Test Task 2"
        event.duration = 45

        # These are sequential traits, handled from the sequential model
        event.time_preference = TymboxTaskTimePreference.preferred
        event.preference_value = midnight + 60 * 60 * 2

        # Explicitly set schedules
        event.start_time = midnight + 60 * 60 * 2
        event.end_time = midnight + 60 * 60 * 2 + 60 * 45
        model.insert_task(1, event)

        self.assertEqual(2, model.rowCount())

        self.assertEqual(midnight + 60*60*1, model.data(model.index(0, TymboxModelColumns.start_time)))
        self.assertEqual(midnight + 60*60*2, model.data(model.index(1, TymboxModelColumns.start_time)))

        self.assertEqual(30, model.data(model.index(0, TymboxModelColumns.duration)))
        self.assertEqual(45, model.data(model.index(1, TymboxModelColumns.duration)))

        model.remove_task(0)

        self.assertEqual(1, model.rowCount())
        self.assertEqual(midnight + 60 * 60 * 2, model.data(model.index(0, TymboxModelColumns.start_time)))
        self.assertEqual(45, model.data(model.index(0, TymboxModelColumns.duration)))

if __name__ == '__main__':
    unittest.main()
