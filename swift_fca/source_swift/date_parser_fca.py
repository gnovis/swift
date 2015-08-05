from datetime import datetime

"""

With this code is possible to parse java SimpleDateFormat

import jpype
class JavaDateParser():
    ISO_FORMAT = "yyyy-MM-dd'T'HH:mm:ss"

    def __init__(self, pattern):
        if not jpype.isJVMStarted():
            jpype.startJVM(jpype.getDefaultJVMPath())
        if not jpype.isThreadAttachedToJVM():
            jpype.attachThreadToJVM()
        self._date_format = jpype.java.text.SimpleDateFormat(pattern)

    def get_time_stamp(self, date):
        date = self._date_format.parse(date)
        return date.getTime()

    def get_format(self):
        return self._date_format.toPattern()

    def time_stamp_to_str(self, ts):
        return ts
"""


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
