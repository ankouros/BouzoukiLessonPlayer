import os
import sqlite3
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QHBoxLayout,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QSettings
from core.media_utils import extract_metadata
from core.database import (
    connect_to_db,
    create_folders_table,
    insert_folder,
    get_all_folders,
    insert_lesson,
    ensure_lesson_mapping_table,
    get_or_assign_lesson_number,
)
from core.media_utils import extract_audio_metadata
from ui.widgets.master import update_master_list


def propagate_status_to_app(app_reference, message: str) -> None:
    """Send scan status text to the main app status bar when available."""
    if app_reference is not None and hasattr(app_reference, "_set_status_message"):
        app_reference._set_status_message(message)


class FolderScannerWorker(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(int, int)

    def __init__(self, db_path, folder):
        super().__init__()
        self.db_path = db_path
        self.folder = folder

    def run(self):
        conn = connect_to_db(self.db_path)
        ensure_lesson_mapping_table(conn)

        added = 0
        skipped = 0
        files_to_process = []

        for root, _, files in os.walk(self.folder):
            # Always ignore any directory named "Downloads" (and its subtrees)
            # to avoid scanning typical download locations.
            parts = os.path.normpath(root).split(os.sep)
            if "Downloads" in parts:
                self.status.emit(f"Ignoring Downloads folder: {root}")
                continue

            for file in files:
                if file.lower().endswith((".mp4", ".mkv", ".mp3")):
                    files_to_process.append(os.path.join(root, file))

        total = len(files_to_process)

        if total == 0:
            # Nothing to process: keep progress at 0 and finish cleanly.
            self.status.emit("No media files found.")
            self.progress.emit(0)
            conn.close()
            self.finished.emit(0, 0)
            return

        for i, file_path in enumerate(files_to_process, 1):
            folder_name = os.path.basename(os.path.dirname(file_path))

            # Try to extract metadata
            lesson_number, lesson_name = extract_metadata(folder_name)

            # Fallback if extraction failed
            if lesson_number is None:
                lesson_number = get_or_assign_lesson_number(conn, folder_name)
                lesson_name = folder_name.replace("_", " ").strip()

            # Extract media info
            duration, bitrate = extract_audio_metadata(file_path)

            try:
                insert_lesson(
                    conn,
                    lesson_number,
                    lesson_name,
                    os.path.basename(file_path),
                    file_path,
                    duration,
                    bitrate,
                )
                added += 1
                self.status.emit(f"✅ Added: {file_path}")
            except sqlite3.IntegrityError:
                skipped += 1
                self.status.emit(f"⏭️ Skipped (duplicate): {file_path}")
            except Exception as e:
                self.status.emit(f"❌ Error: {file_path} -> {e}")

            self.progress.emit(int(i / total * 100))

        conn.close()
        self.finished.emit(added, skipped)


class FolderScannerWindow(QDialog):
    def __init__(self, db_path, app_reference=None):
        super().__init__()
        self.setModal(True)
        self.db_path = db_path
        self.conn = connect_to_db(db_path)
        self.app_reference = app_reference  # optional reference to main app
        self.setWindowTitle("Search and Update Media")
        self.setGeometry(300, 300, 700, 450)
        self.setLayout(self._init_ui())
        self._load_existing_folders()

    def _init_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Previously Scanned Folders:"))

        self.folder_list = QListWidget()
        layout.addWidget(self.folder_list)

        # Button Bar
        button_bar = QHBoxLayout()

        self.select_btn = QPushButton("Select Folder")
        self.select_btn.clicked.connect(self.select_folder)
        button_bar.addWidget(self.select_btn)

        self.delete_btn = QPushButton("Delete Folder")
        self.delete_btn.clicked.connect(self.delete_selected_folder)
        button_bar.addWidget(self.delete_btn)

        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_scan)
        button_bar.addWidget(self.start_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)  # Placeholder
        button_bar.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)  # Placeholder
        button_bar.addWidget(self.stop_btn)

        layout.addLayout(button_bar)

        # Scan Feedback
        layout.addWidget(QLabel("Scan Status:"))
        self.status_bar = QListWidget()
        self.status_bar.setMaximumHeight(150)
        layout.addWidget(self.status_bar)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        return layout

    def _load_existing_folders(self):
        create_folders_table(self.conn)
        for path in get_all_folders(self.conn):
            self.folder_list.addItem(path)

    def select_folder(self):
        settings = QSettings("bouzouki", "lessonplayer")
        default_dir = settings.value("default_scan_folder") or settings.value("media_library_path") or ""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", default_dir)
        if folder:
            self._insert_folder(folder)

    def delete_selected_folder(self):
        selected_items = self.folder_list.selectedItems()
        if not selected_items:
            return

        cursor = self.conn.cursor()
        for item in selected_items:
            folder_path = item.text()
            cursor.execute("DELETE FROM folders WHERE path = ?", (folder_path,))
            self.folder_list.takeItem(self.folder_list.row(item))
        self.conn.commit()

    def _insert_folder(self, folder):
        try:
            insert_folder(self.conn, folder)
            if not any(self.folder_list.item(i).text() == folder for i in range(self.folder_list.count())):
                self.folder_list.addItem(folder)
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"Failed to add folder: {e}")

    def start_scan(self):
        selected_items = self.folder_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Folder Selected", "Please select a folder to scan.")
            return

        folder = selected_items[0].text()
        self._start_scan_thread(folder)

    def _start_scan_thread(self, folder):
        self.progress_bar.setValue(0)
        self.status_bar.clear()

        self.worker = FolderScannerWorker(self.db_path, folder)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.status.connect(self.status_bar.addItem)
        # Also propagate scan status to the main app's status bar when possible.
        if self.app_reference is not None:
            self.worker.status.connect(lambda msg: propagate_status_to_app(self.app_reference, msg))
        self.worker.finished.connect(self._scan_complete)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _scan_complete(self, added, skipped):
        QMessageBox.information(
            self,
            "Scan Complete",
            f"Scan finished.\nAdded: {added}\nSkipped duplicates: {skipped}",
        )
        summary = f"Scan finished. Added: {added}, Skipped: {skipped}"
        propagate_status_to_app(self.app_reference, summary)
        if self.app_reference:
            update_master_list(self.app_reference)
