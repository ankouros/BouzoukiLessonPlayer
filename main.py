import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings, QTranslator, QLocale

from ui.main_window import LessonPlayerApp
from core.theme_manager import load_theme


def configure_logging(
    log_file: str = "bouzouki_player.log",
    max_bytes: int = 1_000_000,
    backup_count: int = 3,
) -> None:
    """Configure application logging with simple rotation.

    This keeps the main log from growing without bound while preserving
    a small number of historical files.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Replace any existing handlers to avoid duplicate logging
    logger.handlers = [handler]


def main():
    # Set application name
    QApplication.setApplicationName("Bouzouki Lesson Player")

    # Enable high DPI scaling (optional, helps on 4K monitors)
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

    # Initialize logging with rotation
    configure_logging()

    try:
        # Create Qt application
        app = QApplication(sys.argv)

        # Load language preference and install translator if available
        settings = QSettings("bouzouki", "lessonplayer")
        lang_code = settings.value("language_code", "")
        if lang_code:
            translator = QTranslator()
            # Attempt to load a translation file; this is infrastructure
            # only and will quietly do nothing if no file is present.
            if translator.load(f"bouzouki_{lang_code}", "resources/i18n"):
                app.installTranslator(translator)

        # Load and apply saved theme
        load_theme(app)

        # Create and show main window
        window = LessonPlayerApp(db_path="./lessons.db")
        window.show()

        # Run event loop
        sys.exit(app.exec_())

    except Exception as e:
        logging.exception("An unexpected error occurred:")  # Log the error
        print(f"A critical error occurred: {e}")  # Show error to user
        sys.exit(1)  # Exit with error code


if __name__ == "__main__":
    main()
