"""
GUI application for Swift FCA
"""

import sys
import collections
import os.path
import traceback
import itertools
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL
from .swift_core.managers_fca import Browser, Convertor, Printer, BgWorker
from .swift_core.constants_fca import RunParams, FileType, ShortCuts
from .swift_core.validator_fca import ConvertValidator
from .swift_core.errors_fca import ErrorMessage
import swift_fca.resources.resources_rc  # NOQA Resources file


class GuiSwift(QtGui.QWidget):
    STATUS_MESSAGE_DURRATION = 5000
    SCROLL_COUNT = 50

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

    def scroll_count(self):
        return self.SCROLL_COUNT

    def initUI(self):

        st_find = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+f"), self)
        st_find.activated.connect(lambda: FindDialog(self))

        def move_splitter_right():
            sizes = self.splitter.sizes()
            self.splitter.setSizes([sizes[0]+10, sizes[1]-10])

        def move_splitter_left():
            sizes = self.splitter.sizes()
            self.splitter.setSizes([sizes[0]-10, sizes[1]+10])

        st_move_splitter_right = QtGui.QShortcut(QtGui.QKeySequence("Alt+Right"), self)
        st_move_splitter_right.activated.connect(move_splitter_right)

        st_move_splitter_left = QtGui.QShortcut(QtGui.QKeySequence("Alt+Left"), self)
        st_move_splitter_left.activated.connect(move_splitter_left)

        # Widgets
        label_source = QtGui.QLabel('<b>Source File</b>')
        label_target = QtGui.QLabel('<b>Target File</b>')

        self.line_source = QtGui.QLineEdit()
        self.line_source.setObjectName('line_source')
        self.line_target = QtGui.QLineEdit()
        self.line_target.setObjectName('line_target')
        regexp_ext = QtCore.QRegExp('^.+\.(arff|data|names|dat|cxt|csv)$')
        regexp_all = QtCore.QRegExp('^.+$')
        self.line_ext_validator = QtGui.QRegExpValidator(regexp_ext)
        self.line_all_validator = QtGui.QRegExpValidator(regexp_all)
        self.set_line_prop(self.line_source, self.line_ext_validator)
        self.set_line_prop(self.line_target, self.line_ext_validator)

        self.line_source.textChanged.connect(self.check_state_source)
        self.line_target.textChanged.connect(self.check_state_target)

        st_source_focus = QtGui.QShortcut(QtGui.QKeySequence("Alt+s"), self)
        st_source_focus.activated.connect(self.line_source.setFocus)
        st_target_focus = QtGui.QShortcut(QtGui.QKeySequence("Alt+t"), self)
        st_target_focus.activated.connect(self.line_target.setFocus)

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
        self.btn_s_params = QtGui.QPushButton("Settings")
        self.btn_t_params = QtGui.QPushButton("Settings")
        self.btn_browse = QtGui.QPushButton("Browse")
        self.btn_export_info = QtGui.QPushButton("Export Info")
        self.btn_s_orig_data = QtGui.QPushButton("Original data")
        self.btn_t_orig_data = QtGui.QPushButton("Original data")

        self.btn_convert = QtGui.QPushButton("Convert")
        self.btn_convert.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        f = QtGui.QFont()
        f.setBold(True)
        f.setPointSize(12)
        self.btn_convert.setFont(f)

        self.file_filter = "FCA files (*.arff *.cxt *.data *.names *.dat *.csv);;All(*)"

        open_orig = lambda path: OriginalDataDialog(path, self)

        self.convert_shortcut = QtGui.QShortcut(QtGui.QKeySequence(ShortCuts.CONVERT), self.btn_convert, self.convert)
        self.select_source_shortcut = QtGui.QShortcut(QtGui.QKeySequence(ShortCuts.SOURCE_FILE), btn_s_select, self.select_source)
        self.select_target_shortcut = QtGui.QShortcut(QtGui.QKeySequence(ShortCuts.TARGET_FILE), btn_t_select, self.select_target)
        self.source_settings_shortcut = QtGui.QShortcut(QtGui.QKeySequence(ShortCuts.SOURCE_SETTINGS), self.btn_s_params, self.change_source_params)
        self.target_settings_shortcut = QtGui.QShortcut(QtGui.QKeySequence(ShortCuts.TARGET_SETTINGS), self.btn_t_params, self.change_target_params)
        self.source_origin_shortcut = QtGui.QShortcut(QtGui.QKeySequence(ShortCuts.SOURCE_ORIG_DATA), self.btn_s_orig_data, lambda: open_orig(self._source))
        self.target_origin_shortcut = QtGui.QShortcut(QtGui.QKeySequence(ShortCuts.TARGET_ORIG_DATA), self.btn_t_orig_data, lambda: open_orig(self._target))
        self.browse_shortcut = QtGui.QShortcut(QtGui.QKeySequence(ShortCuts.BROWSE), self.btn_browse, self.browse_source)
        self.export_shortcut = QtGui.QShortcut(QtGui.QKeySequence(ShortCuts.EXPORT), self.btn_export_info, self.export_info)

        # Buttons tool-tip
        tooltip_format = "({})\n{}"
        btn_s_select.setToolTip(
            tooltip_format.format(ShortCuts.SOURCE_FILE,
                                  "Select existing data file in one of the format: ARFF, DATA, CSV, DAT, CXT"))
        btn_t_select.setToolTip(
            tooltip_format.format(ShortCuts.TARGET_FILE,
                                  ("Select name for new data file, supported formats: " +
                                   "ARFF, DATA, CSV, DAT, CXT.\nThis file will be created or rewrited by converted data.")))

        self.btn_s_orig_data.setToolTip(
            tooltip_format.format(ShortCuts.SOURCE_ORIG_DATA,
                                  "Display original source data."))
        self.btn_t_orig_data.setToolTip(
            tooltip_format.format(ShortCuts.TARGET_ORIG_DATA,
                                  "Display original target data."))

        self.btn_s_params.setToolTip(
            tooltip_format.format(ShortCuts.SOURCE_SETTINGS,
                                  "Set arguments which will be used for Source Data in selected operation."))

        self.btn_t_params.setToolTip(
            tooltip_format.format(ShortCuts.TARGET_SETTINGS,
                                  "Set arguments which will be used for Target Data in conversion."))

        self.btn_browse.setToolTip(
            tooltip_format.format(ShortCuts.BROWSE,
                                  "Display and browse Source Data"))

        self.btn_export_info.setToolTip(
            tooltip_format.format(ShortCuts.EXPORT,
                                  "Select file for export informations about Source Data"))

        self.btn_convert.setToolTip(
            tooltip_format.format(ShortCuts.CONVERT,
                                  "Convert Source Data to Target Data"))

        self.btn_export_info.clicked.connect(self.export_info)
        self.btn_s_params.clicked.connect(self.change_source_params)
        self.btn_t_params.clicked.connect(self.change_target_params)
        self.btn_browse.setEnabled(False)
        self.btn_export_info.setEnabled(False)
        self.btn_convert.setEnabled(False)
        self.btn_s_orig_data.setEnabled(False)
        self.btn_t_orig_data.setEnabled(False)
        self.btn_s_params.setEnabled(False)
        self.btn_t_params.setEnabled(False)
        btn_s_select.clicked.connect(self.select_source)
        btn_t_select.clicked.connect(self.select_target)
        self.btn_browse.clicked.connect(self.browse_source)
        self.btn_convert.clicked.connect(self.convert)
        self.btn_s_orig_data.clicked.connect(lambda: open_orig(self._source))
        self.btn_t_orig_data.clicked.connect(lambda: open_orig(self._target))

        # Checkbox
        self.chb_browse_convert = QtGui.QCheckBox("Browse data after convert")
        self.chb_browse_convert.setChecked(True)

        # Status Bar
        self.status_bar = QtGui.QStatusBar(self)
        self.status_bar.showMessage("Welcome in Swift FCA Converter", self.STATUS_MESSAGE_DURRATION)

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
        hbox_s_btn_set.addWidget(self.btn_export_info)
        hbox_s_btn_set.addWidget(self.btn_browse)
        hbox_s_btn_set.addWidget(self.btn_s_orig_data)
        hbox_s_btn_set.addWidget(self.btn_s_params)
        hbox_t_btn_set.addWidget(self.chb_browse_convert)
        hbox_t_btn_set.addWidget(self.btn_t_orig_data)
        hbox_t_btn_set.addWidget(self.btn_t_params)

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
        grid.setRowStretch(3, 1)

        grid.addWidget(label_source, 0, 0)
        grid.addWidget(label_target, 0, 3)
        grid.addLayout(hbox_source, 1, 0)
        grid.addLayout(hbox_target, 1, 3)
        grid.addWidget(self.btn_convert, 1, 1, 2, 2)
        grid.addLayout(hbox_s_btn_set, 2, 0)
        grid.addLayout(hbox_t_btn_set, 2, 3)

        self.splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.setHandleWidth(15)
        self.splitter.addWidget(self.table_view_source)
        self.splitter.addWidget(self.table_view_target)
        grid.addWidget(self.splitter, 3, 0, 1, 4)

        grid.addWidget(self.status_bar, 4, 0, 1, 2)

        self.setLayout(grid)

        self.showMaximized()
        self.setWindowTitle('Swift - FCA Converter')
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
            self.reset_table(self.table_view_source)
            self.btn_browse.setEnabled(True)
            self.btn_export_info.setEnabled(True)
            self.btn_s_orig_data.setEnabled(True)
            self._source = sender.text()
        else:
            color = self.Colors.RED
            self.btn_browse.setEnabled(False)
            self.btn_export_info.setEnabled(False)
            self.btn_s_orig_data.setEnabled(False)
            self.browser_source = None
            self.reset_table(self.table_view_source)
            self._source = None
        if sender.text() == "":
            color = self.Colors.WHITE
            self._source_params.clear()
            self.btn_s_params.setEnabled(False)
        else:
            self.btn_s_params.setEnabled(True)
        self.set_line_bg(sender, color)
        self.btn_convert.setEnabled(self.can_convert())

    def check_state_target(self, *args, **kwargs):
        """Slot for line_target textChanged"""
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = self.Colors.GREEN
            self.browser_target = None
            self.reset_table(self.table_view_target)
            if os.path.isfile(sender.text()):
                self.btn_t_orig_data.setEnabled(True)
            else:
                self.btn_t_orig_data.setEnabled(False)
            self._target = sender.text()
        else:
            color = self.Colors.RED
            self.btn_t_orig_data.setEnabled(False)
            self.browser_target = None
            self.reset_table(self.table_view_target)
            self._target = None
        if sender.text() == "":
            color = self.Colors.WHITE
            self._target_params.clear()
            self.btn_t_params.setEnabled(False)
        else:
            self.btn_t_params.setEnabled(True)
        self.set_line_bg(sender, color)
        self.btn_convert.setEnabled(self.can_convert())

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
        self.change_params(SourceParamsDialog, self._source_params, self.line_source)

    def change_target_params(self):
        """Slot for btn_t_params"""
        self.change_params(TargetParamsDialog, self._target_params, self.line_target)

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

    def export_info(self):
        file_name = QtGui.QFileDialog.getSaveFileName(self, "Select file to export info about data")
        if file_name != "":

            def worker_finished(worker, pbar):
                errors = worker.get_errors()
                if len(errors) > 0:
                    pbar.cancel()
                    self.show_dialog(
                        "Print Error",
                        "Wasn't possible to prepare data for print informations, please check syntax in source file and specified arguments.",
                        errors=errors)
                    self.status_bar.showMessage("Export infomatios about source data aborted.",
                                                self.STATUS_MESSAGE_DURRATION)

            def cont(printer, pbar):
                if not printer.stop:
                    self.status_bar.showMessage("Informations about source data were successfully exported to {}".format(file_name),
                                                self.STATUS_MESSAGE_DURRATION)
                    printer.print_info(open(file_name, 'w'))
                    pbar.cancel()
                if printer.errors:
                    self.show_dialog(ErrorMessage.SKIPPED_ERRORS_HEADER, ErrorMessage.SKIPPED_ERRORS, printer.errors, QtGui.QMessageBox.Information)

            try:
                main_args = self.source_params
                main_args[RunParams.SOURCE] = open(self.subst_ext(self.source), 'r')
                printer = Printer(main_args, **self.source_params)
            except:
                errors = traceback.format_exc()
                self.show_dialog(errors=[errors])
            else:
                pbar = self.get_prepare_pbar(printer)
                printer.next_percent.connect(pbar.update)

                def bg_func(worker):
                    """function which will be run on background"""
                    printer.read_info()
                    worker.emit(SIGNAL('file_readed'), printer, pbar)

                bg = BgWorker(bg_func)
                bg.finished.connect(lambda: worker_finished(bg, pbar))
                bg.connect(bg, SIGNAL('file_readed'), cont, QtCore.Qt.QueuedConnection)
                bg.start()

    def convert(self):
        """Slot for btn_convert"""
        validator = ConvertValidator(self.source, self.target, self.source_params, self.target_params)
        warnings = validator.warnings

        procces = True
        if len(warnings) > 0:
            msgBox = QtGui.QMessageBox()
            msgBox.setWindowTitle("Arguments Warning")
            msgBox.setText("{} Do you want to continue?".format(ErrorMessage.MISSING_ARGS_ERROR))
            msgBox.setInformativeText("Warnings: \n" + "\n".join(warnings))
            msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            msgBox.setDefaultButton(QtGui.QMessageBox.No)
            msgBox.setIcon(QtGui.QMessageBox.Warning)
            if msgBox.exec_() == QtGui.QMessageBox.No:
                procces = False
        if procces:
            # preparing params
            s_p = self.source_params
            s_p[RunParams.SOURCE] = open(self.subst_ext(self.source), 'r')
            t_p = self.target_params
            t_p[RunParams.TARGET] = open(self.subst_ext(self.target), 'w')

            # conversion

            def display_data(convertor, pbar):
                if not convertor.stop:
                    self.btn_t_orig_data.setEnabled(True)
                    pbar.cancel()
                    self.status_bar.showMessage("Conversion was successful.",
                                                self.STATUS_MESSAGE_DURRATION)
                    # display data
                    if self.chb_browse_convert.isChecked():
                        self.browser_target = self.browse_first_data(self.table_view_target, self.browser_target,
                                                                     self.target, self.target_params)
                if convertor.errors:
                    self.show_dialog(ErrorMessage.SKIPPED_ERRORS_HEADER, ErrorMessage.SKIPPED_ERRORS, convertor.errors, QtGui.QMessageBox.Information)

            # method is called when background thread finished
            def worker_finished(worker, pbar):
                errors = worker.get_errors()
                if len(errors) > 0:
                    pbar.cancel()
                    self.show_dialog("Convert Error",
                                     "Wasn't possible to convert data, please check syntax in source file and specified arguments.",
                                     errors=errors)
                    self.status_bar.showMessage("Conversion aborted.",
                                                self.STATUS_MESSAGE_DURRATION)

            # signal handler -> continue after thread ends
            def cont(convertor, pbar):
                if not convertor.stop:
                    pbar.cancel()
                    self.status_bar.showMessage("Data were successfully prepared for conversion.",
                                                self.STATUS_MESSAGE_DURRATION)
                    pbar_convert = PBarDialog(self, convertor, title="Convert Data", label_text="Converting, please wait.")
                    convertor.next_percent.disconnect()
                    convertor.next_percent.connect(pbar_convert.update)

                    # function which will be run on background
                    def bg_func(worker):
                        convertor.convert()
                        worker.emit(SIGNAL('file_converted'), convertor, pbar_convert)

                    self.bg_worker = BgWorker(bg_func)
                    self.bg_worker.finished.connect(lambda: worker_finished(self.bg_worker, pbar_convert))
                    self.bg_worker.connect(self.bg_worker, SIGNAL('file_converted'), display_data, QtCore.Qt.QueuedConnection)
                    self.bg_worker.start()

            try:
                convertor = Convertor(s_p, t_p, gui=True, **self.source_params)
            except:
                errors = traceback.format_exc()
                self.show_dialog(errors=[errors])
            else:
                pbar = self.get_prepare_pbar(convertor)
                convertor.next_percent.connect(pbar.update)

                # function which will be run on background
                def bg_func(worker):
                    convertor.read_info()
                    worker.emit(SIGNAL('file_readed'), convertor, pbar)

                bg = BgWorker(bg_func)
                bg.finished.connect(lambda: worker_finished(bg, pbar))
                bg.connect(bg, SIGNAL('file_readed'), cont, QtCore.Qt.QueuedConnection)
                bg.start()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    " OTHERS
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

    @staticmethod
    def subst_ext(path):
        root, ext = os.path.splitext(path)
        if ext == FileType.NAMES_EXT:
            path = root + FileType.DATA_EXT
        return path

    def get_prepare_pbar(self, convertor):
        return PBarDialog(self, convertor, title="Prepare Data", label_text="Preparing data, please wait.")

    def can_convert(self):
        return bool(self.source and self.target)

    def show_dialog(self, title="Arguments Error", message="Some of arguments aren't correct, operation aborted.",
                    errors=[], icon=QtGui.QMessageBox.Critical):
        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle(title)
        msgBox.setText(message)
        msgBox.setStandardButtons(QtGui.QMessageBox.Close)
        msgBox.setDetailedText("\n".join(errors))
        msgBox.setIcon(icon)
        msgBox.exec_()

    def set_line_prop(self, line, validator, min_w=200):
        line.setMinimumWidth(min_w)
        self.set_line_bg(line, '#ffffff')
        line.setValidator(validator)

    def set_line_bg(self, line, color):
        line.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def browse_data(self, browser, table_view):
        data = browser.get_display_data(self.scroll_count())
        table_view.model().table.extend(data)
        table_view.model().layoutChanged.emit()
        if browser.errors:
            self.show_dialog(ErrorMessage.SKIPPED_ERRORS_HEADER, ErrorMessage.SKIPPED_ERRORS, browser.errors, QtGui.QMessageBox.Information)

    def reset_table(self, table):
        table_model = SwiftTableModel(self)
        table.setModel(table_model)

    def browse_first_data(self, table_view, browser, source_file, params):
        # clear old data
        self.reset_table(table_view)
        if browser:
            browser.close_file()

        # signal handler -> continue after thread ends
        def cont(browser, pbar):
            if not browser.stop:
                header = browser.get_header()
                table_view.model().header.extend(header)
                self.browse_data(browser, table_view)

                pbar.cancel()
                self.status_bar.showMessage("Data were successfully prepared for browsing.",
                                            self.STATUS_MESSAGE_DURRATION)

        def worker_finished(worker, pbar):
            errors = worker.get_errors()
            if len(errors) > 0:
                pbar.cancel()
                self.reset_table(table_view)
                self.show_dialog("Browse Error",
                                 "Wasn't possible to browse data, please check syntax in browsing file and separator used.",
                                 errors=errors)
                self.status_bar.showMessage("Data preparation for browsing aborted.",
                                            self.STATUS_MESSAGE_DURRATION)

        try:
            main_args = params
            main_args[RunParams.SOURCE] = open(self.subst_ext(source_file), 'r')
            browser = Browser(main_args, **params)
        except:
            errors = traceback.format_exc()
            self.show_dialog(errors=[errors])
        else:
            pbar = self.get_prepare_pbar(browser)
            browser.next_percent.connect(pbar.update)

            # function which will be run on background
            def bg_func(worker):
                browser.read_info()
                worker.emit(SIGNAL('file_readed'), browser, pbar)

            bg = BgWorker(bg_func)
            bg.finished.connect(lambda: worker_finished(bg, pbar))
            bg.connect(bg, SIGNAL('file_readed'), cont, QtCore.Qt.QueuedConnection)
            bg.start()
            return browser

    def change_params(self, cls, params, line):
        result = cls.get_params(self)
        confirmed = result[1]
        if confirmed:
            params.clear()
            params.update(result[0])

            def set_validator(validator):
                line.setValidator(validator)
                # refresh
                line.textChanged.emit(line.text())

            if RunParams.FORMAT in params:
                set_validator(self.line_all_validator)
            else:
                set_validator(self.line_ext_validator)


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


