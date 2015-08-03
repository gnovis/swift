#!/usr/bin/python3
"""
GUI application for Swift FCA
"""

import sys
import collections
import os.path
import traceback
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL
from source_swift.managers_fca import (Browser, Convertor, Printer, BgWorker)
from source_swift.constants_fca import (RunParams, FileType)
from source_swift.validator_fca import ParamValidator
import images_rc  # NOQA Resources file


class GuiSwift(QtGui.QWidget):

    SCROLL_COUNT = 50
    STATUS_MESSAGE_DURRATION = 5000

    class Colors():
        GREEN = '#c4df9b'
        RED = '#f6989d'
        WHITE = '#ffffff'

    def __init__(self):
        super().__init__()

        self._source = None
        self._target = None
        self._source_params = {}
        self._target_params = {}

        self.browser_source = None
        self.browser_target = None

        self.convert_pbar = PBarDialogStandart(self, title="Convert Data", label_text="Converting, please wait.")
        self.estimate_pbar = PBarDialogEstimate(self, title="Prepare Data", label_text="Preparing data, please wait.")

        self.initUI()

    @property
    def source(self):
        return self._source

    @property
    def target(self):
        return self._target

    @property
    def source_params(self):
        return self._source_params.copy()

    @property
    def target_params(self):
        return self._target_params.copy()

    def initUI(self):

        # Widgets
        label_source = QtGui.QLabel('Source file')
        label_target = QtGui.QLabel('Target file')

        self.line_source = QtGui.QLineEdit()
        self.line_source.setObjectName('line_source')
        self.line_target = QtGui.QLineEdit()
        self.line_target.setObjectName('line_target')
        regexp = QtCore.QRegExp('^.+\.(arff|data|dat|cxt|csv)$')
        line_validator = QtGui.QRegExpValidator(regexp)
        self.set_line_prop(self.line_source, line_validator)
        self.set_line_prop(self.line_target, line_validator)

        self.line_source.textChanged.connect(self.check_state_source)
        self.line_target.textChanged.connect(self.check_state_target)

        # Tables
        self.table_view_source = QtGui.QTableView()
        self.table_view_target = QtGui.QTableView()
        table_model_source = SwiftTableModel(self)
        table_model_target = SwiftTableModel(self)
        self.table_view_source.setModel(table_model_source)
        self.table_view_target.setModel(table_model_target)

        self.table_view_source.verticalScrollBar().valueChanged.connect(self.browse_next_source)
        self.table_view_target.verticalScrollBar().valueChanged.connect(self.browse_next_target)

        # Buttons

        btn_s_select = QtGui.QPushButton("Select")
        btn_t_select = QtGui.QPushButton("Select")
        self.btn_s_params = QtGui.QPushButton("Set Arguments")
        self.btn_t_params = QtGui.QPushButton("Set Arguments")
        self.btn_convert = QtGui.QPushButton("Convert")
        self.btn_browse = QtGui.QPushButton("Browse")
        self.btn_export_info = QtGui.QPushButton("Export Info")
        self.file_filter = "FCA files (*.arff *.cxt *.data *.dat *.csv);;All(*)"

        self.btn_export_info.clicked.connect(self.export_info)
        self.btn_s_params.clicked.connect(self.change_source_params)
        self.btn_t_params.clicked.connect(self.change_target_params)
        self.btn_t_params.setEnabled(False)
        self.btn_s_params.setEnabled(False)
        self.btn_browse.setEnabled(False)
        self.btn_export_info.setEnabled(False)
        btn_s_select.clicked.connect(self.select_source)
        btn_t_select.clicked.connect(self.select_target)
        self.btn_browse.clicked.connect(self.browse_source)
        self.btn_convert.clicked.connect(self.convert)

        # Checkbox
        self.chb_browse_convert = QtGui.QCheckBox("Browse data after convert")

        # Status Bar
        self.status_bar = QtGui.QStatusBar(self)
        self.status_bar.showMessage("Welcome in Swift FCA convertor", self.STATUS_MESSAGE_DURRATION)

        # Layout
        hbox_source = QtGui.QHBoxLayout()
        hbox_target = QtGui.QHBoxLayout()
        hbox_s_btn_set = QtGui.QHBoxLayout()
        hbox_t_btn_set = QtGui.QHBoxLayout()
        hbox_s_btn_set.setDirection(QtGui.QBoxLayout.RightToLeft)
        hbox_t_btn_set.setDirection(QtGui.QBoxLayout.RightToLeft)

        hbox_source.addWidget(self.line_source)
        hbox_source.addWidget(btn_s_select)
        hbox_target.addWidget(self.line_target)
        hbox_target.addWidget(btn_t_select)
        hbox_t_btn_set.addStretch(0)
        hbox_s_btn_set.addStretch(0)
        hbox_s_btn_set.addWidget(self.btn_convert)
        hbox_s_btn_set.addWidget(self.btn_export_info)
        hbox_s_btn_set.addWidget(self.btn_browse)
        hbox_s_btn_set.addWidget(self.btn_s_params)
        hbox_t_btn_set.addWidget(self.chb_browse_convert)
        hbox_t_btn_set.addWidget(self.btn_t_params)

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(label_source, 0, 0)
        grid.addWidget(label_target, 0, 1)
        grid.addLayout(hbox_source, 1, 0)
        grid.addLayout(hbox_target, 1, 1)
        grid.addLayout(hbox_s_btn_set, 2, 0)
        grid.addLayout(hbox_t_btn_set, 2, 1)
        grid.addWidget(self.table_view_source, 3, 0)
        grid.addWidget(self.table_view_target, 3, 1)
        grid.addWidget(self.status_bar, 4, 0, 1, 2)

        self.setLayout(grid)

        self.showMaximized()
        self.setWindowTitle('Swift - FCA convertor')
        self.setWindowIcon(QtGui.QIcon(':swift_icon.svg'))
        self.show()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    " EVENTS
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    def closeEvent(self, event):
        if self.browser_source:
            self.browser_source.close_file()
        if self.browser_target:
            self.browser_target.close_file()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    " SLOTS
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    def check_state_source(self, *args, **kwargs):
        """Slot for line_source textChanged"""
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]

        if state == QtGui.QValidator.Acceptable and os.path.isfile(sender.text()):
            color = self.Colors.GREEN
            self.browser_source = None
            self.clear_table(self.table_view_source)
            self._source_params.clear()
            self.btn_s_params.setEnabled(True)
            self.btn_browse.setEnabled(True)
            self.btn_export_info.setEnabled(True)
            self._source = sender.text()
        else:
            color = self.Colors.RED
            self.btn_s_params.setEnabled(False)
            self.btn_browse.setEnabled(False)
            self.btn_export_info.setEnabled(False)
        if sender.text() == "":
            color = self.Colors.WHITE
            self.browser_source = None
            self.clear_table(self.table_view_source)
            self._source = None
            self.btn_s_params.setEnabled(False)
            self.btn_browse.setEnabled(False)
            self.btn_export_info.setEnabled(False)
            self._source_params.clear()
        self.set_line_bg(sender, color)

    def check_state_target(self, *args, **kwargs):
        """Slot for line_target textChanged"""
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = self.Colors.GREEN
            self.browser_target = None
            self.clear_table(self.table_view_target)
            self._target_params.clear()
            self.btn_t_params.setEnabled(True)
            self._target = sender.text()
        else:
            color = self.Colors.RED
            self.btn_t_params.setEnabled(False)
        if sender.text() == "":
            self.browser_target = None
            self.clear_table(self.table_view_target)
            color = self.Colors.WHITE
            self._target = None
            self.btn_t_params.setEnabled(False)
            self._target_params.clear()
        self.set_line_bg(sender, color)

    def select_source(self):
        """Slot for btn_s_select"""
        file_name = QtGui.QFileDialog.getOpenFileName(self, "Select source file", filter=self.file_filter)
        self.line_source.setText(file_name)

    def select_target(self):
        """Slot for btn_t_select"""
        file_name = QtGui.QFileDialog.getSaveFileName(self, "Select target file", filter=self.file_filter)
        self.line_target.setText(file_name)

    def change_source_params(self):
        """Slot for btn_s_params"""
        self.change_params(SourceParamsDialog, self._source_params)

    def change_target_params(self):
        """Slot for btn_t_params"""
        self.change_params(TargetParamsDialog, self._target_params)

    def browse_source(self):
        """Slot for btn_source"""
        self.browser_source = self.browse_first_data(self.table_view_source, self.browser_source,
                                                     self.source, self.source_params)

    def browse_next_source(self, value):
        """Slot for table_view_source ValueChanged"""
        if self.table_view_source.verticalScrollBar().maximum() == value and self.browser_source:
            self.browse_data(self.browser_source, self.table_view_source)

    def browse_next_target(self, value):
        """Slot for table_view_target ValueChanged"""
        if self.table_view_target.verticalScrollBar().maximum() == value and self.browser_target:
            self.browse_data(self.browser_target, self.table_view_target)

    def update_estimate_pbar(self, line, i):
        """Slot for estimate progress bar - line_prepared"""
        self.estimate_pbar.update(line, i)

    def export_info(self):
        file_name = QtGui.QFileDialog.getSaveFileName(self, "Select file to export info about data")
        if file_name != "":

            def worker_finished(worker):
                errors = worker.get_errors()
                if len(errors) > 0:
                    self.estimate_pbar.cancel()
                    self.show_error_dialog(
                        "Print Error",
                        "Wasn't possible to prepare data for print informations, please check syntax in source file and specified parameters.",
                        errors)
                    self.status_bar.showMessage("Export infomatios about source data aborted.",
                                                self.STATUS_MESSAGE_DURRATION)

            def cont(printer):
                self.status_bar.showMessage("Informations about source data were successfully exported.",
                                            self.STATUS_MESSAGE_DURRATION)
                printer.print_info(file_name)
                self.estimate_pbar.cancel()

            try:
                printer = Printer(source=self.source, **self.source_params)
            except:
                errors = traceback.format_exc()
                self.show_error_dialog(errors=errors)
            else:
                self.estimate_pbar.setup(self.source, printer)
                printer.next_line_prepared.connect(self.update_estimate_pbar)
                # function which will be run on background

                def bg_func(worker):
                    printer.read_info()
                    worker.emit(SIGNAL('file_readed'), printer)

                bg = BgWorker(bg_func, self)
                bg.finished.connect(lambda: worker_finished(bg))
                bg.connect(bg, SIGNAL('file_readed'), cont, QtCore.Qt.QueuedConnection)
                bg.start()

    def convert(self):
        """Slot for btn_convert"""
        validator = ParamValidator(self.source, self.target, self.source_params, self.target_params)
        warnings = validator.warnings

        procces = True
        if len(warnings) > 0:
            msgBox = QtGui.QMessageBox()
            msgBox.setWindowTitle("Parameters Warning")
            msgBox.setText("Some of required parameters weren't specified correctly, conversion may crash. Do you want to continue?")
            msgBox.setInformativeText("Warnings: \n" + "\n".join(warnings))
            msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            msgBox.setDefaultButton(QtGui.QMessageBox.No)
            msgBox.setIcon(QtGui.QMessageBox.Warning)
            if msgBox.exec_() == QtGui.QMessageBox.No:
                procces = False
        if procces:
            # preparing params
            s_p = self.source_params
            s_p[RunParams.SOURCE] = self.source
            t_p = self.target_params
            t_p[RunParams.TARGET] = self.target

            # conversion
            def update_pbar():
                self.convert_pbar.update()

            def display_data(c):
                self.convert_pbar.cancel()
                self.status_bar.showMessage("Conversion was successful.",
                                            self.STATUS_MESSAGE_DURRATION)
                # display data
                if self.chb_browse_convert.isChecked():
                    self.browser_target = self.browse_first_data(self.table_view_target, self.browser_target,
                                                                 self.target, self.target_params)

            # method is called when background thread finished
            def worker_finished(worker):
                errors = worker.get_errors()
                if len(errors) > 0:
                    self.estimate_pbar.cancel()
                    self.convert_pbar.cancel()
                    self.show_error_dialog("Convert Error",
                                           "Wasn't possible to convert data, please check syntax in source file and specified parameters.",
                                           errors)
                    self.status_bar.showMessage("Conversion aborted.",
                                                self.STATUS_MESSAGE_DURRATION)

            # signal handler -> continue after thread ends
            def cont(convertor):
                self.estimate_pbar.cancel()
                self.status_bar.showMessage("Data were successfully prepared for conversion.",
                                            self.STATUS_MESSAGE_DURRATION)
                self.convert_pbar.setup(convertor.source_line_count, convertor)
                convertor.next_line_converted.connect(update_pbar)

                # function which will be run on background
                def bg_func(worker):
                    convertor.convert()
                    worker.emit(SIGNAL('file_converted'), convertor)

                bg = BgWorker(bg_func, self)
                bg.finished.connect(lambda: worker_finished(bg))
                bg.connect(bg, SIGNAL('file_converted'), display_data, QtCore.Qt.QueuedConnection)
                bg.start()

            try:
                convertor = Convertor(s_p, t_p)
            except:
                errors = traceback.format_exc()
                self.show_error_dialog(errors=[errors])
            else:
                self.estimate_pbar.setup(self.source, convertor)
                convertor.next_line_prepared.connect(self.update_estimate_pbar)

                # function which will be run on background
                def bg_func(worker):
                    convertor.read_info()
                    worker.emit(SIGNAL('file_readed'), convertor)

                bg = BgWorker(bg_func, self)
                bg.finished.connect(lambda: worker_finished(bg))
                bg.connect(bg, SIGNAL('file_readed'), cont, QtCore.Qt.QueuedConnection)
                bg.start()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    " OTHERS
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    def show_error_dialog(self, title="Arguments Error", message="Some of arguments aren't correct, operation aborted.", errors=[]):
        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle(title)
        msgBox.setText(message)
        msgBox.setStandardButtons(QtGui.QMessageBox.Close)
        msgBox.setDetailedText("\n".join(errors))
        msgBox.setIcon(QtGui.QMessageBox.Critical)
        msgBox.exec_()

    def set_line_prop(self, line, validator):
        line.setMinimumWidth(200)
        self.set_line_bg(line, '#ffffff')
        line.setValidator(validator)

    def set_line_bg(self, line, color):
        line.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def browse_data(self, browser, table_view):
        data = browser.get_display_data(self.SCROLL_COUNT)
        table_view.model().table.extend(data)
        table_view.model().layoutChanged.emit()

    def clear_table(self, table):
        table.model().table.clear()
        table.model().header.clear()
        table.model().layoutChanged.emit()

    def browse_first_data(self, table_view, browser, source_file, params):
        # clear old data
        self.clear_table(table_view)
        if browser:
            browser.close_file()

        # signal handler -> continue after thread ends
        def cont(browser, worker):
            header = browser.get_header()
            table_view.model().header.extend(header)
            self.browse_data(browser, table_view)
            self.estimate_pbar.cancel()
            self.status_bar.showMessage("Data were successfully prepared for browsing.",
                                        self.STATUS_MESSAGE_DURRATION)

        def worker_finished(worker):
            errors = worker.get_errors()
            if len(errors) > 0:
                self.estimate_pbar.cancel()
                self.clear_table(table_view)
                self.show_error_dialog("Browse Error",
                                       "Wasn't possible to browse data, please check syntax in browsing file and separator used.",
                                       errors)
                self.status_bar.showMessage("Data preparation for browsing aborted.",
                                            self.STATUS_MESSAGE_DURRATION)

        try:
            browser = Browser(source=source_file, **params)
        except:
            errors = traceback.format_exc()
            self.show_error_dialog(errors=errors)
        else:
            self.estimate_pbar.setup(source_file, browser)
            browser.next_line_prepared.connect(self.update_estimate_pbar)

            # function which will be run on background
            def bg_func(worker):
                browser.read_info()
                worker.emit(SIGNAL('file_readed'), browser, worker)

            bg = BgWorker(bg_func, self)
            bg.finished.connect(lambda: worker_finished(bg))
            bg.connect(bg, SIGNAL('file_readed'), cont, QtCore.Qt.QueuedConnection)
            bg.start()
            return browser

    def change_params(self, cls, params):
        result = cls.get_params(self)
        confirmed = result[1]
        if confirmed:
            params.clear()
            params.update(result[0])


class SwiftTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.table = []
        self.header = []
        self.parent = parent

    def rowCount(self, parent):
        return len(self.table)

    def columnCount(self, parent):
        if self.table:
            return len(self.table[0])
        return 0

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        try:
            return self.table[index.row()][index.column()]
        except IndexError:
            return None

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return col
        return None


class ParamsDialog(QtGui.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.widgets = collections.OrderedDict()
        self.params = {}

        # OK and Cancel buttons
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout = QtGui.QVBoxLayout(self)
        self.layout.addStretch(0)
        self.layout.setDirection(QtGui.QBoxLayout.BottomToTop)
        self.layout.addWidget(buttons)

    @classmethod
    def get_params(cls, parent):
        dialog = cls(parent)
        result = dialog.exec_()
        return (dialog.get_dict_data(), result == QtGui.QDialog.Accepted)

    def get_dict_data(self):
        result = {}
        for name, w in self.widgets.items():
            if w.data() != w.default_val and w.data() != w.NONE_VAL:
                result[name] = w.data()
        return result

    def fill_layout(self, suff):
        poss_args = self.format_poss_args[suff]
        filtered = collections.OrderedDict()
        for name, w in self.widgets.items():
            if name in poss_args:
                self.layout.addWidget(w)
                filtered[name] = w
        self.widgets = filtered

    def fill_widgets(self):
        for name, w in self.widgets.items():
            if name in self.params:
                w.set_data(self.params[name])

    def showEvent(self, event):
        self.fill_widgets()


class SourceParamsDialog(ParamsDialog):

    NO_PARAMS = 'no_params'
    format_poss_args = {FileType.ARFF: (RunParams.SOURCE_SEP),
                        FileType.CSV: (RunParams.SOURCE_SEP, RunParams.NFL, RunParams.SOURCE_ATTRS),
                        FileType.CXT: (NO_PARAMS),
                        FileType.DAT: (NO_PARAMS),
                        FileType.DATA: (RunParams.SOURCE_SEP)}

    def __init__(self, parent):
        super().__init__(parent)
        self.params = parent.source_params
        # form lines
        self.line_separator = FormLine("Separator", default_val=',')
        self.line_str_attrs = FormLine("Attributes")
        # check box
        self.cb_nfl = FormCheckBox('Attributes on first line')

        # layout
        self.widgets[RunParams.NFL] = self.cb_nfl
        self.widgets[RunParams.SOURCE_ATTRS] = self.line_str_attrs
        self.widgets[RunParams.SOURCE_SEP] = self.line_separator
        self.widgets[self.NO_PARAMS] = FormLabel("No paramteres can be set.")

        suffix = os.path.splitext(parent.source)[1]  # source file must be set!
        self.fill_layout(suffix)
        self.setWindowTitle('Parameters for source file')


class TargetParamsDialog(ParamsDialog):

    format_poss_args = {FileType.ARFF: (RunParams.TARGET_ATTRS, RunParams.TARGET_SEP),
                        FileType.CSV: (RunParams.TARGET_ATTRS, RunParams.TARGET_SEP),
                        FileType.CXT: (RunParams.TARGET_ATTRS, RunParams.TARGET_OBJECTS),
                        FileType.DAT: (RunParams.TARGET_ATTRS),
                        FileType.DATA: (RunParams.TARGET_ATTRS, RunParams.CLASSES, RunParams.TARGET_SEP)}

    def __init__(self, parent):
        super().__init__(parent)
        self.params = parent.target_params
        # form lines
        self.line_separator = FormLine("Separator", default_val=',')
        self.line_str_attrs = FormLine("Attributes")
        self.line_str_objects = FormLine("Objects")
        self.line_rel_name = FormLine("Relation Name")
        self.line_classes = FormLine("Classes")
        # layout
        self.widgets[RunParams.CLASSES] = self.line_classes
        self.widgets[RunParams.TARGET_SEP] = self.line_separator
        self.widgets[RunParams.TARGET_OBJECTS] = self.line_str_objects
        self.widgets[RunParams.TARGET_ATTRS] = self.line_str_attrs
        self.widgets[RunParams.RELATION_NAME] = self.line_rel_name
        suffix = os.path.splitext(parent.target)[1]
        self.fill_layout(suffix)
        self.setWindowTitle('Parameters for target file')


class FormWidget(QtGui.QWidget):
    NONE_VAL = ''

    def __init__(self, parent=None, default_val=NONE_VAL):
        super().__init__(parent)
        self._default_val = default_val

    @property
    def default_val(self):
        return self._default_val

    def data(self):
        return self.NONE_VAL

    def set_data(self):
        pass


class FormCheckBox(FormWidget):
    def __init__(self, label, parent=None, default_val=QtCore.Qt.Checked):
        super().__init__(parent, default_val)
        self.cb = QtGui.QCheckBox(label, self)
        self.cb.toggle()
        self.cb.setChecked(default_val)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.cb)
        layout.setContentsMargins(6, 0, 0, 10)
        self.setLayout(layout)

    def data(self):
        return not bool(self.cb.checkState())

    def set_data(self, data):
        if data:
            self.cb.setChecked(QtCore.Qt.Unchecked)


