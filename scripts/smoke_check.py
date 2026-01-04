"""Simple smoke-check script for BouzoukiLessonsPlayer.

This script starts the application main window and then closes it
shortly after, to catch import/runtime errors outside of pytest.
"""

import sys
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

from core.theme_manager import load_theme
from ui.main_window import LessonPlayerApp
from main import configure_logging


def run_smoke_check():
    """Start the main window briefly to ensure it can be created."""
    configure_logging()

    app = QApplication.instance() or QApplication(sys.argv)
    load_theme(app)

    window = LessonPlayerApp(db_path="./lessons.db")
    window.show()

    # Close the app shortly after startup.
    QTimer.singleShot(500, app.quit)
    app.exec_()


if __name__ == "__main__":
    run_smoke_check()

