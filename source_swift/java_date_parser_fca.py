import jpype


class JavaDateParser():

    def __init__(self, pattern):
        if not jpype.isJVMStarted():
            jpype.startJVM(jpype.getDefaultJVMPath())
        self._date_format = jpype.java.text.SimpleDateFormat(pattern)

    def get_time_stamp(self, date):
        date = self._date_format.parse(date)
        return date.getTime()

    def get_format(self):
        return self._date_format.toPattern()
