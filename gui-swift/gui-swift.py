#!/usr/bin/python3

"""
GUI application for Swift FCA
"""

import sys
from PyQt4 import QtGui, QtCore


class GuiSwift(QtGui.QWidget):

    def __init__(self):
        super(GuiSwift, self).__init__()

        self.initUI()

    def initUI(self):

        # Widgets
        label_source = QtGui.QLabel('Source file')
        label_target = QtGui.QLabel('Target file')

        self.line_source = QtGui.QLineEdit()
        self.line_target = QtGui.QLineEdit()
        regexp = QtCore.QRegExp('^.+\.(arff|data|dat|cxt|csv)$')
        line_validator = QtGui.QRegExpValidator(regexp)
        self.set_line_prop(self.line_source, line_validator)
        self.set_line_prop(self.line_target, line_validator)

        table_view_source = QtGui.QTableView()
        table_view_target = QtGui.QTableView()

        btn_source = QtGui.QPushButton("Select")
        btn_target = QtGui.QPushButton("Select")
        self.file_filter = "FCA files (*.arff *.cxt *.data *.dat *.csv);;All(*)"
        btn_source.clicked.connect(self.select_source)
        btn_target.clicked.connect(self.select_target)

        # Layout
        hbox_source = QtGui.QHBoxLayout()
        hbox_target = QtGui.QHBoxLayout()

        hbox_source.addWidget(self.line_source)
        hbox_source.addWidget(btn_source)
        hbox_target.addWidget(self.line_target)
        hbox_target.addWidget(btn_target)

        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(label_source, 0, 0)
        grid.addWidget(label_target, 0, 1)
        grid.addLayout(hbox_source, 1, 0)
        grid.addLayout(hbox_target, 1, 1)
        grid.addWidget(table_view_source, 2, 0)
        grid.addWidget(table_view_target, 2, 1)

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
        else:
            color = '#f6989d'  # red
        if sender.text() == "":
            color = '#ffffff'  # white
        self.set_line_bg(sender, color)

    def select_source(self):
        file_name = QtGui.QFileDialog.getOpenFileName(self, "Select source file", filter=self.file_filter)
        self.line_source.setText(file_name)

    def select_target(self):
        file_name = QtGui.QFileDialog.getSaveFileName(self, "Select target file", filter=self.file_filter)
        self.line_target.setText(file_name)


def main():

    app = QtGui.QApplication(sys.argv)
    ex = GuiSwift()  # NOQA
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
