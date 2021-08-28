import sys

from PySide6.QtWidgets import QMainWindow, QTreeWidget, QTreeWidgetItem, QApplication, QFileDialog, QErrorMessage, QVBoxLayout, QPushButton, QWidget, QMessageBox

import model.feature_list as fl
import model.hud as hud

import traceback

from pathlib import Path
import shutil


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        treeWidget = QTreeWidget(self)
        treeWidget.setColumnCount(2)
        treeWidget.setHeaderHidden(True)

        self.nameToClass = {cls.__name__: cls for cls in fl.classes}

        self.baseItem = QTreeWidgetItem(treeWidget, ["Base/Foundation"])
        self.items = [QTreeWidgetItem(treeWidget, [name]) for name in self.nameToClass.keys()]

        treeWidget.resizeColumnToContents(0)

        treeWidget.itemClicked['QTreeWidgetItem*', 'int'].connect(self.tree_item_clicked)

        main = QWidget(self)
        box = QVBoxLayout(main)
        box.addWidget(treeWidget)
        button = QPushButton("export")
        button.clicked.connect(self.export_pressed)
        box.addWidget(button)
        self.setCentralWidget(main)

    def export_pressed(self):
        d = QFileDialog.getExistingDirectory(self, "Directory To Export To", None, QFileDialog.ShowDirsOnly)

        if d:
            exportdir = Path(d) / 'MIXER_EXPORTED_HUD'
            if exportdir.exists():
                reply = QMessageBox.question(self, "Export Overwrite", "Do you want to overwrite hud at %s" % exportdir,
                                             QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return
                elif reply == QMessageBox.Yes:
                    shutil.rmtree(exportdir)

            inhud = self.baseItem.data(100, 0)
            outhud = hud.OutHud(inhud, exportdir)

            for item in self.items:
                feature, importhud = item.data(0, 0), item.data(100, 0)
                if importhud.__class__ == hud.ImportHud:
                    outhud.add_feature(self.nameToClass[feature](importhud))

            outhud.export()
            QMessageBox.information(self, "Information", "Hud exported to %s" % exportdir)

            
            

    def tree_item_clicked(self, item, n):
        d = QFileDialog.getExistingDirectory(self, "Open Directory", None, QFileDialog.ShowDirsOnly)
        if d:
            try:
                print('trying to import hud %s' % d)
                newhud = (hud.BaseHud if item == self.baseItem else hud.ImportHud)(d)
                print(newhud)
                item.setData(1, 0, newhud.translation_key)
                item.setData(100, 0, newhud)
            except hud.HudException as e:
                print(e)
                QErrorMessage(self).showMessage('error importing hud, %s' % e)
            except AssertionError as e:
                print('failed loading %s' % d)
                QErrorMessage(self).showMessage('failed loading %s, %s'% (d, '\n'.join(traceback.format_exception(AssertionError, e, e.__traceback__))))
