import logging
import os
import platform
import subprocess
import sys

from PyQt5.QtWidgets import (
    QListWidgetItem,
    QWidget,
    QVBoxLayout,
    QListWidget,
    QSplitter,
    QMenu,
    QInputDialog,
    QMessageBox,
    QApplication,
    QLabel,
    QSizePolicy,
    QFileDialog,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QUrl, Qt, QTimer, QSettings
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget

from core.vlc_player import VlcMediaPlayer, VlcUnavailableError
from ui.widgets.player_controls import init_player_controls

logger = logging.getLogger(__name__)


def _should_use_vlc_backend() -> bool:
    settings = QSettings("bouzouki", "lessonplayer")
    val = settings.value("use_vlc_backend", True)
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("true", "1", "yes")


def create_detail_panel(app):
    widget = QWidget()
    layout = QVBoxLayout(widget)
    app.right_panel_layout = layout

    splitter = QSplitter(Qt.Vertical)

    video_container = QWidget()
    video_layout = QVBoxLayout(video_container)
    # Slight padding to keep the player from touching window edges while
    # avoiding large empty borders.
    video_layout.setContentsMargins(6, 6, 6, 4)
    video_layout.setSpacing(6)

    app.video_widget = QVideoWidget()
    app.media_player = QMediaPlayer()

    # Optional VLC backend for audio/video (pitch-preserving time-stretch)
    app.vlc_player = None
    if _should_use_vlc_backend():
        try:
            app.vlc_player = VlcMediaPlayer()
            app.media_player.setVolume(0)

            def _attach_vlc_video():
                try:
                    window_id = int(app.video_widget.winId())
                    app.vlc_player.set_video_output(window_id)
                    logger.info("VLC backend enabled for audio/video playback")
                except Exception:
                    logger.exception("Failed to attach VLC video output; falling back to Qt video")
                    app.vlc_player = None
                    app.media_player.setVolume(70)
                    app.media_player.setVideoOutput(app.video_widget)

            # Delay attachment until the widget has a valid native handle
            QTimer.singleShot(0, _attach_vlc_video)
        except VlcUnavailableError:
            app.vlc_player = None
            logger.warning("VLC backend requested but unavailable; falling back to QMediaPlayer")
            QTimer.singleShot(100, lambda: app.media_player.setVideoOutput(app.video_widget))
    else:
        QTimer.singleShot(100, lambda: app.media_player.setVideoOutput(app.video_widget))

    app.placeholder_label = QLabel()
    app.placeholder_label.setAlignment(Qt.AlignCenter)
    app.placeholder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def resize_placeholder():
        target_height = int(video_container.height() * 0.45)
        target_width = video_container.width()
        scaled_pixmap = QPixmap("resources/bouzouki.png").scaled(
            target_width,
            target_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        app.placeholder_label.setPixmap(scaled_pixmap)

    QTimer.singleShot(0, resize_placeholder)
    video_container.resizeEvent = lambda event: resize_placeholder()

    video_layout.addWidget(app.placeholder_label)
    video_layout.addWidget(app.video_widget)

    controls = init_player_controls(app)
    video_layout.addLayout(controls)

    # Practice preset / metronome status label just below the controls.
    app.practice_status_label = QLabel("")
    app.practice_status_label.setAlignment(Qt.AlignLeft)
    app.practice_status_label.setObjectName("practiceStatusLabel")
    video_layout.addWidget(app.practice_status_label)

    # Make the video area consume most of the vertical space, keeping
    # controls and status compact at the bottom.
    video_layout.setStretch(0, 5)  # placeholder/video region
    video_layout.setStretch(1, 5)
    video_layout.setStretch(2, 0)  # controls
    video_layout.setStretch(3, 0)  # status label

    splitter.addWidget(video_container)

    app.video_list = QListWidget()
    app.video_list.setSpacing(2)
    app.video_list.setContextMenuPolicy(Qt.CustomContextMenu)
    app.video_list.customContextMenuRequested.connect(lambda pos: show_context_menu(app, pos))

    def on_video_selected(item):
        app.placeholder_label.hide()
        app.video_widget.show()
        apply_practice_preset(app, item)
        play_selected_video(app, item)

    app.video_list.itemClicked.connect(on_video_selected)
    app.video_list.setSortingEnabled(True)
    splitter.addWidget(app.video_list)

    layout.addWidget(splitter)

    QTimer.singleShot(0, lambda: splitter.setSizes([
        int(splitter.height() * 0.7),
        int(splitter.height() * 0.3),
    ]))

    app.video_widget.hide()
    app.placeholder_label.show()

    def keyPressEvent(event):
        if event.key() == Qt.Key_Space:
            if app.media_player.state() == QMediaPlayer.PlayingState:
                app.media_player.pause()
                if getattr(app, "vlc_player", None):
                    app.vlc_player.pause()
            else:
                app.media_player.play()
                if getattr(app, "vlc_player", None):
                    app.vlc_player.play()
            event.accept()
        else:
            QWidget.keyPressEvent(widget, event)

    widget.keyPressEvent = keyPressEvent
    widget.setFocusPolicy(Qt.StrongFocus)
    widget.setFocus()

    return widget


def extract_lesson_number_from_item(item):
    try:
        value = item.data(Qt.UserRole)
    except AttributeError:
        value = None
    if isinstance(value, int):
        return value

    try:
        text = item.text()
    except AttributeError:
        return None

    if ":" in text:
        prefix = text.split(":", 1)[0].strip()
        try:
            return int(prefix)
        except ValueError:
            return None
    return None


def update_detail_view(app, item):
    lesson_number = extract_lesson_number_from_item(item)
    videos = app.db.fetch_videos(lesson_number)

    # Update window title with the selected lesson label for extra context.
    try:
        label_text = item.text()
    except AttributeError:
        label_text = None
    if label_text and hasattr(app, "setWindowTitle"):
        app.setWindowTitle(f"Bouzouki Lesson Player – {label_text}")

    app.video_list.clear()
    for file_name, file_path in videos:
        list_item = QListWidgetItem(file_name)
        list_item.setData(Qt.UserRole, file_path)
        app.video_list.addItem(list_item)
    app.video_list.sortItems()


def apply_practice_preset(app, item):
    """Apply any saved practice preset for this media item to the player state."""
    if not hasattr(app, "db"):
        return
    file_path = item.data(Qt.UserRole)
    if not file_path:
        return

    preset = app.db.get_practice_preset(file_path)
    if not preset:
        if hasattr(app, "practice_status_label"):
            app.practice_status_label.setText("")
        if hasattr(app, "_set_status_message"):
            app._set_status_message("Preset cleared")
        return

    # Transpose
    transpose_steps = preset["transpose_steps"]
    if transpose_steps is not None and hasattr(app, "transpose_steps"):
        app.transpose_steps = int(transpose_steps)
        app.apply_transposition()

    # Loop section
    loop_start = preset["loop_start_ms"]
    loop_end = preset["loop_end_ms"]
    if loop_start is not None and loop_end is not None:
        if hasattr(app, "loop_start_ms") and hasattr(app, "loop_end_ms"):
            app.loop_start_ms = int(loop_start)
            app.loop_end_ms = int(loop_end)

    # Groove: store as first tag in lesson metadata if present
    groove = preset["metronome_groove"]
    if groove:
        try:
            row = app.db.get_lesson_metadata(file_path)
        except Exception:
            row = None
        tags_text = groove
        if row and row["tags"]:
            # Keep existing tags but ensure groove is first token when present
            parts = [groove] + [p for p in str(row["tags"]).split(",") if p.strip() and p.strip() != groove]
            tags_text = ", ".join(parts)
        app.db.update_lesson_metadata(file_path, None, None, tags_text)
    status_text = "Preset on"
    if hasattr(app, "practice_status_label"):
        app.practice_status_label.setText(status_text)
    if hasattr(app, "_set_status_message"):
        app._set_status_message(status_text)


def play_selected_video(app, item):
    file_path = item.data(Qt.UserRole)
    if not file_path:
        QMessageBox.warning(app, "Error", "Could not determine file path.")
        return
    if not os.path.exists(file_path):
        QMessageBox.warning(app, "Error", f"File not found:\n{file_path}")
        return

    app.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))

    if getattr(app, "vlc_player", None):
        app.vlc_player.set_media(file_path)
        app.vlc_player.play()
        app.media_player.play()
    else:
        app.media_player.play()


