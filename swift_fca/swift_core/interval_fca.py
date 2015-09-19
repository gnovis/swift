from math import isinf


class Interval:

    def __init__(self, val_from, val_to):
        self._val_from = float(val_from)
        self._val_to = float(val_to)

    def __contains__(self, value):
        return bool(self._val_from <= float(value) <= self._val_to)

    def __str__(self):
        return "{}-{}".format(self._val_from, self._val_to)

    def is_open(self):
        return bool(isinf(self._val_to))


class Intervals:

    def __init__(self, intervals):
        self._open_intervals = []
        self._closed_intervals = []
        for i in intervals:
            if i.is_open():
                self._open_intervals.append(i)
            else:
                self._closed_intervals.append(i)

    def val_in_open_interval(self, value):
        return self.val_in(self._open_intervals, value)

    def val_in_closed_interval(self, value):
        return self.val_in(self._closed_intervals, value)

    def val_in(self, intervals, value):
        for interval in intervals:
            if value in interval:
                return True
        return False