class RadioButton(QtGui.QRadioButton):
    def __init__(self, text, ident, parent=None):
        super().__init__(text, parent=parent)
        self._ident = ident

    @property
    def ident(self):
        return self._ident


class FindDialog(QtGui.QDialog):
    SOURCE_TABLE = 1
    TARGET_TABLE = 2

    def __init__(self, parent):
        super().__init__(parent)
        self.tables = {self.SOURCE_TABLE: parent.table_view_source,
                       self.TARGET_TABLE: parent.table_view_target}
        self.curr_table = self.tables[self.SOURCE_TABLE]
        self.occurences = itertools.cycle([])
        self.occur_count = 0

        btn_find = QtGui.QPushButton("Find")
        btn_close = QtGui.QPushButton("Close")
        self.btn_next = QtGui.QPushButton("Next")
        self.btn_next.setEnabled(False)
        btn_find.clicked.connect(self.find)
        self.btn_next.clicked.connect(self.next)
        buttons = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        buttons.addButton(btn_find, QtGui.QDialogButtonBox.ActionRole)
        buttons.addButton(self.btn_next, QtGui.QDialogButtonBox.ActionRole)
        buttons.addButton(btn_close, QtGui.QDialogButtonBox.ActionRole)
        btn_close.clicked.connect(self.reject)

        radio_btn_source = RadioButton("Source Table", self.SOURCE_TABLE)
        radio_btn_source.setChecked(True)
        radio_btn_target = RadioButton("Target Table", self.TARGET_TABLE)
        btn_group = QtGui.QButtonGroup(self)
        btn_group.addButton(radio_btn_source)
        btn_group.addButton(radio_btn_target)
        btn_group.buttonClicked.connect(self.change_table)
        radio_hbox = QtGui.QHBoxLayout()
        radio_hbox.addWidget(radio_btn_source)
        radio_hbox.addWidget(radio_btn_target)

        self.line = QtGui.QLineEdit()
        self.line.setStyleSheet('QLineEdit { background-color: %s }' % '#ffffff')
        self.line.setMinimumWidth(350)

        self.msg = QtGui.QLabel("")

        vbox = QtGui.QVBoxLayout(self)
        vbox.addLayout(radio_hbox)
        vbox.addWidget(self.line)
        vbox.addWidget(self.msg)
        vbox.addWidget(buttons)
        vbox.addStretch(0)
        self.setWindowModality(QtCore.Qt.NonModal)
        self.setWindowTitle("Find in table")

        self.show()

    def find(self):
        self.curr_table.selectionModel().clearSelection()
        search_val = self.line.text()
        result = []
        no = 0
        for row_i, row in enumerate(self.curr_table.model().table):
            for col_i, col in enumerate(row):
                if col == search_val:
                    no += 1
                    result.append([no, [row_i, col_i]])
        if result:
            self.occurences = itertools.cycle(result)
            self.occur_count = no
            self.next()
            self.btn_next.setEnabled(True)
        else:
            self.msg.setText("Phrase not found")
            self.btn_next.setEnabled(False)

    def next(self):
        EMPTY = None
        occur = next(self.occurences, EMPTY)
        if occur:
            no, match = occur
            ind = self.curr_table.model().index(*match)
            self.curr_table.selectionModel().select(ind, QtGui.QItemSelectionModel.Select)
            self.curr_table.scrollTo(ind, QtGui.QAbstractItemView.PositionAtCenter)
            self.msg.setText("{} of {} matches".format(no, self.occur_count))

    def change_table(self, btn):
        self.curr_table = self.tables[btn.ident]


