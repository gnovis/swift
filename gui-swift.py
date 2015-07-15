#!/usr/bin/python3

"""
GUI application for Swift FCA
"""

import sys
from PyQt4 import QtGui, QtCore
from source_swift.managers_fca import Browser


class GuiSwift(QtGui.QWidget):

    SCROLL_COUNT = 50

    def __init__(self):
        super(GuiSwift, self).__init__()

        self.initUI()

    def initUI(self):

        self.can_browse = False
        self.browser_source = None
        self.browser_target = None

        # Widgets
        label_source = QtGui.QLabel('Source file')
        label_target = QtGui.QLabel('Target file')

        self.line_source = QtGui.QLineEdit()
        self.line_target = QtGui.QLineEdit()
        regexp = QtCore.QRegExp('^.+\.(arff|data|dat|cxt|csv)$')
        line_validator = QtGui.QRegExpValidator(regexp)
        self.set_line_prop(self.line_source, line_validator)
        self.set_line_prop(self.line_target, line_validator)

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

        btn_s_select.clicked.connect(self.select_source)
        btn_t_select.clicked.connect(self.select_target)

        # Layout
        hbox_source = QtGui.QHBoxLayout()
        hbox_target = QtGui.QHBoxLayout()
        hbox_s_btn_set = QtGui.QHBoxLayout()
        hbox_t_btn_set = QtGui.QHBoxLayout()
        hbox_s_btn_set.addStretch(1)
        hbox_t_btn_set.addStretch(1)
        hbox_s_btn_set.setDirection(1)
        hbox_t_btn_set.setDirection(1)

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
        line.textChanged.connect(self.check_state)

    def set_line_bg(self, line, color):
        line.setStyleSheet('QLineEdit { background-color: %s }' % color)

    def check_state(self, *args, **kwargs):
        sender = self.sender()
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QtGui.QValidator.Acceptable:
            color = '#c4df9b'  # green
            self.can_browse = True
            self.browse_first_data()
        else:
            color = '#f6989d'  # red
            self.can_browse = False
        if sender.text() == "":
            color = '#ffffff'  # white
            self.clear_table(self.table_view_source)
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
        table.model().table = []
        table.model().header = []
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

    def closeEvent(self, event):
        if self.browser_source:
            self.browser_source.close_file()
        if self.browser_target:
            self.browser_target.close_file()


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


def main():

    app = QtGui.QApplication(sys.argv)
    ex = GuiSwift()  # NOQA
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
