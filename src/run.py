import sys

from qtpy.QtWidgets import QApplication
from ui.interface import MainWindow

assert __name__ == '__main__'

app = QApplication([])
widget = MainWindow()
widget.setWindowTitle("Tf2 hud mixer")

widget.resize(300, 300)
widget.show()

sys.exit(app.exec())