class ParamsDialog(QtGui.QDialog):
    NO_PARAMS = 'no_params'

    def __init__(self, parent):
        super().__init__(parent)
        self.widgets = collections.OrderedDict()
        self.widgets_selected = collections.OrderedDict()
        self.params = {}

        # OK and Cancel buttons
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.main_layout = QtGui.QVBoxLayout(self)
        self.main_layout.addStretch(0)
        self.main_layout.setDirection(QtGui.QBoxLayout.BottomToTop)
        self.main_layout.addWidget(buttons)
        self.layout = QtGui.QVBoxLayout()
        self.main_layout.addLayout(self.layout)

        # combobox
        self.combo_format = FormComboBox("Format", items=FileType.ALL_REPR)
        self.combo_format.combo.activated.connect(self.refresh_layout)
        self.widgets[RunParams.FORMAT] = self.combo_format

    @classmethod
    def get_params(cls, parent):
        dialog = cls(parent)
        result = dialog.exec_()
        return (dialog.get_dict_data(), result == QtGui.QDialog.Accepted)

    def get_dict_data(self):
        result = {}
        for name, w in self.widgets_selected.items():
            if w.data() != w.default_val and w.data() != w.NONE_VAL:
                result[name] = w.data()
        return result

    def refresh_layout(self, ext):
        for name, w in self.widgets.items():
            w.hide()
        if RunParams.FORMAT in self.params:
            del self.params[RunParams.FORMAT]
        if ext:
            self.params[RunParams.FORMAT] = FileType.ALL_REPR[ext-1]
        self.filter_widgets()

    def filter_widgets(self, path=""):
        try:
            if RunParams.FORMAT in self.params:
                suff = ".{}".format(self.params[RunParams.FORMAT])
            else:
                suff = os.path.splitext(path)[1]
            poss_args = self.format_poss_args[suff]
        except (AttributeError, KeyError):
            for name, w in self.widgets.items():
                w.show()
            return
        self.widgets_selected.clear()
        for name, w in self.widgets.items():
            if name in poss_args:
                w.show()
                self.widgets_selected[name] = w

    def fill_layout(self, path):
        for name, w in self.widgets.items():
            w.hide()
            self.layout.addWidget(w)
        self.filter_widgets(path)

    def fill_widgets(self):
        for name, w in self.widgets.items():
            if name in self.params:
                w.set_data(self.params[name])

    def showEvent(self, event):
        self.fill_widgets()


