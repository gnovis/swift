#!/usr/bin/python3

"""
GUI application for Swift FCA
"""

import sys
import collections
import os.path
from PyQt4 import QtGui, QtCore
from source_swift.managers_fca import Browser
from source_swift.constants_fca import (RunParams, FileType)


class GuiSwift(QtGui.QWidget):

    SCROLL_COUNT = 50

    def __init__(self):
        super(GuiSwift, self).__init__()

        self._source_params = {}
        self._target_params = {}

        self.can_browse = False
        self.browser_source = None
        self.browser_target = None

        self.initUI()

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

        self.table_view_source.verticalScrollBar().valueChanged.connect(self.browse_next_data)

        # Buttons
        btn_s_select = QtGui.QPushButton("Select")
        btn_t_select = QtGui.QPushButton("Select")
        self.btn_s_params = QtGui.QPushButton("Change Params")
        self.btn_t_params = QtGui.QPushButton("Change Params")
        self.btn_convert = QtGui.QPushButton("Convert")
        self.file_filter = "FCA files (*.arff *.cxt *.data *.dat *.csv);;All(*)"

        self.btn_s_params.clicked.connect(self.change_source_params)
        self.btn_t_params.clicked.connect(self.change_target_params)
        self.btn_s_params.setEnabled(False)
        self.btn_t_params.setEnabled(False)
        btn_s_select.clicked.connect(self.select_source)
        btn_t_select.clicked.connect(self.select_target)

        # Layout
        hbox_source = QtGui.QHBoxLayout()
        hbox_target = QtGui.QHBoxLayout()
        hbox_s_btn_set = QtGui.QHBoxLayout()
        hbox_t_btn_set = QtGui.QHBoxLayout()
        hbox_s_btn_set.addStretch(1)
        hbox_t_btn_set.addStretch(1)
        hbox_s_btn_set.setDirection(QtGui.QBoxLayout.RightToLeft)
        hbox_t_btn_set.setDirection(QtGui.QBoxLayout.RightToLeft)

        hbox_source.addWidget(self.line_source)
        hbox_source.addWidget(btn_s_select)
        hbox_target.addWidget(self.line_target)
        hbox_target.addWidget(btn_t_select)
        hbox_s_btn_set.addWidget(self.btn_convert)
        hbox_s_btn_set.addWidget(self.btn_s_params)
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
            self.can_browse = True
            self.browse_first_data()
            self._source_params.clear()
            self._source_params[RunParams.SOURCE] = sender.text()
            self.btn_s_params.setEnabled(True)
        else:
            color = '#f6989d'  # red
            self.can_browse = False
            self.btn_s_params.setEnabled(False)
        if sender.text() == "":
            color = '#ffffff'  # white
            self.clear_table(self.table_view_source)
            self.btn_s_params.setEnabled(False)
        self.set_line_bg(sender, color)

    def check_state_target(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = '#c4df9b'  # green
            self._target_params.clear()
            self._target_params[RunParams.TARGET] = sender.text()
            self.btn_t_params.setEnabled(True)
        else:
            color = '#f6989d'  # red
            self.btn_t_params.setEnabled(False)
        if sender.text() == "":
            color = '#ffffff'  # white
            self.btn_t_params.setEnabled(False)
        self.set_line_bg(sender, color)

    def select_source(self):
        file_name = QtGui.QFileDialog.getOpenFileName(self, "Select source file", filter=self.file_filter)
        self.line_source.setText(file_name)

    def select_target(self):
        file_name = QtGui.QFileDialog.getSaveFileName(self, "Select target file", filter=self.file_filter)
        self.line_target.setText(file_name)

    def browse_data(self):
        data = self.browser_source.get_display_data(self.SCROLL_COUNT)
        self.table_view_source.model().table.extend(data)
        self.table_view_source.model().layoutChanged.emit()

    def clear_table(self, table):
        table.model().table.clear()
        table.model().header.clear()
        table.model().layoutChanged.emit()

    def browse_first_data(self):
        if self.can_browse:
            # clear old data
            self.table_view_source.model().table = []
            self.table_view_source.model().header = []
            if self.browser_source:
                self.browser_source.close_file()

            # add new data
            self.browser_source = Browser(self.line_source.text())
            header = self.browser_source.get_header()
            self.table_view_source.model().header.extend(header)
            self.browse_data()

    def browse_next_data(self, value):
        if self.table_view_source.verticalScrollBar().maximum() == value and self.can_browse:
            self.browse_data()

    def change_source_params(self):
        self.change_params(SourceParamsDialog, self._source_params)

    def change_target_params(self):
        self.change_params(TargetParamsDialog, self._target_params)

    def change_params(self, cls, params):
        result = cls.get_params(self)
        confirmed = result[1]
        if confirmed:
            params.update(result[0])

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
            if w.data() != "":
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

    format_poss_args = {FileType.ARFF: (RunParams.SOURCE_SEP),
                        FileType.CSV: (RunParams.SOURCE_SEP, RunParams.NFL, RunParams.SOURCE_ATTRS),
                        FileType.CXT: (),
                        FileType.DAT: (RunParams.SOURCE_SEP),
                        FileType.DATA: (RunParams.SOURCE_SEP)}

    def __init__(self, parent):
        super().__init__(parent)
        self.params = parent.source_params
        # form lines
        self.line_separator = FormLine("Separator")
        self.line_str_attrs = FormLine("Attributes")
        # check box
        self.cb_nfl = FormCheckBox('Attributes on first line')

        # layout
        self.widgets[RunParams.NFL] = self.cb_nfl
        self.widgets[RunParams.SOURCE_ATTRS] = self.line_str_attrs
        self.widgets[RunParams.SOURCE_SEP] = self.line_separator

        suffix = os.path.splitext(self.params[RunParams.SOURCE])[1]
        self.fill_layout(suffix)
        self.setWindowTitle('Parameters for source file')


class TargetParamsDialog(ParamsDialog):

    format_poss_args = {FileType.ARFF: (RunParams.TARGET_ATTRS, RunParams.TARGET_SEP),
                        FileType.CSV: (RunParams.TARGET_ATTRS, RunParams.TARGET_SEP),
                        FileType.CXT: (RunParams.TARGET_ATTRS, RunParams.TARGET_OBJECTS),
                        FileType.DAT: (RunParams.TARGET_ATTRS, RunParams.TARGET_SEP),
                        FileType.DATA: (RunParams.TARGET_ATTRS, RunParams.CLASSES, RunParams.TARGET_SEP)}

    def __init__(self, parent):
        super().__init__(parent)
        self.params = parent.target_params
        # form lines
        self.line_separator = FormLine("Separator")
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
        suffix = os.path.splitext(self.params[RunParams.TARGET])[1]
        self.fill_layout(suffix)
        self.setWindowTitle('Parameters for target file')


class FormCheckBox(QtGui.QWidget):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.cb = QtGui.QCheckBox(label, self)
        self.cb.toggle()
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.cb)
        layout.setContentsMargins(6, 0, 0, 10)
        self.setLayout(layout)

    def data(self):
        return not bool(self.cb.checkState())

    def set_data(self, data):
        if data:
            self.cb.setChecked(QtCore.Qt.Unchecked)


class FormLine(QtGui.QWidget):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        self.label = QtGui.QLabel(label)
        self.line = QtGui.QLineEdit()
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


def main():

    app = QtGui.QApplication(sys.argv)
    ex = GuiSwift()  # NOQA
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
