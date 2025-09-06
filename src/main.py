#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication

from ui import PromptWindow


def main():
    app = QApplication(sys.argv)
    win = PromptWindow()
    win.show()
    exit(app.exec())


if __name__ == "__main__":
    main()