class FormLine(FormWidget):
    def __init__(self, label, parent=None, default_val=FormWidget.NONE_VAL):
        super().__init__(parent, default_val)

        self.label = QtGui.QLabel(label)
        self.line = QtGui.QLineEdit()
        self.line.setText(default_val)
        self.line.setMinimumWidth(350)
        self.line.setStyleSheet('QLineEdit { background-color: %s }' % '#ffffff')
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.line)
        self.setLayout(layout)

    def data(self):
        return self.line.text()

    def set_data(self, data):
        self.line.setText(data)


class FormLabel(FormWidget):
    def __init__(self, text, parent=None, default_val=FormWidget.NONE_VAL):
        super().__init__(parent, default_val)
        self.label = QtGui.QLabel(text, self)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)


class PBarDialog(QtGui.QProgressDialog):
    def __init__(self, parent, label_text="", title=""):
        super().__init__(parent)
        self.parent = parent
        self.setLabelText(label_text)
        self.setWindowTitle(title)
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.setMinimum(1)
        self.setMaximum(100)
        self.canceled.connect(self.canceled_by_user)

    def canceled_by_user(self):
        self.parent.status_bar.showMessage("Operation canceled by user.",
                                           self.parent.STATUS_MESSAGE_DURRATION)
        self.manager.stop = True
        self.cancel()

    def setup(self, manager):
        self.manager = manager
        self.show()

    def update(self, *args):
        raise NotImplementedError('update method must be implemented in child class')


class PBarDialogStandart(PBarDialog):

    def setup(self, maximum, manager):
        self._current_percent = 0
        self._one_percent = round(maximum / 100)
        super().setup(manager)

    def update(self):
        if self._current_percent == self._one_percent:
            self._current_percent = 0
            self.setValue(self.value() + 1)
        else:
            self._current_percent += 1


class PBarDialogEstimate(PBarDialog):

    def setup(self, data_file, manager):
        self.proc_line_count = 0
        self.proc_line_size_sum = 0
        self.base_line_size = sys.getsizeof("")
        self.current_percent = 0
        self.data_size = os.path.getsize(data_file)
        super().setup(manager)

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
            self.setValue(self.value() + 1)
        else:
            self.current_percent += 1


def main():
    app = QtGui.QApplication(sys.argv)
    sw = GuiSwift()  # NOQA
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
