from enum import IntEnum, unique

import math
from PyQt5.QtCore import QModelIndex, pyqtSlot
from PyQt5.QtCore import Qt

from Models.ExtendableItemModel import ItemModelDataSetType, ItemModelDataSet
from Models.Tymbox.TymboxModel import TymboxModel, TymboxModelColumnsCount, TymboxModelColumns, \
    TymboxTaskTimePreference, TymboxEvent


class SequentialTiming(object):
    def __init__(self):
        self.earliest_start = 0
        self.latest_end = 0

@unique
class SequentialTymboxModelColumns(IntEnum):
    earliest_start  = TymboxModelColumnsCount
    latest_end      = earliest_start + 1

class SequentialTymboxModel(TymboxModel):
    def __init__(self, parent=None):
        TymboxModel.__init__(self, parent)
        self.setObjectName("SequentialTymboxModel")
        self.timing_data = []

        self.dataChanged.connect(self.on_dataChanged)
        self.rowsInserted.connect(self.on_rowInserted)
        self.rowsRemoved.connect(self.on_rowRemoved)

        # Figure this design flaw out later
        # Goal is to have the object name for the model set before it logs column additions
        self._register_columns()

    def _register_columns(self):
        TymboxModel._register_columns(self)

        data_set = self.add_data_set("SequentialModelDS", self.timing_data, ItemModelDataSetType.Obj, True)
        self.add_columns(SequentialTymboxModelColumns, data_set)

        self.set_column_formatter(SequentialTymboxModelColumns.earliest_start, self._time_formatter)
        self.set_column_formatter(SequentialTymboxModelColumns.latest_end, self._time_formatter)

    # Pre-calculations
    def calculate_earliest_start(self, pos) -> int:
        if pos > 0:
            previous_task = self.tasks[pos-1]
            if previous_task.time_preference in [TymboxTaskTimePreference.preferred, TymboxTaskTimePreference.sequential]:
                # Min duration 15m, move onto previous event
                return self.calculate_earliest_start(pos-1) + 15*60
            elif previous_task.time_preference == TymboxTaskTimePreference.duration:
                # Min duration of n, move onto previous event
                return self.calculate_earliest_start(pos-1) + previous_task.duration
            elif previous_task.time_preference == TymboxTaskTimePreference.start_at:
                # Eat duration
                return previous_task.start_time + 15*60
            elif previous_task.time_preference == TymboxTaskTimePreference.end_no_later:
                # Use preferred time
                return previous_task.end_time
            return self.tasks[pos-1].end_time
        else:
            return self.start_time

    def calculate_latest_end(self, pos) -> int:
        if pos+1 < self.rowCount():
            event = self.get_event(pos+1)
            if event.time_preference == TymboxTaskTimePreference.preferred:
                return self.calculate_latest_end(pos+1)-15*60
            else:
                return self.tasks[pos+1].start_time
        else:
            return self.start_time + self.duration

    # Aligning the model
    def get_next_overlapping_event(self, row) -> (TymboxEvent, SequentialTiming):
        if row+1 < len(self.tasks):
            event = self.get_event(row)
            next_event = self.get_event(row+1)
            if event.end_time > next_event.start_time:
                return next_event, self.timing_data[row+1]
        return None, None

    def get_previous_overlapping_event(self, row: int) -> (TymboxEvent, SequentialTiming):
        if row > 0:
            event = self.get_event(row)
            previous_event = self.get_event(row-1)
            if previous_event.end_time > event.start_time:
                return previous_event, self.timing_data[row-1]
        return None, None

    def alter_event_start_time(self, row: int, amount_s: int) -> int:
        event = self.get_event(row)

        if amount_s < 0:
            if (event.start_time + amount_s) < self.timing_data[row].earliest_start:
                amount_s = self.timing_data[row].earliest_start - event.start_time
        elif amount_s > 0:
            if (event.end_time + amount_s) > self.timing_data[row].latest_end:
                amount_s = self.timing_data[row].latest_end - event.end_time

        if amount_s != 0:
            new_start_time = event.start_time + amount_s
            new_end_time = event.end_time + amount_s

            self.setData(self.index(row, TymboxModelColumns.end_time), new_end_time, Qt.EditRole)
            self.setData(self.index(row, TymboxModelColumns.start_time), new_start_time, Qt.EditRole)

            return new_start_time

        return event.start_time

    def alter_event_duration(self, row, amount_s):
        event = self.get_event(row)
        new_end_time = event.end_time + amount_s
        assert((new_end_time - event.start_time) >= 15*60)
        if new_end_time > self.timing_data[row].latest_end:
            new_end_time = self.timing_data[row].latest_end

        if event.end_time != new_end_time:
            self.setData(self.index(row, TymboxModelColumns.end_time), new_end_time)

    def bring_to_preferred_start(self, row):
        """ Moves a task towards its preferred start time """

        event = self.get_event(row)

        original_distance_to_preferred = distance_to_preferred = event.preference_value - event.start_time

        if distance_to_preferred < 0:
            previous_event = self.get_event(row - 1) if row > 0 else None
            next_start = previous_event.end_time if previous_event is not None else self.start_time
            max_distance = next_start - event.start_time
            if distance_to_preferred < max_distance:
                distance_to_preferred = max_distance
        else:
            next_event = self.get_event(row + 1) if row + 1 < self.rowCount() else None
            next_end = next_event.start_time if next_event is not None else self.start_time + self.duration
            max_distance = next_end - event.end_time
            if distance_to_preferred > max_distance:
                distance_to_preferred = max_distance

        self.log_debug("Bring to preferred start",
                       row_number = row,
                       event_preferred_start_time = event.preference_value,
                       event_start_time = event.start_time,
                       original_distance_to_preferred = original_distance_to_preferred,
                       distance_to_preferred = distance_to_preferred,
                       max_distance=max_distance)

        if distance_to_preferred != 0:
            self.alter_event_start_time(row, distance_to_preferred)

    def construct_data_source(self, data_set: ItemModelDataSet, pos: int) -> object:
        if data_set.id == "SequentialModelDS":
            self.log_debug("Constructing sequential timing data source")
            return SequentialTiming()
        return TymboxModel.construct_data_source(self, data_set, pos)


    def __end_time_changed(self, row):
        if row + 1 < self.rowCount():
            # The next event will need a recalculated end time
            self.setData(self.index(row + 1, SequentialTymboxModelColumns.earliest_start),
                         self.calculate_earliest_start(row + 1))

            self.log_debug("Calculated earliest start time for row",
                           row=row + 1,
                           earliest_start=self.timing_data[row + 1].earliest_start)

            previous_end_time = self.get_previous_value(self.index(row, TymboxModelColumns.end_time))
            event = self.get_event(row)

            if previous_end_time is not None and event.end_time <= previous_end_time:
                # There could be space between this task and the next
                # Try bring the next task to it's preferred times
                next_event = self.get_event(row + 1)
                if next_event.time_preference == TymboxTaskTimePreference.preferred:
                    if next_event.start_time > next_event.preference_value:
                        self.bring_to_preferred_start(row + 1)
                return

            self.log_debug("End time increased, checking for overlap",
                           end_time=event.end_time,
                           previous_end_time=previous_end_time)

            overlapping_event, overlapping_timing_data = self.get_next_overlapping_event(row)

            # If the task has extended it could be overlapping the next task
            if overlapping_event is not None:
                self.log_info(event.name, "is overlapping next", overlapping_event.name, "by",
                      event.end_time - overlapping_event.start_time)
                # TODO next task preferred times
                self.alter_event_start_time(row + 1, event.end_time - overlapping_event.start_time)

    def __start_time_changed(self, row):
        if row > 0:
            # The previous event will need a recalculated end time
            self.setData(self.index(row - 1, SequentialTymboxModelColumns.latest_end),
                         self.calculate_latest_end(row - 1))

            self.log_debug("Calculated latest end time for row",
                           row=row - 1,
                           latest_end=self.timing_data[row - 1].latest_end)

            previous_start_time = self.get_previous_value(self.index(row, TymboxModelColumns.start_time))
            event = self.get_event(row)

            if previous_start_time is not None and event.start_time >= previous_start_time:
                # There could be space between this task and the previous
                # Try bring the previous task to it's preferred times
                previous_event = self.get_event(row - 1)
                if previous_event.time_preference == TymboxTaskTimePreference.preferred:
                    if previous_event.start_time < previous_event.preference_value:
                        self.bring_to_preferred_start(row - 1)
                return

            self.log_debug("Start time decreased, checking for overlap",
                           start_time=event.start_time,
                           previous_start_time=previous_start_time)

            overlapping_event, overlapping_timing_data = self.get_previous_overlapping_event(row)

            # If the task has been moved ahead it could be overlapping the previous task
            if overlapping_event is not None:

                self.log_info(event.name, "is overlapping previous", overlapping_event.name, "by",
                      overlapping_event.end_time - event.start_time)
                overlap_s = event.start_time - overlapping_event.end_time

                if overlapping_event.time_preference == TymboxTaskTimePreference.preferred:
                    # Previous overlapping event is cool to move around, try moving it ahead of time
                    if overlapping_event.start_time + overlap_s >= overlapping_timing_data.earliest_start:
                        self.alter_event_start_time(row - 1, overlap_s)
                    # Have to shorten its duration
                    elif overlapping_event.duration + overlap_s >= 15*60:
                        self.alter_event_duration(row - 1, overlap_s)
                    else:
                        raise ValueError("Irrecoverable overlapping event")

                elif overlapping_event.time_preference == TymboxTaskTimePreference.start_at:
                    # Can only try shortening the duration
                    if overlapping_event.duration + overlap_s >= 15*60:
                        self.alter_event_duration(row - 1, overlap_s)
                    else:
                        raise ValueError("Irrecoverable overlapping event")

                elif overlapping_event.time_preference == TymboxTaskTimePreference.fixed:
                    raise ValueError("Irrecoverable overlapping event")


    #@pyqtSlot(QModelIndex, QModelIndex)
    def on_dataChanged(self, top_left: QModelIndex, bottom_right: QModelIndex, roles = None):
        """ Ensures sequential order
            Recalculates earliest/latest times
            Moves surrounding events towards their preferred times"""

        if roles is None or Qt.EditRole in roles:
            for row in range(top_left.row(), bottom_right.row()+1):
                for column in range(top_left.column(), bottom_right.column()+1):
                    if column == TymboxModelColumns.end_time:
                        self.__end_time_changed(row)
                    elif column == TymboxModelColumns.start_time:
                        self.__start_time_changed(row)

    @pyqtSlot(QModelIndex, int, int)
    def on_rowInserted(self, parent: QModelIndex, first: int, last: int):
        for i in range(first, last+1):
            self.timing_data[i].earliest_start = self.calculate_earliest_start(i)
            self.timing_data[i].latest_end = self.calculate_latest_end(i)
            print("Calculated timing data for row", i, "earliest start:", self.timing_data[i].earliest_start, "latest end:", self.timing_data[i].latest_end)

        for i in range(first-1, -1, -1):
            self.timing_data[i].latest_end = self.calculate_latest_end(i)
            print("Calculated timing data for row", i, "earliest start:", self.timing_data[i].earliest_start,
                  "latest end:", self.timing_data[i].latest_end)

        for i in range(last+1, self.rowCount()):
            self.timing_data[i].earliest_start = self.calculate_earliest_start(i)
            print("Calculated timing data for row", i, "earliest start:", self.timing_data[i].earliest_start,
                  "latest end:", self.timing_data[i].latest_end)

    @pyqtSlot(QModelIndex, int, int)
    def on_rowRemoved(self, parent: QModelIndex, first: int, last: int):
        if self.rowCount() > 0:
            for i in range(first-1, -1, -1):
                self.timing_data[i].latest_end = self.calculate_latest_end(i)
                print("Calculated timing data for row", i, "latest start:", self.timing_data[i].earliest_start,
                      "latest end:", self.timing_data[i].latest_end)

            for i in range(last, self.rowCount()):
                self.timing_data[i].earliest_start = self.calculate_earliest_start(i)
                print("Calculated timing data for row", i, "earliest start:", self.timing_data[i].earliest_start,
                      "latest end:", self.timing_data[i].latest_end)