class TextView(QtGui.QFrame):
    class NumberBar(QtGui.QWidget):

        def __init__(self, edit):
            super().__init__(edit)

            self.edit = edit
            self.adjustWidth(1)

        def paintEvent(self, event):
            self.edit.numberbarPaint(self, event)
            QtGui.QWidget.paintEvent(self, event)

        def adjustWidth(self, count):
            width = self.fontMetrics().width(str(count)) + 10
            if self.width() != width:
                self.setFixedWidth(width)

        def updateContents(self, rect, scroll):
            if scroll:
                self.scroll(0, scroll)
            else:
                self.update()

    class PlainTextEdit(QtGui.QPlainTextEdit):

        def __init__(self, *args):
            QtGui.QPlainTextEdit.__init__(self, *args)

            self.setFrameStyle(QtGui.QFrame.NoFrame)

            self.setFrameStyle(QtGui.QFrame.NoFrame)
            self.highlight()
            self.setLineWrapMode(QtGui.QPlainTextEdit.NoWrap)

            self.cursorPositionChanged.connect(self.highlight)

        def highlight(self):
            hi_selection = QtGui.QTextEdit.ExtraSelection()
            hi_selection.format.setBackground(self.palette().alternateBase())
            hi_selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, QtCore.QVariant)
            hi_selection.cursor = self.textCursor()
            hi_selection.cursor.select(QtGui.QTextCursor.LineUnderCursor)
            self.setExtraSelections([hi_selection])

        def numberbarPaint(self, number_bar, event):
            font_metrics = self.fontMetrics()
            current_line = self.document().findBlock(self.textCursor().position()).blockNumber() + 1

            block = self.firstVisibleBlock()
            line_count = block.blockNumber()
            painter = QtGui.QPainter(number_bar)
            painter.fillRect(event.rect(), self.palette().base())

            # Iterate over all visible text blocks in the document.
            while block.isValid():
                line_count += 1
                block_top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()

                # Check if the position of the block is out side of the visible
                # area.
                if not block.isVisible() or block_top == event.rect().bottom():
                    break

                # We want the line number for the selected line to be bold.
                if line_count == current_line:
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)

                # Draw the line number left justified at the position of the line.
                paint_rect = QtCore.QRect(-5, block_top, number_bar.width(), font_metrics.height())
                painter.drawText(paint_rect, QtCore.Qt.AlignRight, str(line_count))

                block = block.next()

            painter.end()

    def __init__(self, *args):
        QtGui.QFrame.__init__(self, *args)

        self.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)

        self.edit = self.PlainTextEdit()
        self.number_bar = self.NumberBar(self.edit)

        hbox = QtGui.QHBoxLayout(self)
        hbox.setSpacing(5)
        hbox.setMargin(5)
        hbox.addWidget(self.number_bar)
        hbox.addWidget(self.edit)

        self.edit.blockCountChanged.connect(self.number_bar.adjustWidth)
        self.edit.updateRequest.connect(self.number_bar.updateContents)

    def getEdit(self):
        return self.edit


