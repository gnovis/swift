from datetime import datetime


class DateParser():

    ISO_FORMAT = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, pattern):
        self._pattern = pattern

    def get_time_stamp(self, date):
        date = datetime.strptime(date, self._pattern)
        return date.timestamp()

    def get_format(self):
        return self._pattern

    def time_stamp_to_str(self, ts):
        return datetime.fromtimestamp(ts).strftime(self._pattern)
