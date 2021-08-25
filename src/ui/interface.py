import sys

from qtpy.QtWidgets import QMainWindow, QTreeWidget, QTreeWidgetItem, QApplication, QFileDialog, QErrorMessage
from qtpy import QtCore

import model.feature_list as fl
import model.hud as hud

import traceback


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        treeWidget = QTreeWidget(self)
        treeWidget.setColumnCount(2)

        self.nameToClass = {cls.__name__: cls for cls in fl.classes}

        self.items = [QTreeWidgetItem(treeWidget, [name]) for name in self.nameToClass.keys()]

        treeWidget.resizeColumnToContents(0)

        treeWidget.itemClicked['QTreeWidgetItem*', 'int'].connect(self.tree_item_clicked)
        self.setCentralWidget(treeWidget)

    def tree_item_clicked(self, item, n):
        d = QFileDialog.getExistingDirectory(self, "Open Directory", None, QFileDialog.ShowDirsOnly)

        print(d)

        if d:
            try:
                print('trying to import hud %s' % d)
                newhud = hud.ImportHud(d)
                print(newhud)
                item.setData(1, 0, newhud.translation_key)
                item.setData(100, 0, newhud)
            except hud.HudException as e:
                print(e)
                QErrorMessage(self).showMessage('error importing hud, %s' % e)
            except AssertionError as e:
                print('failed loading %s' % d)
                QErrorMessage(self).showMessage('failed loading %s, %s'% (d, '\n'.join(traceback.format_exception(AssertionError, e, e.__traceback__))))
