import os
import traceback
from PyQt4 import QtCore
from source_swift.data_fca import (Data, DataCsv, DataArff, DataDat, DataCxt, DataData)
from source_swift.constants_fca import (FileType, RunParams)


class ManagerFca(QtCore.QObject):
    EXTENSIONS = {FileType.CSV: DataCsv,
                  FileType.ARFF: DataArff,
                  FileType.DAT: DataDat,
                  FileType.CXT: DataCxt,
                  FileType.DATA: DataData}

    def __init__(self):
        super().__init__()
        self._stop = False

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, value):
        self._stop = value

    def get_data_class(self, file_path):
        return self.EXTENSIONS[os.path.splitext(file_path)[1]]


class Browser(ManagerFca):

    next_line_prepared = QtCore.pyqtSignal(str, int)

    def __init__(self, **kwargs):
        super().__init__()
        file_path = kwargs[RunParams.SOURCE]
        self._data = self.get_data_class(file_path)(**kwargs)
        self._opened_file = open(file_path, "r")

    def read_info(self):
        self._data.get_header_info()
        self._data.get_data_info_for_browse(self)
        Data.skip_lines(self._data.index_data_start, self._opened_file)

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
                to_display.append(self._data.prepare_line(line))
        return to_display

    def close_file(self):
        self._opened_file.close()


class Convertor(ManagerFca):
    """Manage data conversion"""

    next_line_converted = QtCore.pyqtSignal()
    next_line_prepared = QtCore.pyqtSignal(str, int)

    def __init__(self, old, new, print_info=False):
        super().__init__()
        # suffixes of input files
        self._source_cls = self.get_data_class(old['source'])
        self._target_cls = self.get_data_class(new['source'])

        # create data file object according suffix
        self._old_data = self._source_cls(**old)
        self._new_data = self._target_cls(**new)
        self._print_info = print_info

    @property
    def source_line_count(self):
        return self._source_line_count

    def read_info(self):
        # get information from source data
        self._old_data.get_header_info()
        self._old_data.get_data_info(self)
        if self._print_info:
            self._old_data.print_info()
        # this is for progress bar
        self._source_line_count = self._old_data.obj_count
        # check if should scale

    def convert(self):
        """Call this method to convert data"""
        self._scaling = False
        if (self._source_cls == DataCsv or
            self._source_cls == DataArff or
            self._source_cls == DataData) and (self._target_cls == DataDat or
                                               self._target_cls == DataCxt):
            self._scaling = True
            self._new_data.parse_old_attrs_for_scale(self._old_data.str_attrs,
                                                     self._old_data.separator)
            self._new_data.parse_new_attrs_for_scale()

        target_file = open(self._new_data.source, 'w')
        # write header part
        self._new_data.write_header(target_file, old_data=self._old_data)
        with open(self._old_data.source, 'r') as f:
            # skip header lines
            Data.skip_lines(self._old_data.index_data_start, f)
            for i, line in enumerate(f):
                prepared_line = self._old_data.prepare_line(line)
                if self._scaling:
                    self._new_data.write_data_scale(prepared_line,
                                                    target_file)
                else:
                    self._new_data.write_line(prepared_line,
                                              target_file)
                if self.stop:
                    break
                self.next_line_converted.emit()
        target_file.close()


class BgWorker(QtCore.QThread):
    def __init__(self, function, mw):
        super(BgWorker, self).__init__(mw)
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