class OriginalDataDialog(QtGui.QDialog):
    def __init__(self, source_path, parent):
        super().__init__(parent)
        self.source_path = source_path
        self.load_count = parent.scroll_count()

        self.init_ui()

        self.source = source_path
        self.source = open(source_path, 'r')
        self.data_view.setPlainText(self.load_next(self.load_count))
        self.show()

    def init_ui(self):
        vbox = QtGui.QVBoxLayout(self)
        textw = TextView()
        self.data_view = textw.getEdit()
        self.data_view.setReadOnly(True)
        self.data_view.verticalScrollBar().valueChanged.connect(self.fill_next)
        vbox.addWidget(textw)
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Close, QtCore.Qt.Horizontal, self)
        buttons.rejected.connect(self.reject)

        self.line = QtGui.QLineEdit()
        self.line.setStyleSheet('QLineEdit { background-color: %s }' % '#ffffff')
        btn_find = QtGui.QPushButton("Find")
        btn_find.clicked.connect(self.find)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.line)
        hbox.addWidget(btn_find)
        hbox.addWidget(buttons)
        vbox.addLayout(hbox)

        self.resize(700, 400)
        self.setWindowTitle(self.source_path)
        self.setWindowModality(QtCore.Qt.NonModal)

    def find(self):
        self.data_view.find(self.line.text())

    def reject(self):
        self.source.close()
        super().reject()

    def fill_next(self, value):
        if self.data_view.verticalScrollBar().maximum() == value:
            new_rows = self.load_next(self.load_count)
            if new_rows:
                self.data_view.moveCursor(QtGui.QTextCursor.End)
                self.data_view.insertPlainText("\n{}".format(new_rows))

    def load_next(self, count):
        new_rows = ""
        for i, line in enumerate(self.source):
            new_rows += line
            if i == count:
                break
        return new_rows.strip()


