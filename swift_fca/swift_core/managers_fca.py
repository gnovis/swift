import os
import traceback
import sys
import time
from PyQt4 import QtCore
from .data_fca import (Data, DataCsv, DataArff, DataDat, DataCxt, DataData)
from .constants_fca import FileType, RunParams, ErrorMessage
from .exceptions_fca import SwiftException
from .parser_fca import parse_sequence


class ManagerFca(QtCore.QObject):
    CSV = FileType.CSV
    ARFF = FileType.ARFF
    DAT = FileType.DAT
    CXT = FileType.CXT
    DATA = FileType.DATA

    EXTENSIONS = {CSV: DataCsv,
                  ARFF: DataArff,
                  DAT: DataDat,
                  CXT: DataCxt,
                  DATA: DataData}

    # source+target -> read / don't read
    READ_DATA = {CSV+CSV: False, CSV+ARFF: True, CSV+DAT: False, CSV+CXT: True, CSV+DATA: True,
                 ARFF+ARFF: False, ARFF+DAT: False, ARFF+CXT: True, ARFF+DATA: False, ARFF+CSV: False,
                 DAT+DAT: True, DAT+CXT: True, DAT+DATA: True, DAT+CSV: True, DAT+ARFF: True,
                 CXT+CXT: False, CXT+DATA: False, CXT+CSV: False, CXT+ARFF: False, CXT+DAT: False,
                 DATA+DATA: False, DATA+CSV: False, DATA+ARFF: True, DATA+DAT: False, DATA+CXT: True}

    # Signals
    next_percent = QtCore.pyqtSignal()

    def __init__(self, source, line_count=float("inf"), skipped_lines=None):
        super().__init__()
        self._stop = False
        self._counter = None
        self._line_count = line_count
        self._source_from_stdin = not source.seekable()
        self._skipped_lines = parse_sequence(skipped_lines)

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, value):
        self._stop = value

    @property
    def line_count(self):
        return self._line_count

    @property
    def source_from_stdin(self):
        return self._source_from_stdin

    def skip_line(self, i):
        return bool(i in self._skipped_lines)

    def update_percent(self):
        self.next_percent.emit()

    def update_counter(self, line, index):
        self._counter.update(line, index)

    def get_extension(self, args):
        f = args[RunParams.SOURCE]
        if not f.seekable():
            try:
                ext = ".{}".format(args[RunParams.FORMAT])
            except KeyError:
                # same exception is raised in validator, it should be implemented only on one place
                raise SwiftException("Format Argument",
                                     "Format argument is missing.",
                                     "If you are using standart input/output as source/target, argument source/target format must be set.")
            del args[RunParams.FORMAT]
        else:
            ext = os.path.splitext(f.name)[1]
        return ext

    def get_data_class(self, args):
        return self.EXTENSIONS[self.get_extension(args)]


class Printer(ManagerFca):
    def __init__(self, kwargs, line_count=float("inf"), skipped_lines=None):
        super().__init__(kwargs[RunParams.SOURCE], line_count, skipped_lines)
        self._file_path = kwargs[RunParams.SOURCE].name
        self._data = self.get_data_class(kwargs)(**kwargs)

    def read_info(self):
        self._counter = EstimateCounter(self._file_path, self)
        self._data.get_attrs_info(self)
        self._data.get_data_info(self, read=True)

    def print_info(self, f):
        self._data.print_info(out_file=f)
        f.close()


class Browser(ManagerFca):
    def __init__(self, kwargs, line_count=20, skipped_lines=None):
        super().__init__(kwargs[RunParams.SOURCE], line_count, skipped_lines)
        self._opened_file = kwargs[RunParams.SOURCE]
        self._data = self.get_data_class(kwargs)(**kwargs)
        self._curr_line_index = -1

    def read_info(self):
        self._counter = EstimateCounter(self._opened_file.name, self)
        self._data.get_attrs_info(self)

    def __del__(self):
        self._opened_file.close()

    def get_header(self):
        return list(map(lambda x: x.name, self._data.attributes))

    def get_display_data(self, count):
        count = int(count)
        END_FILE = -1
        to_display = []

        i = 0
        while i < count:
            self._curr_line_index += 1
            line = next(self._opened_file, END_FILE)
            if line == END_FILE:
                break
            if self.skip_line(self._curr_line_index):
                continue
            prepared_line = self._data.prepare_line(line.strip(),
                                                    self._curr_line_index, False)
            if not prepared_line:  # line is comment
                continue
            to_display.append(prepared_line)
            i += 1
        return to_display

    def close_file(self):
        self._opened_file.close()


