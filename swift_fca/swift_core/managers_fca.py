import os
import traceback
import sys
import time
from PyQt4 import QtCore
from .data_fca import (Data, DataCsv, DataArff, DataDat, DataCxt, DataData)
from .constants_fca import (FileType, RunParams)


class ManagerFca(QtCore.QObject):
    EXTENSIONS = {FileType.CSV: DataCsv,
                  FileType.ARFF: DataArff,
                  FileType.DAT: DataDat,
                  FileType.CXT: DataCxt,
                  FileType.DATA: DataData}
    # Signals
    next_percent = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self._stop = False
        self._counter = None

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, value):
        self._stop = value

    def get_data_class(self, file_path):
        return self.EXTENSIONS[os.path.splitext(file_path)[1]]

    def update_percent(self):
        self.next_percent.emit()

    def update_counter(self, line, index):
        self._counter.update(line, index)


class Printer(ManagerFca):
    def __init__(self, **kwargs):
        super().__init__()
        self._file_path = kwargs[RunParams.SOURCE].name
        self._data = self.get_data_class(self._file_path)(**kwargs)

    def read_info(self):
        self._counter = EstimateCounter(self._file_path, self)
        self._data.get_attrs_info(self._data.get_header_info)
        self._data.get_data_info(self)

    def print_info(self, file_path):
        with open(file_path, "w") as f:
            self._data.print_info(out_file=f)


class Browser(ManagerFca):
    def __init__(self, **kwargs):
        super().__init__()
        self._opened_file = kwargs[RunParams.SOURCE]
        self._data = self.get_data_class(self._opened_file.name)(**kwargs)

    def read_info(self):
        self._counter = EstimateCounter(self._opened_file.name, self)
        self._data.get_attrs_info(self._data.get_header_info)
        self._data.get_data_info_for_browse(self)

    def __del__(self):
        self._opened_file.close()

    def get_header(self):
        return list(map(lambda x: x.name, self._data.attributes))

    def get_display_data(self, count):
        END_FILE = -1
        to_display = []
        for i in range(count):
            line = next(self._opened_file, END_FILE)
            if line == END_FILE:
                break
            else:
                prepared_line = self._data.prepare_line(line, False)
                if not prepared_line:  # line is comment
                    continue
                to_display.append(prepared_line)
        return to_display

    def close_file(self):
        self._opened_file.close()


class Convertor(ManagerFca):
    """Manage data conversion"""

    next_percent_converted = QtCore.pyqtSignal()

    def __init__(self, old, new, print_info=False, gui=False):
        super().__init__()
        self._gui = gui
        self._source_cls = self.get_data_class(old)
        self._target_cls = self.get_data_class(new)
        self._scaling = self.is_scaling()
        self._old_data = self._source_cls(**old)
        self._new_data = self._target_cls(**new)
        self._print_info = print_info

    def get_data_class(self, args):
        f = args['source']
        if not f.seekable():
            suff = '.' + args['format']
            del args['format']
        else:
            suff = os.path.splitext(f.name)[1]
        return self.EXTENSIONS[suff]

    @property
    def source_line_count(self):
        return self._source_line_count

    def update_convert_counter(self):
        self._counter.update()

    def update_percent_converted(self):
        self.next_percent_converted.emit()

    def is_scaling(self):
        if (self._source_cls == DataCsv or
            self._source_cls == DataArff or
            self._source_cls == DataData) and (self._target_cls == DataDat or
                                               self._target_cls == DataCxt):
            return True
        return False

    def read_info(self):
        self._counter = EstimateCounter(self._old_data.source.name, self, gui=self._gui)
        # get information from source data
        self._old_data.get_attrs_info(self._old_data.get_header_info)
        self._old_data.get_data_info(self)
        if self._print_info:
            self._old_data.print_info()
        # this is for progress bar
        self._source_line_count = self._old_data.obj_count
        # check if should scale

    def convert(self):
        """
        Method for converting data.
        Before calling this, must be called read_info method !
        """

        self._counter = Counter(self._source_line_count, self, gui=self._gui)

        source_file = self._old_data.source
        # write header part
        self._new_data.write_header(self._old_data)
        # skip header lines
        Data.skip_lines(self._old_data.index_data_start, source_file)
        for i, line in enumerate(source_file):
            prepared_line = self._old_data.prepare_line(line)
            if not prepared_line:  # line is comment
                continue
            self._new_data.write_line(prepared_line)
            if self.stop:
                break
            self.update_convert_counter()
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
        except:
            self.push_error(traceback.format_exc())


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

    def update(self):
        if self._current_percent == self._one_percent:
            self._current_percent = 0
            self.manager.update_percent_converted()
            if self.gui:
                time.sleep(0.01)
        else:
            self._current_percent += 1