class SourceParamsDialog(ParamsDialog):
    format_poss_args = {FileType.ARFF_EXT: (RunParams.FORMAT, RunParams.SOURCE_ATTRS, RunParams.SOURCE_SEP, RunParams.SKIPPED_LINES, RunParams.SKIP_ERRORS),
                        FileType.CSV_EXT: (RunParams.FORMAT, RunParams.SOURCE_SEP, RunParams.NFL,
                                           RunParams.SOURCE_ATTRS, RunParams.SKIPPED_LINES, RunParams.SKIP_ERRORS),
                        FileType.CXT_EXT: (RunParams.FORMAT, RunParams.SOURCE_ATTRS, RunParams.SKIPPED_LINES, RunParams.SKIP_ERRORS),
                        FileType.DAT_EXT: (RunParams.FORMAT, RunParams.SOURCE_ATTRS, RunParams.SKIPPED_LINES, RunParams.SKIP_ERRORS, RunParams.SOURCE_SEP),
                        FileType.DATA_EXT: (RunParams.FORMAT, RunParams.SOURCE_ATTRS, RunParams.SOURCE_SEP, RunParams.SKIPPED_LINES, RunParams.SKIP_ERRORS),
                        FileType.NAMES_EXT: (RunParams.FORMAT, RunParams.SOURCE_ATTRS, RunParams.SOURCE_SEP, RunParams.SKIPPED_LINES, RunParams.SKIP_ERRORS)}

    def __init__(self, parent):
        super().__init__(parent)
        self.params = parent.source_params
        # form lines
        seqregex = QtCore.QRegExp('^(\d+|(\d+)?-\d+)(,(\d+|(\d+)?-\d+))*$')
        seq_validator = QtGui.QRegExpValidator(seqregex)

        self.skip_lines = FormLine("Skip Lines", validator=seq_validator)
        self.line_separator = FormLine("Separator", default_val=',')
        self.line_str_attrs = FormLine("Attributes")
        # checkbox
        self.cb_nfl = FormCheckBox('Attributes on first line')
        self.cb_skip_errors = FormCheckBox('Skip Errors', default_val=QtCore.Qt.Unchecked)

        # layout
        self.widgets[RunParams.SOURCE_ATTRS] = self.line_str_attrs
        self.widgets[RunParams.SOURCE_SEP] = self.line_separator
        self.widgets[RunParams.SKIPPED_LINES] = self.skip_lines
        self.widgets[RunParams.SKIP_ERRORS] = self.cb_skip_errors
        self.widgets[RunParams.NFL] = self.cb_nfl

        self.fill_layout(parent.source)
        self.setWindowTitle('Arguments for source file')