def open_file_in_explorer(app, item):
    file_name = item.text()
    file_path = item.data(Qt.UserRole)
    if not file_path:
        return

    folder_path = os.path.dirname(file_path)

    if platform.system() == "Windows":
        subprocess.Popen(f'explorer /select,"{file_path}"')
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", "-R", file_path])
    else:
        if os.environ.get("XDG_CURRENT_DESKTOP") == "KDE":
            subprocess.Popen(["dolphin", "--select", file_path])
        elif os.environ.get("XDG_CURRENT_DESKTOP") in ("GNOME", "Unity", "X-Cinnamon"):
            subprocess.Popen(["nautilus", "--select", file_path])
        else:
            subprocess.Popen(["xdg-open", folder_path])


def open_metronome_for_item(app, item):
    """Launch the metronome app pre-configured for this lesson if possible."""
    file_path = item.data(Qt.UserRole)
    if not file_path or not hasattr(app, "db"):
        return

    tempo_arg = None
    groove_arg = None

    # Prefer practice preset when available, fall back to lesson metadata.
    preset = None
    try:
        preset = app.db.get_practice_preset(file_path)
    except Exception:
        preset = None

    if preset:
        if preset["tempo"] is not None:
            tempo_arg = str(int(preset["tempo"]))
        if preset["metronome_groove"]:
            groove_arg = str(preset["metronome_groove"])
    else:
        try:
            row = app.db.get_lesson_metadata(file_path)
        except Exception:
            row = None

        if row:
            tempo_val = row["tempo"]
            if tempo_val is not None:
                tempo_arg = str(int(tempo_val))
            tags_val = row["tags"]
            if tags_val:
                first_tag = str(tags_val).split(",")[0].strip()
                if first_tag:
                    groove_arg = first_tag

    cmd = [sys.executable or "python", "-m", "metronome.metronome"]
    if tempo_arg is not None:
        cmd.extend(["--tempo", tempo_arg])
    if groove_arg is not None:
        cmd.extend(["--groove", groove_arg])

    try:
        subprocess.Popen(cmd)
        label = "Metronome"
        if tempo_arg is not None:
            label += f" {tempo_arg} BPM"
        if groove_arg is not None:
            label += f" ({groove_arg})"
        if hasattr(app, "practice_status_label"):
            app.practice_status_label.setText(label)
        if hasattr(app, "_set_status_message"):
            app._set_status_message(label)
    except Exception as e:
        QMessageBox.warning(
            app,
            "Metronome Error",
            f"Could not start metronome:\n{e}",
        )


