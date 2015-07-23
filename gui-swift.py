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
from source_swift.managers_fca import (Browser, Convertor, BgWorker)
from source_swift.constants_fca import (RunParams, FileType)
from source_swift.validator_fca import ParamValidator


class GuiSwift(QtGui.QWidget):

    SCROLL_COUNT = 50

    def __init__(self):
        super(GuiSwift, self).__init__()

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

        def set_btn_size(btn):
            btn.setSizePolicy(QtGui.QSizePolicy.Fixed,
                              QtGui.QSizePolicy.Fixed)

        btn_s_select = QtGui.QPushButton("Select")
        btn_t_select = QtGui.QPushButton("Select")
        self.btn_s_params = QtGui.QPushButton("Set Params")
        self.btn_t_params = QtGui.QPushButton("Set Params")
        self.btn_convert = QtGui.QPushButton("Convert")
        self.btn_browse = QtGui.QPushButton("Browse")
        self.file_filter = "FCA files (*.arff *.cxt *.data *.dat *.csv);;All(*)"
        set_btn_size(self.btn_t_params)
        set_btn_size(self.btn_s_params)
        set_btn_size(self.btn_convert)
        set_btn_size(self.btn_browse)

        self.btn_s_params.clicked.connect(self.change_source_params)
        self.btn_t_params.clicked.connect(self.change_target_params)
        self.btn_t_params.setEnabled(False)
        self.btn_s_params.setEnabled(False)
        self.btn_browse.setEnabled(False)
        btn_s_select.clicked.connect(self.select_source)
        btn_t_select.clicked.connect(self.select_target)
        self.btn_browse.clicked.connect(self.browse_source)
        self.btn_convert.clicked.connect(self.convert)

        # Progress Bar
        self.p_bar = QtGui.QProgressBar(self)
        self.p_bar.hide()

        def get_pbar_inf(layout=None):
            pb = PBar(layout=layout, parent=self)
            pb.setMaximum(0)
            pb.setMinimum(0)
            return pb

        # Layout
        hbox_source = QtGui.QHBoxLayout()
        hbox_target = QtGui.QHBoxLayout()
        hbox_s_btn_set = QtGui.QHBoxLayout()
        hbox_t_btn_set = QtGui.QHBoxLayout()
        hbox_s_btn_set.setDirection(QtGui.QBoxLayout.RightToLeft)
        hbox_t_btn_set.setDirection(QtGui.QBoxLayout.RightToLeft)

        self.source_pbar = get_pbar_inf(hbox_s_btn_set)
        self.target_pbar = get_pbar_inf()

        hbox_source.addWidget(self.line_source)
        hbox_source.addWidget(btn_s_select)
        hbox_target.addWidget(self.line_target)
        hbox_target.addWidget(btn_t_select)
        hbox_t_btn_set.addWidget(self.target_pbar)
        hbox_s_btn_set.addWidget(self.source_pbar)
        hbox_t_btn_set.addWidget(self.p_bar)
        hbox_s_btn_set.addWidget(self.btn_convert, alignment=QtCore.Qt.AlignLeft)
        hbox_s_btn_set.addWidget(self.btn_browse, alignment=QtCore.Qt.AlignLeft)
        hbox_s_btn_set.addWidget(self.btn_s_params, alignment=QtCore.Qt.AlignLeft)
        hbox_t_btn_set.addWidget(self.btn_t_params, alignment=QtCore.Qt.AlignLeft)

        self.source_pbar.hide()
        self.target_pbar.hide()

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

        self.setLayout(grid)

        self.showMaximized()
        self.setWindowTitle('Swift - FCA convertor')
        self.show()

    def set_line_prop(self, line, validator):
        line.setMinimumWidth(200)
        self.set_line_bg(line, '#ffffff')
        line.setValidator(validator)

    def set_line_bg(self, line, color):
        line.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def check_state_source(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]

        if state == QtGui.QValidator.Acceptable and os.path.isfile(sender.text()):
            color = '#c4df9b'  # green
            self._source_params.clear()
            self.btn_s_params.setEnabled(True)
            self.btn_browse.setEnabled(True)
            self._source = sender.text()
        else:
            color = '#f6989d'  # red
            self.btn_s_params.setEnabled(False)
            self.btn_browse.setEnabled(False)
        if sender.text() == "":
            color = '#ffffff'  # white
            self._source = None
            self.btn_s_params.setEnabled(False)
            self.btn_browse.setEnabled(False)
            self._source_params.clear()
            self.clear_table(self.table_view_source)
        self.set_line_bg(sender, color)

    def check_state_target(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = '#c4df9b'  # green
            self._target_params.clear()
            self.btn_t_params.setEnabled(True)
            self._target = sender.text()
        else:
            color = '#f6989d'  # red
            self.btn_t_params.setEnabled(False)
        if sender.text() == "":
            color = '#ffffff'  # white
            self._target = None
            self.btn_t_params.setEnabled(False)
            self._target_params.clear()
            self.clear_table(self.table_view_target)
        self.set_line_bg(sender, color)

    def select_source(self):
        file_name = QtGui.QFileDialog.getOpenFileName(self, "Select source file", filter=self.file_filter)
        self.line_source.setText(file_name)

    def select_target(self):
        file_name = QtGui.QFileDialog.getSaveFileName(self, "Select target file", filter=self.file_filter)
        self.line_target.setText(file_name)

    def browse_data(self, browser, table_view):
        data = browser.get_display_data(self.SCROLL_COUNT)
        table_view.model().table.extend(data)
        table_view.model().layoutChanged.emit()

    def clear_table(self, table):
        table.model().table.clear()
        table.model().header.clear()
        table.model().layoutChanged.emit()

    def browse_first_data(self, table_view, browser, source_file, params, pbar):
        # clear old data
        self.clear_table(table_view)
        if browser:
            browser.close_file()

        # signal handler -> continue after thread ends
        def cont(browser):
            header = browser.get_header()
            table_view.model().header.extend(header)
            self.browse_data(browser, table_view)
            pbar.hide()

        try:
            pbar.show()
            browser = Browser(source=source_file, **params)

            # function which will be run on background
            def bg_func(worker):
                browser.read_info()
                worker.emit(SIGNAL('file_readed'), browser)

            bg = BgWorker(bg_func, self)
            bg.connect(bg, SIGNAL('file_readed'), cont, QtCore.Qt.QueuedConnection)
            bg.start()
            return browser
        except:
            self.clear_table(table_view)
            tb = traceback.format_exc()
            msgBox = QtGui.QMessageBox()
            msgBox.setWindowTitle("Browsing error")
            msgBox.setText("Wasn't possible to browse data, please check syntax in browsing file and separator used.")
            msgBox.setStandardButtons(QtGui.QMessageBox.Close)
            msgBox.setDetailedText(tb)
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.exec_()

    def browse_next_source(self, value):
        if self.table_view_source.verticalScrollBar().maximum() == value:
            self.browse_data(self.browser_source, self.table_view_source)

    def browse_next_target(self, value):
        if self.table_view_target.verticalScrollBar().maximum() == value:
            self.browse_data(self.browser_target, self.table_view_target)

    def change_source_params(self):
        self.change_params(SourceParamsDialog, self._source_params)

    def change_target_params(self):
        self.change_params(TargetParamsDialog, self._target_params)

    def change_params(self, cls, params):
        result = cls.get_params(self)
        confirmed = result[1]
        if confirmed:
            params.clear()
            params.update(result[0])
            print(params)

    def browse_source(self):
        self.browser_source = self.browse_first_data(self.table_view_source, self.browser_source,
                                                     self.source, self.source_params, self.source_pbar)

    def convert(self):
        validator = ParamValidator(self.source, self.target, self.source_params, self.target_params)
        warnings = validator.warnings

        procces = True
        if len(warnings) > 0:
            msgBox = QtGui.QMessageBox()
            msgBox.setWindowTitle("Parameters warning")
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
                self.p_bar.setValue(self.p_bar.value() + 1)

            def setup_pbar(maximum):
                self.p_bar.show()
                self.p_bar.setMinimum(1)
                self.p_bar.setMaximum(maximum)
                self.p_bar.setTextVisible(True)
                self.p_bar.setFormat("Converting, please wait " + self.p_bar.format())

            def clear_pbar():
                self.p_bar.reset()
                self.p_bar.hide()

            def display_data(c):
                clear_pbar()
                # display data
                self.browser_target = self.browse_first_data(self.table_view_target, self.browser_target,
                                                             self.target, self.target_params, self.target_pbar)

            # signal handler -> continue after thread ends
            def cont(convertor):
                self.target_pbar.hide()
                setup_pbar(convertor.source_line_count)
                convertor.next_line.connect(update_pbar)

                # function which will be run on background
                def bg_func(worker):
                    convertor.convert()
                    worker.emit(SIGNAL('file_converted'), convertor)

                bg = BgWorker(bg_func, self)
                bg.connect(bg, SIGNAL('file_converted'), display_data, QtCore.Qt.QueuedConnection)
                bg.start()
            try:
                convertor = Convertor(s_p, t_p)
                self.target_pbar.show()

                # function which will be run on background
                def bg_func(worker):
                    convertor.read_info()
                    worker.emit(SIGNAL('file_readed'), convertor)

                bg = BgWorker(bg_func, self)
                bg.connect(bg, SIGNAL('file_readed'), cont, QtCore.Qt.QueuedConnection)
                bg.start()

            except:
                tb = traceback.format_exc()
                msgBox = QtGui.QMessageBox()
                msgBox.setWindowTitle("Convert error")
                msgBox.setText("Wasn't possible to convert data, please check syntax in source file and specified parameters.")
                msgBox.setStandardButtons(QtGui.QMessageBox.Close)
                msgBox.setDetailedText(tb)
                msgBox.setIcon(QtGui.QMessageBox.Critical)
                msgBox.exec_()

    def closeEvent(self, event):
        if self.browser_source:
            self.browser_source.close_file()
        if self.browser_target:
            self.browser_target.close_file()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()


class SwiftTableModel(QtCore.QAbstractTableModel):
    def __init__(self, parent, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.table = []
        self.header = []

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
        return self.table[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
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


class PBar(QtGui.QProgressBar):

    def __init__(self, layout=None, parent=None):
        super().__init__(parent)
        self.layout = layout

    def hide(self):
        super().hide()
        if self.layout:
            self.layout.insertStretch(0, 1)

    def show(self):
        super().show()
        if self.layout:
            self.layout.takeAt(0)


def main():

    app = QtGui.QApplication(sys.argv)
    ex = GuiSwift()  # NOQA
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