class Convertor(ManagerFca):
    """Manage data conversion"""

    def __init__(self, old, new, print_info=False, gui=False,
                 line_count=float("inf"), skipped_lines=None):
        super().__init__(old[RunParams.SOURCE], line_count, skipped_lines)
        self._gui = gui
        self._source_ext = self.get_extension(old)
        self._target_ext = self.get_extension(new)

        self._source_cls = self.EXTENSIONS[self._source_ext]
        self._target_cls = self.EXTENSIONS[self._target_ext]
        self._old_data = self._source_cls(**old)
        self._new_data = self._target_cls(**new)
        self._print_info = print_info

    @property
    def source_line_count(self):
        return self._source_line_count

    def read_info(self):
        self._counter = EstimateCounter(self._old_data.source.name, self, gui=self._gui)
        # get information from source data
        self._old_data.get_attrs_info(self)
        read_data = self.READ_DATA[self._source_ext + self._target_ext]
        self._old_data.get_data_info(self, read=read_data)
        if self._print_info:
            self._old_data.print_info()
        # this is for progress bar
        self._source_line_count = self._old_data.obj_count

    def convert(self):
        """
        Method for converting data.
        Before calling this, must be called read_info method !
        """
        if self.source_line_count == 0:
            self._counter = EstimateCounter(self._old_data.source.name, self, gui=self._gui)
        else:
            self._counter = Counter(self._source_line_count, self, gui=self._gui)

        source_file = self._old_data.source
        # write header part
        self._new_data.write_header(self._old_data)
        # skip header lines
        Data.skip_lines(self._old_data.index_data_start, source_file)
        for i, line in enumerate(source_file):
            if self.skip_line(i):
                continue
            prepared_line = self._old_data.prepare_line(line, i)
            if not prepared_line:  # line is comment
                continue
            self._new_data.write_line(prepared_line)
            if self.stop or (self.line_count-1) <= i:
                break
            self._counter.update(line, self._old_data.index_data_start)
        self._new_data.source.close()
        source_file.close()


class BgWorker(QtCore.QThread):
    def __init__(self, function, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.function = function
        self.errors = []

    def push_error(self, error):
        self.errors.append(error)

    def get_errors(self):
        return self.errors.copy()

    def run(self):
        try:
            self.function(self)
        except SwiftException as e:
            self.push_error(str(e))
        except:
            msg = ErrorMessage.UNKNOWN_ERROR + traceback.format_exc()
            self.push_error(msg)


class EstimateCounter():
    def __init__(self, data_file, manager, gui=True):
        self.gui = gui
        self.proc_line_count = 0
        self.proc_line_size_sum = 0
        self.base_line_size = sys.getsizeof("")
        self.current_percent = 0
        self.data_size = 0
        if os.path.isfile(data_file):
            self.data_size = os.path.getsize(data_file)
        self.manager = manager

    def update(self, line, index_data_start):
        self.proc_line_count += 1
        if self.proc_line_count < 10:
            curr_line_size = sys.getsizeof(line) - self.base_line_size
            self.proc_line_size_sum += curr_line_size
            average_line_size = self.proc_line_size_sum / self.proc_line_count

            # becuase of header lines
            if self.proc_line_count == 1:
                self.data_size = self.data_size - (index_data_start * average_line_size)

            average_line_count = self.data_size / average_line_size
            self.one_percent = round(average_line_count / 100)

        if self.current_percent == self.one_percent:
            self.current_percent = 0
            self.manager.update_percent()
            if self.gui:
                time.sleep(0.02)
        else:
            self.current_percent += 1


class Counter():
    def __init__(self, maximum, manager, gui=True):
        self.gui = gui
        self._current_percent = 0
        self._one_percent = round(maximum / 100)
        self.manager = manager

    def update(self, line=None, index_data_start=None):
        if self._current_percent == self._one_percent:
            self._current_percent = 0
            self.manager.update_percent()
            if self.gui:
                time.sleep(0.02)
        else:
            self._current_percent += 1