def open_in_external_player(app, item):
    """Open the media file in a user-configured external player/command."""
    file_path = item.data(Qt.UserRole)
    if not file_path:
        return

    settings = QSettings("bouzouki", "lessonplayer")
    cmd_str = settings.value("external_player_command", "").strip()
    if not cmd_str:
        QMessageBox.information(
            app,
            "External Player",
            "No external player command is configured.\n"
            "Set it under Settings → External player command.",
        )
        return

    import shlex

    try:
        base_cmd = shlex.split(cmd_str)
    except ValueError:
        QMessageBox.warning(
            app,
            "External Player",
            "Invalid external player command. Please check Settings.",
        )
        return

    cmd = base_cmd + [file_path]

    try:
        subprocess.Popen(cmd)
    except Exception as e:
        QMessageBox.warning(
            app,
            "External Player Error",
            f"Could not start external player:\n{e}",
        )


def send_to_daw(app, item):
    """Send the media file to an external DAW command, if configured."""
    file_path = item.data(Qt.UserRole)
    if not file_path:
        return

    settings = QSettings("bouzouki", "lessonplayer")
    cmd_str = settings.value("daw_command", "").strip()
    if not cmd_str:
        QMessageBox.information(
            app,
            "External DAW",
            "No DAW command is configured.\n"
            "Set it under Settings → DAW command.",
        )
        return

    import shlex

    try:
        base_cmd = shlex.split(cmd_str)
    except ValueError:
        QMessageBox.warning(
            app,
            "External DAW",
            "Invalid DAW command. Please check Settings.",
        )
        return

    cmd = base_cmd + [file_path]

    try:
        subprocess.Popen(cmd)
    except Exception as e:
        QMessageBox.warning(
            app,
            "External DAW Error",
            f"Could not send file to DAW:\n{e}",
        )