class TargetParamsDialog(ParamsDialog):
    format_poss_args = {FileType.ARFF_EXT: (RunParams.FORMAT, RunParams.TARGET_SEP, RunParams.RELATION_NAME),
                        FileType.CSV_EXT: (RunParams.FORMAT, RunParams.TARGET_SEP, RunParams.NFL),
                        FileType.CXT_EXT: (RunParams.FORMAT, RunParams.TARGET_OBJECTS, RunParams.RELATION_NAME),
                        FileType.DAT_EXT: (RunParams.FORMAT),
                        FileType.DATA_EXT: (RunParams.FORMAT, RunParams.CLASSES, RunParams.TARGET_SEP),
                        FileType.NAMES_EXT: (RunParams.FORMAT, RunParams.CLASSES, RunParams.TARGET_SEP)}

    def __init__(self, parent):
        super().__init__(parent)
        self.params = parent.target_params
        self.line_separator = FormLine("Separator", default_val=',')
        self.line_str_objects = FormLine("Objects")
        self.line_rel_name = FormLine("Relation Name")
        self.line_classes = FormLine("Classes")
        self.cb_nfl = FormCheckBox('Attributes on first line')
        # placeholders
        self.line_str_objects.setPlaceholderText("obj1_name, obj2_name, obj3_name")
        self.line_classes.setPlaceholderText("cls1_name, cls2_name, cls3_name")
        # layout
        self.widgets[RunParams.CLASSES] = self.line_classes
        self.widgets[RunParams.TARGET_SEP] = self.line_separator
        self.widgets[RunParams.TARGET_OBJECTS] = self.line_str_objects
        self.widgets[RunParams.RELATION_NAME] = self.line_rel_name
        self.widgets[RunParams.NFL] = self.cb_nfl
        # self.widgets[self.NO_PARAMS] = FormLabel("No arguments can be set.")

        self.fill_layout(parent.target)
        self.setWindowTitle('Arguments for target file')


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

    def set_data(self, data):
        pass


