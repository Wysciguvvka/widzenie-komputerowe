from PySide6 import QtGui
from PySide6.QtGui import QIcon, QKeyEvent
from PySide6.QtWidgets import QApplication, QMainWindow

from src import UiMainWindow

import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)


class UI(QMainWindow):
    def __init__(self, *args, **kwargs) -> None:
        super(UI, self).__init__(*args, **kwargs)
        self.setWindowTitle("Aplikacja")
        size = app.primaryScreen().size() * 0.6
        self.resize(size)
        self.setMinimumSize(800, 450)
        self.ui = UiMainWindow(self)
        self.setCentralWidget(self.ui)

    # def keyPressEvent(self, event: QKeyEvent) -> None:
    #     super().keyPressEvent(event)
    #     if event.matches(QtGui.QKeySequence.Paste):  # type: ignore
    #         self.ui.content.image_picker.paste()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    ui = UI()
    ui.show()
    sys.exit(app.exec())