def rename_file(app, item):
    file_path = item.data(Qt.UserRole)
    file_name = item.text()
    if not file_path:
        return

    new_name, ok = QInputDialog.getText(app, "Rename File", "Enter new file name:", text=file_name)
    if not ok or not new_name.strip():
        return

    new_name = new_name.strip()
    new_path = os.path.join(os.path.dirname(file_path), new_name)

    try:
        os.rename(file_path, new_path)
        app.db.update_file_entry(file_path, new_name, new_path)
        update_detail_view(app, app.master_list.currentItem())
        QMessageBox.information(app, "Renamed", f"File renamed to:\n{new_name}")
    except Exception as e:
        QMessageBox.warning(app, "Rename Failed", f"Could not rename file:\n{e}")


def delete_file(app, item):
    file_path = item.data(Qt.UserRole)
    file_name = item.text()
    if not file_path:
        return

    confirm = QMessageBox.question(
        app,
        "Delete File",
        f"Are you sure you want to delete:\n{file_name}?",
        QMessageBox.Yes | QMessageBox.No,
    )
    if confirm != QMessageBox.Yes:
        return

    try:
        os.remove(file_path)
        app.db.delete_file_entry(file_path)
        update_detail_view(app, app.master_list.currentItem())
        QMessageBox.information(app, "Deleted", f"File deleted:\n{file_name}")
    except Exception as e:
        QMessageBox.warning(app, "Delete Failed", f"Could not delete file:\n{e}")


def edit_metadata(app, item):
    """Basic metadata editor for a lesson entry (title, tempo, tags)."""
    file_path = item.data(Qt.UserRole)
    if not file_path or not hasattr(app, "db"):
        return

    row = app.db.get_lesson_metadata(file_path)
    current_title = row["lesson_name"] if row and row["lesson_name"] else item.text()
    current_tempo = "" if not row or row["tempo"] is None else str(row["tempo"])
    current_tags = "" if not row or row["tags"] is None else str(row["tags"])

    title, ok = QInputDialog.getText(
        app,
        "Edit Title",
        "Lesson title:",
        text=current_title,
    )
    if not ok:
        return
    title = title.strip() or None

    tempo_text, ok = QInputDialog.getText(
        app,
        "Edit Tempo",
        "Tempo (BPM, optional):",
        text=current_tempo,
    )
    if not ok:
        return
    tempo_text = tempo_text.strip()
    if tempo_text:
        try:
            tempo_val = int(tempo_text)
            if tempo_val <= 0:
                raise ValueError("Tempo must be positive")
        except ValueError:
            QMessageBox.warning(
                app,
                "Invalid Tempo",
                "Tempo must be a positive integer (BPM) or left blank.",
            )
            return
    else:
        tempo_val = None

    tags_text, ok = QInputDialog.getText(
        app,
        "Edit Tags",
        "Tags (comma-separated, optional):",
        text=current_tags,
    )
    if not ok:
        return
    tags_text = tags_text.strip() or None

    try:
        app.db.update_lesson_metadata(file_path, title, tempo_val, tags_text)
        if title:
            item.setText(title)
        QMessageBox.information(app, "Metadata Updated", "Lesson metadata has been updated.")
    except Exception as e:
        QMessageBox.warning(app, "Update Failed", f"Could not update metadata:\n{e}")