class FormComboBox(FormWidget):
    def __init__(self, label, items=[], parent=None, default_val="---"):
        super().__init__(parent, default_val)
        self.label = QtGui.QLabel(label)
        self.combo = QtGui.QComboBox()
        self.combo.addItem(default_val)
        self.combo.addItems(items)
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
        self.setLayout(layout)

    def data(self):
        return self.combo.currentText()

    def set_data(self, data):
        index = self.combo.findText(data)
        self.combo.setCurrentIndex(index)


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
        return bool(self.cb.checkState())

    def set_data(self, data):
        self.cb.setChecked(data)


class FormLine(FormWidget):
    def __init__(self, label, parent=None, default_val=FormWidget.NONE_VAL, validator=None):
        super().__init__(parent, default_val)
        self.label = QtGui.QLabel(label)
        self.line = QtGui.QLineEdit()
        self.line.setValidator(validator)
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

    def setPlaceholderText(self, text):
        self.line.setPlaceholderText(text)


class FormLabel(FormWidget):
    def __init__(self, text, parent=None, default_val=FormWidget.NONE_VAL):
        super().__init__(parent, default_val)
        self.label = QtGui.QLabel(text, self)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)


class PBarDialog(QtGui.QProgressDialog):
    def __init__(self, parent, manager, label_text="", title=""):
        super().__init__(parent)
        self.parent = parent
        self.manager = manager
        self.setLabelText(label_text)
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setMinimumHeight(120)
        self.setWindowModality(QtCore.Qt.NonModal)
        self.canceled.connect(self.canceled_by_user)
        self.show()

    def canceled_by_user(self):
        self.parent.status_bar.showMessage("Operation canceled by user.",
                                           self.parent.STATUS_MESSAGE_DURRATION)
        self.manager.stop = True
        self.cancel()

    def update(self, *args):
        self.setValue(self.value() + 1)


def main():
    app = QtGui.QApplication(sys.argv)
    sw = GuiSwift()  # NOQA
    sys.exit(app.exec_())
