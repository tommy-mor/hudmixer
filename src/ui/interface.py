import sys

from qtpy.QtWidgets import QMainWindow, QTreeWidget, QTreeWidgetItem, QApplication
from qtpy import QtCore

import src.feature_list as fl


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        treeWidget = QTreeWidget(self)
        treeWidget.setColumnCount(2)

        items = [QTreeWidgetItem(cls.__name__) for cls in fl.classes]
        treeWidget.insertTopLevelItems(0, items)
        self.setCentralWidget(treeWidget)


