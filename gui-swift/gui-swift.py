#!/usr/bin/python3

"""
GUI application for Swift FCA
"""

import sys
from PyQt4 import QtGui


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
        self.set_line_prop(self.line_source)
        self.set_line_prop(self.line_target)

        table_view_source = QtGui.QTableView()
        table_view_target = QtGui.QTableView()

        btn_source = QtGui.QPushButton("Select")
        btn_target = QtGui.QPushButton("Select")
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

    def set_line_prop(self, line):
        line.setMinimumWidth(200)

    def select_source(self):
        file_name = QtGui.QFileDialog.getOpenFileName(self)
        self.line_source.setText(file_name)

    def select_target(self):
        file_name = QtGui.QFileDialog.getSaveFileName(self, caption="Select target file")
        self.line_target.setText(file_name)


def main():

    app = QtGui.QApplication(sys.argv)
    ex = GuiSwift()  # NOQA
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
