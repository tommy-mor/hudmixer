import sys

from qtpy.QtWidgets import QApplication
from ui.interface import MainWindow

assert __name__ == '__main__'

app = QApplication([])
widget = MainWindow()

widget.resize(300, 600)
widget.show()

sys.exit(app.exec())
