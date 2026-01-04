import os
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QLabel,
)
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtGui import QIcon

from ui.menu_bar import create_menu_bar
from ui.widgets.master_detail import init_master_detail


class LessonPlayerApp(QMainWindow):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.conn = None
        self.current_speed = 1.0
        self.transpose_steps = 0
        self.loop_enabled = False
        self.loop_start_ms = None
        self.loop_end_ms = None
        # Will be set by detail view if VLC backend is enabled
        self.vlc_player = None
        self.eq_profile_active = False

        self.setWindowTitle("Bouzouki Lesson Player")
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(960, 540)
        icon_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "resources", "bouzouki.png",
        ))
        self.setWindowIcon(QIcon(icon_path))

        self._init_status_bar()
        self._init_main_ui()
        self._init_feedback_overlay()
        self._init_count_in_settings()

    def _init_status_bar(self):
        self.status_bar = QStatusBar()
        self.status_message = QLabel("Ready")
        self.status_bar.addWidget(self.status_message)
        self.setStatusBar(self.status_bar)

    def _set_status_message(self, text: str):
        if hasattr(self, "status_message"):
            backend = "VLC" if getattr(self, "vlc_player", None) else "Qt"
            suffix = ""
            if backend == "VLC" and getattr(self, "eq_profile_active", False):
                suffix = "+EQ"
            self.status_message.setText(f"[{backend}{suffix}] {text}")

    def _init_main_ui(self):
        self.setMenuBar(create_menu_bar(self))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)

        settings = QSettings("bouzouki", "lessonplayer")
        compact_val = settings.value("compact_layout_enabled", False)
        if isinstance(compact_val, bool):
            compact = compact_val
        else:
            compact = str(compact_val).lower() in ("true", "1", "yes")

        if compact:
            layout.setContentsMargins(4, 4, 4, 4)
            layout.setSpacing(4)
        else:
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(8)

        master_detail_widget = init_master_detail(self)
        layout.addWidget(master_detail_widget)

    def closeEvent(self, event):
        if self.conn:
            self.conn.close()
        event.accept()

    # Playback Controls
    def play_video(self):
        if not hasattr(self, "media_player"):
            return

        # Preserve old behaviour for test stubs that call the unbound method.
        if not isinstance(self, LessonPlayerApp):
            self._start_playback_immediately()
            return

        if getattr(self, "count_in_enabled", False):
            # Only start count-in when not already active and not already playing.
            if not self._count_in_active and self.media_player.state() != QMediaPlayer.PlayingState:
                self._run_count_in_and_start()
                return

        self._start_playback_immediately()

    def pause_video(self):
        if hasattr(self, "media_player"):
            self.media_player.pause()
            if hasattr(self, "vlc_player") and getattr(self, "vlc_player", None):
                self.vlc_player.pause()
            self._set_status_message("Pause")

    def stop_video(self):
        if hasattr(self, "media_player"):
            self.media_player.stop()
            if hasattr(self, "vlc_player") and getattr(self, "vlc_player", None):
                self.vlc_player.stop()
            self.transpose_steps = 0
            self.apply_transposition()
            self._set_status_message("Stop")

    # Loop / A–B Repeat Controls
    def set_loop_start(self):
        if not hasattr(self, "media_player"):
            return
        self.loop_start_ms = self.media_player.position()
        self._set_status_message("Loop start (A) set")
        self.show_feedback("Loop A set")

    def set_loop_end(self):
        if not hasattr(self, "media_player"):
            return
        current_pos = self.media_player.position()
        if self.loop_start_ms is not None and current_pos <= self.loop_start_ms:
            self.show_feedback("Loop B must be after A")
            return
        self.loop_end_ms = current_pos
        self._set_status_message("Loop end (B) set")
        self.show_feedback("Loop B set")

    def toggle_loop(self):
        if not hasattr(self, "media_player"):
            return
        if not self.loop_enabled:
            if self.loop_start_ms is None or self.loop_end_ms is None:
                self.show_feedback("Set A and B before enabling loop")
                return
            self.loop_enabled = True
            self._set_status_message("Loop enabled")
            self.show_feedback("Loop ON")
        else:
            self.loop_enabled = False
            self._set_status_message("Loop disabled")
            self.show_feedback("Loop OFF")

    def handle_position_changed(self, pos: int):
        # Update progress slider if present
        if hasattr(self, "progress_bar"):
            self.progress_bar.setValue(pos)

        # Apply loop logic when enabled
        if (
            getattr(self, "loop_enabled", False)
            and self.loop_start_ms is not None
            and self.loop_end_ms is not None
        ):
            if pos >= self.loop_end_ms:
                self.media_player.setPosition(self.loop_start_ms)

    # Navigation and Volume
    def seek_forward_5s(self):
        if not hasattr(self, "media_player"):
            return
        new_pos = self.media_player.position() + 5000
        self.media_player.setPosition(new_pos)
        self.show_feedback("⏩ +5s")

    def seek_back_5s(self):
        if not hasattr(self, "media_player"):
            return
        new_pos = self.media_player.position() - 5000
        self.media_player.setPosition(max(0, new_pos))
        self.show_feedback("⏪ -5s")

    def volume_up_small(self):
        if hasattr(self, "volume_slider"):
            new_volume = min(100, self.volume_slider.value() + 5)
            self.volume_slider.setValue(new_volume)
            self.show_feedback(f"🔊 Volume: {new_volume}")

    def volume_down_small(self):
        if hasattr(self, "volume_slider"):
            new_volume = max(0, self.volume_slider.value() - 5)
            self.volume_slider.setValue(new_volume)
            self.show_feedback(f"🔉 Volume: {new_volume}")

    # Transposition Controls
    def transpose_up(self):
        self.transpose_steps += 1
        self.apply_transposition()

    def transpose_down(self):
        self.transpose_steps -= 1
        self.apply_transposition()

    def apply_transposition(self):
        if not hasattr(self, "media_player"):
            return
        from core.media_utils import HALF_TONE_UP_FACTOR

        if getattr(self, "vlc_player", None):
            # With VLC audio backend:
            # - Video speed should be controlled only by current_speed.
            # - Pitch (transpose) is applied separately via VLC.
            self.media_player.setPlaybackRate(self.current_speed)
            self.vlc_player.set_rate(self.current_speed)
            if hasattr(self.vlc_player, "set_pitch_semitones"):
                self.vlc_player.set_pitch_semitones(self.transpose_steps)
            # Optional clarity enhancement EQ at low speeds
            if hasattr(self.vlc_player, "set_eq_profile"):
                if getattr(self, "low_speed_eq_enabled", False) and self.current_speed < 0.75:
                    self.vlc_player.set_eq_profile("low_speed_clarity")
                    self.eq_profile_active = True
                else:
                    self.vlc_player.set_eq_profile(None)
                    self.eq_profile_active = False
        else:
            # Qt-only backend: combine speed and transpose in playbackRate
            rate = self.current_speed * (HALF_TONE_UP_FACTOR ** self.transpose_steps)
            self.media_player.setPlaybackRate(rate)
            self.eq_profile_active = False

        sign = "+" if self.transpose_steps > 0 else ""
        if hasattr(self, "transpose_label"):
            self.transpose_label.setText(f"{sign}{self.transpose_steps}")

    def keyPressEvent(self, event):
        if not hasattr(self, "media_player"):
            return

        key = event.key()

        if key == Qt.Key_Space:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.pause_video()
            else:
                self.play_video()

        elif key == Qt.Key_Right:
            self.seek_forward_5s()

        elif key == Qt.Key_Left:
            self.seek_back_5s()

        elif key == Qt.Key_Up:
            self.volume_up_small()

        elif key == Qt.Key_Down:
            self.volume_down_small()

    def _init_feedback_overlay(self):
        self.feedback_label = QLabel("", self)
        self.feedback_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            color: white;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 16px;
        """)
        self.feedback_label.setAlignment(Qt.AlignCenter)
        self.feedback_label.setVisible(False)
        self.feedback_label.setFixedHeight(30)
        self.feedback_label.raise_()

        self.feedback_timer = QTimer(self)
        self.feedback_timer.setSingleShot(True)
        self.feedback_timer.timeout.connect(lambda: self.feedback_label.setVisible(False))

    def show_feedback(self, message: str):
        self.feedback_label.setText(message)
        self.feedback_label.adjustSize()
        self.feedback_label.move(
            int((self.width() - self.feedback_label.width()) / 2),
            int(self.height() * 0.15),
        )
        self.feedback_label.setVisible(True)
        self.feedback_timer.start(1000)

    def _init_count_in_settings(self):
        settings = QSettings("bouzouki", "lessonplayer")
        val = settings.value("metronome_count_in_enabled", False)
        if isinstance(val, bool):
            self.count_in_enabled = val
        else:
            self.count_in_enabled = str(val).lower() in ("true", "1", "yes")
        self._count_in_active = False
        eq_val = settings.value("low_speed_eq_enabled", False)
        if isinstance(eq_val, bool):
            self.low_speed_eq_enabled = eq_val
        else:
            self.low_speed_eq_enabled = str(eq_val).lower() in ("true", "1", "yes")

    def _start_playback_immediately(self):
        if hasattr(self, "media_player"):
            self.media_player.play()
            if hasattr(self, "vlc_player") and getattr(self, "vlc_player", None):
                self.vlc_player.play()
            self._set_status_message("Play")

    def _run_count_in_and_start(self):
        if self._count_in_active:
            return
        self._count_in_active = True

        beats = ["1", "2", "3", "4"]
        interval_ms = 300

        def schedule_beat(index):
            if index < len(beats):
                self.show_feedback(f"Count-in: {beats[index]}")
                QTimer.singleShot(interval_ms, lambda: schedule_beat(index + 1))
            else:
                self._count_in_active = False
                self._start_playback_immediately()

        schedule_beat(0)
