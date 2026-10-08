"""AI User Manual - entry point.  Run:  python main.py"""
import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox

import config
import database


def main():
    config.ensure_dirs()
    database.init_db()
    from ui import STYLE, MainWindow   # imported after DB init

    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)

    def excepthook(exc_type, exc, tb):  # last line of defence: never crash the GUI silently
        traceback.print_exception(exc_type, exc, tb)
        QMessageBox.warning(None, "Unexpected error", f"{exc}")

    sys.excepthook = excepthook
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