def relink_file(app, item):
    """Allow the user to re-link a missing or moved media file.

    Uses the existing DB entry keyed by file_path and updates it
    to point to a new path chosen by the user.
    """
    file_path = item.data(Qt.UserRole)
    file_name = item.text()
    if not file_path:
        return

    if os.path.exists(file_path):
        confirm = QMessageBox.question(
            app,
            "Re-link File",
            f"The file appears to exist on disk:\n{file_path}\n\n"
            "Do you still want to re-link it to a different location?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

    new_path, _ = QFileDialog.getOpenFileName(
        app,
        "Select Replacement File",
        os.path.dirname(file_path),
        "Media Files (*.mp3 *.mp4 *.mkv);;All Files (*)",
    )
    if not new_path:
        return

    new_name = os.path.basename(new_path)
    try:
        app.db.update_file_entry(file_path, new_name, new_path)
        item.setText(new_name)
        item.setData(Qt.UserRole, new_path)
        QMessageBox.information(
            app,
            "File Re-linked",
            f"Updated lesson entry to:\n{new_path}",
        )
    except Exception as e:
        QMessageBox.warning(app, "Re-link Failed", f"Could not update file entry:\n{e}")


def save_practice_preset(app, item):
    """Persist the current practice configuration for this media item."""
    if not hasattr(app, "db"):
        return
    file_path = item.data(Qt.UserRole)
    if not file_path:
        return

    tempo_val = None
    groove = None

    # Use lesson metadata tempo/tags when available.
    try:
        row = app.db.get_lesson_metadata(file_path)
    except Exception:
        row = None

    if row:
        if row["tempo"] is not None:
            tempo_val = int(row["tempo"])
        tags_val = row["tags"]
        if tags_val:
            groove = str(tags_val).split(",")[0].strip() or None

    transpose_steps = getattr(app, "transpose_steps", None)
    loop_start = getattr(app, "loop_start_ms", None)
    loop_end = getattr(app, "loop_end_ms", None)

    try:
        app.db.save_practice_preset(
            file_path=file_path,
            tempo=tempo_val,
            transpose_steps=transpose_steps,
            loop_start_ms=loop_start,
            loop_end_ms=loop_end,
            groove=groove,
        )
        QMessageBox.information(
            app,
            "Preset Saved",
            "Practice preset saved for this song.",
        )
        status_text = "Preset on"
        if hasattr(app, "practice_status_label"):
            app.practice_status_label.setText(status_text)
        if hasattr(app, "_set_status_message"):
            app._set_status_message(status_text)
    except Exception as e:
        QMessageBox.warning(app, "Save Failed", f"Could not save practice preset:\n{e}")


def reset_practice_preset(app, item):
    """Clear any saved practice preset for this media item."""
    if not hasattr(app, "db"):
        return
    file_path = item.data(Qt.UserRole)
    if not file_path:
        return

    try:
        # Delete any preset row for this file_path. The practice_presets
        # table uses file_path as a unique key.
        cur = app.db.conn.cursor()
        cur.execute("DELETE FROM practice_presets WHERE file_path = ?", (file_path,))
        app.db.conn.commit()
        if hasattr(app, "practice_status_label"):
            app.practice_status_label.setText("")
        QMessageBox.information(
            app,
            "Preset Reset",
            "Practice preset cleared for this song.",
        )
    except Exception as e:
        QMessageBox.warning(app, "Reset Failed", f"Could not reset practice preset:\n{e}")


def copy_path_to_clipboard(app, item):
    file_path = item.data(Qt.UserRole)
    if not file_path:
        return
    clipboard = QApplication.clipboard()
    clipboard.setText(file_path)
    QMessageBox.information(app, "Path Copied", f"Path copied to clipboard:\n{file_path}")


def show_context_menu(app, pos):
    item = app.video_list.itemAt(pos)
    if not item:
        return

    menu = QMenu()

    menu.addAction("Play", lambda: play_selected_video(app, item))
    menu.addSeparator()

    menu.addAction("Open Metronome", lambda: open_metronome_for_item(app, item))
    menu.addAction("Save Practice Preset", lambda: save_practice_preset(app, item))
    menu.addAction("Reset Practice Preset", lambda: reset_practice_preset(app, item))
    menu.addAction("Open in File Manager", lambda: open_file_in_explorer(app, item))
    menu.addAction("Open in External Player", lambda: open_in_external_player(app, item))
    menu.addAction("Send to DAW", lambda: send_to_daw(app, item))
    menu.addAction("Edit Metadata...", lambda: edit_metadata(app, item))
    menu.addAction("Re-link File...", lambda: relink_file(app, item))
    menu.addAction("Rename", lambda: rename_file(app, item))
    menu.addAction("Delete", lambda: delete_file(app, item))
    menu.addAction("Copy File Path", lambda: copy_path_to_clipboard(app, item))

    menu.exec_(app.video_list.mapToGlobal(pos))
