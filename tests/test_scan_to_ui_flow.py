from pathlib import Path

from PyQt5.QtWidgets import QApplication

from ui.searchUpdateDatabase import FolderScannerWorker
from ui.widgets.master_detail import init_master_detail
from ui.widgets.detail import update_detail_view


def test_scan_to_ui_flow(tmp_path, monkeypatch):
    """End-to-end slice: scan a folder, then verify the master and
    detail lists show the expected lesson and video, with correct
    file_path stored on the detail item."""
    db_path = tmp_path / "test_lessons.db"

    # Prepare a fake lesson folder with one media file
    lesson_folder = tmp_path / "001_Test_Lesson"
    lesson_folder.mkdir()
    media_file = lesson_folder / "example.mp3"
    media_file.write_bytes(b"fake-audio")

    # Avoid calling ffprobe during tests
    def fake_extract_audio_metadata(path):
        return 10.0, 128000

    monkeypatch.setattr(
        "ui.searchUpdateDatabase.extract_audio_metadata",
        fake_extract_audio_metadata,
    )

    # Run the folder scanner worker synchronously
    worker = FolderScannerWorker(str(db_path), str(tmp_path))
    worker.run()

    # Ensure a Qt application exists for widget creation
    app = QApplication.instance() or QApplication([])

    # Minimal app-like object expected by init_master_detail
    class DummyApp:
        def __init__(self, db_path):
            self.db_path = db_path
            self.current_speed = 1.0
            self.transpose_steps = 0

        # Playback methods expected by player_controls
        def play_video(self):
            if hasattr(self, "media_player"):
                self.media_player.play()

        def pause_video(self):
            if hasattr(self, "media_player"):
                self.media_player.pause()

        def stop_video(self):
            if hasattr(self, "media_player"):
                self.media_player.stop()

    dummy_app = DummyApp(str(db_path))

    # Initialize master/detail UI against the populated DB
    splitter = init_master_detail(dummy_app)
    assert dummy_app.master_list.count() == 1

    master_item = dummy_app.master_list.item(0)

    # Trigger detail view population
    update_detail_view(dummy_app, master_item)

    assert dummy_app.video_list.count() == 1
    video_item = dummy_app.video_list.item(0)

    assert video_item.text() == media_file.name
    assert Path(video_item.data(0x0100)) == media_file  # Qt.UserRole

