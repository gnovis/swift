from __future__ import print_function
import os
import sys
import time
from .data_fca import (Data, DataCsv, DataArff, DataDat, DataCxt, DataData)
from .constants_fca import FileType, RunParams, App
from .parser_fca import parse_intervals
from .errors_fca import ArgError, ErrorMessage, LineError, AttrError


class Fake:
    pass


MANAGER_PARENT = Fake
if App.gui:
    from PyQt4 import QtCore
    MANAGER_PARENT = QtCore.QObject


class ManagerFca(MANAGER_PARENT):
    CSV = FileType.CSV_EXT
    ARFF = FileType.ARFF_EXT
    DAT = FileType.DAT_EXT
    CXT = FileType.CXT_EXT
    DATA = FileType.DATA_EXT

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
    if App.gui:
        next_percent = QtCore.pyqtSignal()

    def __init__(self, source, skipped_lines=None, skip_errors=False):
        super().__init__()
        self._gui = False
        self._stop = False
        self._counter = None
        self._source_from_stdin = not source.seekable()
        self._skipped_lines = parse_intervals(skipped_lines)
        self._skip_errors = skip_errors
        self._errors = []

    @property
    def gui(self):
        return self._gui

    @gui.setter
    def gui(self, value):
        self._gui = value

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, value):
        self._stop = value

    @property
    def source_from_stdin(self):
        return self._source_from_stdin

    @property
    def errors(self):
        return self._errors.copy()

    @property
    def skip_errors(self):
        return self._skip_errors

    def add_error(self, e):
        self._errors.append(str(e))

    def skip_line(self, i):
        return self._skipped_lines.val_in_closed_interval(i)

    def skip_rest_lines(self, i):
        return self._skipped_lines.val_in_open_interval(i)

    def update_percent(self):
        if App.gui:
            self.next_percent.emit()

    def update_counter(self, line, index):
        self._counter.update(line, index)

    def print_formated_errors(self):
        if self.errors:
            print("\n{}\n\n{}".format(ErrorMessage.SKIPPED_ERRORS, "\n\n".join(self.errors)), file=sys.stderr)

    @staticmethod
    def get_extension(path, args):
        if RunParams.FORMAT in args:
            ext = ".{}".format(args[RunParams.FORMAT])
        elif path == sys.stdin.name or path == sys.stdout.name:  # stream from stdin -> file extension must be set
            raise ArgError(RunParams.FORMAT)
        else:
            ext = os.path.splitext(path)[1]
        return ext

    def get_data_class(self, ext):
        try:
            return self.EXTENSIONS[ext]
        except KeyError:
            raise ArgError(message="Invalid source/target extension '{}'.\nPossible extensions are: {}".format(ext, ", ".join(FileType.ALL_REPR)))


class Printer(ManagerFca):
    def __init__(self, kwargs, skipped_lines=None, skip_errors=False, **unused):
        super().__init__(kwargs[RunParams.SOURCE], skipped_lines, skip_errors)
        self._file_path = kwargs[RunParams.SOURCE].name
        self._data = self.get_data_class(self.get_extension(kwargs[RunParams.SOURCE].name, kwargs))(**kwargs)

    def read_info(self):
        self._counter = EstimateCounter(self._file_path, self)
        self._data.get_attrs_info(self)
        self._data.get_data_info(self, read=True)

    def print_info(self, f):
        self._data.print_info(out_file=f)
        f.close()
        self.print_formated_errors()


class Browser(ManagerFca):
    def __init__(self, kwargs, skipped_lines=None, skip_errors=False, **unused):
        super().__init__(kwargs[RunParams.SOURCE], skipped_lines, skip_errors)
        self._opened_file = kwargs[RunParams.SOURCE]
        self._data = self.get_data_class(self.get_extension(kwargs[RunParams.SOURCE].name, kwargs))(**kwargs)
        self._curr_line_index = -1

    def read_info(self):
        self._counter = EstimateCounter(self._opened_file.name, self)
        self._data.get_attrs_info(self)

    def __del__(self):
        self._opened_file.close()

    def get_header(self):
        return list(map(lambda x: x.name, self._data.attributes))

    def get_display_data(self, count, print_func=None):
        count = float(count)
        END_FILE = -1
        to_display = []

        i = 0
        while i < count:
            self._curr_line_index += 1
            line = next(self._opened_file, END_FILE)

            if line == END_FILE or self.skip_rest_lines(self._curr_line_index):
                break
            if self.skip_line(self._curr_line_index):
                continue

            try:
                prepared_line = self._data.prepare_line(line.strip(), self._curr_line_index, False)
                prepared_line = list(map(lambda l: l[Data.PREPARED_VAL], prepared_line))
            except (LineError, AttrError) as e:
                if self.skip_errors:
                    self.add_error(e)
                    continue
                raise e

            if not prepared_line:  # line is comment
                continue

            if print_func:  # used for display data from stdin (stream data)
                print_func(prepared_line, self._curr_line_index)
            else:
                to_display.append(prepared_line)
            i += 1
        self.print_formated_errors()
        return to_display

    def close_file(self):
        self._opened_file.close()


class Convertor(ManagerFca):
    def __init__(self, old, new, print_info=False,
                 skipped_lines=None, skip_errors=False, **kwargs):
        super().__init__(old[RunParams.SOURCE], skipped_lines, skip_errors)
        self._source_ext = self.get_extension(old[RunParams.SOURCE].name, old)
        self._target_ext = self.get_extension(new[RunParams.TARGET].name, new)

        self._source_cls = self.get_data_class(self._source_ext)
        self._target_cls = self.get_data_class(self._target_ext)
        self._old_data = self._source_cls(**old)
        self._new_data = self._target_cls(**new)
        self._print_info = print_info

    @property
    def source_line_count(self):
        return self._source_line_count

    def read_info(self):
        self._counter = EstimateCounter(self._old_data.source.name, self, gui=self._gui)
        # get information from source data
        unpack = self._old_data.get_attrs_info(self)
        if unpack:
            self._old_data.get_data_info(self, read=True)
            self._old_data.unpack_attrs()
        else:
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
            if self.stop or self.skip_rest_lines(i):
                break
            if self.skip_line(i):
                continue
            try:
                prepared_line = self._old_data.prepare_line(line, i)
            except (LineError, AttrError) as e:
                if self.skip_errors:
                    self.add_error(e)
                    continue
                raise e
            if not prepared_line:  # line is comment
                continue
            self._new_data.write_line(prepared_line)
            self._counter.update(line, self._old_data.index_data_start)
        self._new_data.source.close()
        source_file.close()
        self.print_formated_errors()


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
