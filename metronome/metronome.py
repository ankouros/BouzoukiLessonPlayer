#!/usr/bin/env python3
"""Polyrhythmic Metronome with Visual Feedback, Swing, Presets, and Animated LEDs

This module previously attempted to auto-install dependencies (numpy,
simpleaudio, PyQt5) at runtime. That behaviour has been removed in
favour of explicit imports and clear error messages if dependencies
are missing.
"""
from __future__ import annotations

import argparse
import math
import sys
import threading
import time
import json
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import simpleaudio as sa
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import (
    QLabel,
    QWidget,
    QGraphicsOpacityEffect,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
)
from PyQt5.QtCore import QPropertyAnimation, QEasingCurve

# Constants
SR = 44100
DUR = 0.05
REG_FREQ, ACC_FREQ = 440, 880
COLORS = ["#FF4D4D", "#4D94FF", "#4DFF4D", "#FFC04D", "#D64DFF", "#4DFFFF"]

# Built-in presets
BUILTIN_PRESETS = {
    "2/4": {"pulses": 2, "accents": [0], "swing": False},
    "3/4": {"pulses": 3, "accents": [0], "swing": False},
    "4/4": {"pulses": 4, "accents": [0], "swing": False},
}

GROOVE_FILE = "metronome/grooves.json"


def load_custom_presets(filepath: str = GROOVE_FILE) -> dict[str, dict]:
    if not Path(filepath).exists():
        return {}
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if "pulses" in v and "accents" in v}
    except Exception as e:
        print(f"Failed to load custom grooves: {e}")
        return {}


PRESETS = {**BUILTIN_PRESETS, **load_custom_presets()}


def _click(freq: int, volume: float = 0.5) -> sa.WaveObject:
    """Generate a short sine click at a given frequency."""
    t = np.linspace(0, DUR, int(SR * DUR), False)
    buf = (volume * np.sin(2 * math.pi * freq * t) * (2**15 - 1)).astype(np.int16)
    return sa.WaveObject(buf.tobytes(), 1, 2, SR)


def _click_pair(reg_freq: int, acc_freq: int, volume: float = 0.5) -> Tuple[sa.WaveObject, sa.WaveObject]:
    return _click(reg_freq, volume), _click(acc_freq, volume)


# Default classic sine clicks
CLICK, ACCENT = _click_pair(REG_FREQ, ACC_FREQ, volume=0.5)
# Softer, mellower clicks
SOFT_CLICK, SOFT_ACCENT = _click_pair(330, 660, volume=0.35)
# Brighter, woodblock-style clicks
WOOD_CLICK, WOOD_ACCENT = _click_pair(1800, 2200, volume=0.4)
# Clave-like mid-high wooden clicks
CLAVE_CLICK, CLAVE_ACCENT = _click_pair(1200, 1800, volume=0.45)
# Metal/hi-hat style clicks
METAL_CLICK, METAL_ACCENT = _click_pair(3500, 5000, volume=0.4)


class RhythmThread(QtCore.QThread):
    tick = QtCore.pyqtSignal(int, bool)

    def __init__(self, pulses, accents, bpm, swing, w_r, w_a):
        super().__init__()
        self.pulses = pulses
        self.accents = set(accents)
        self.w_r = w_r
        self.w_a = w_a
        self.swing = swing
        self.set_bpm(bpm)
        self._stop = threading.Event()

    def set_bpm(self, bpm):
        self.bpm = bpm
        self.base_interval = 60.0 / bpm

    def run(self):
        beat = 0
        while not self._stop.is_set():
            is_accent = beat in self.accents
            (self.w_a if is_accent else self.w_r).play()
            self.tick.emit(beat, is_accent)

            if self.swing and beat % 2 == 0:
                interval = self.base_interval * 0.66
            elif self.swing and beat % 2 == 1:
                interval = self.base_interval * 0.34
            else:
                interval = self.base_interval

            time.sleep(interval)
            beat = (beat + 1) % self.pulses

    def stop(self):
        self._stop.set()
        self.wait()


class MetronomeVisual(QtWidgets.QWidget):
    """Simple physical metronome-style visual with a swinging pendulum."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pulses = 4
        self._beat = 0
        self._is_accent = False
        self.setMinimumHeight(160)

    def set_beat(self, beat_index: int, pulses: int, is_accent: bool) -> None:
        self._beat = beat_index
        self._pulses = max(1, pulses)
        self._is_accent = is_accent
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)

        w = self.width()
        h = self.height()

        # Draw metronome body (simple wooden trapezoid)
        base_width = int(w * 0.5)
        base_height = int(h * 0.65)
        left = (w - base_width) // 2
        right = left + base_width
        top = int(h * 0.15)
        mid = (left + right) // 2

        body = QtGui.QPolygon([
            QtCore.QPoint(mid - base_width // 4, top),
            QtCore.QPoint(right, base_height),
            QtCore.QPoint(left, base_height),
        ])
        gradient = QtGui.QLinearGradient(left, top, right, base_height)
        gradient.setColorAt(0.0, QtGui.QColor("#5D4037"))
        gradient.setColorAt(1.0, QtGui.QColor("#3E2723"))
        painter.setBrush(gradient)
        painter.setPen(QtGui.QPen(QtGui.QColor("#2D1E19"), 2))
        painter.drawPolygon(body)

        # Pendulum arm angle swings left/right across beats
        if self._pulses <= 1:
            phase = 0.0
        else:
            # Map beat index to [-1, 1] across the bar
            phase = (2.0 * (self._beat / float(self._pulses - 1)) - 1.0) if self._pulses > 1 else 0.0
        max_angle = 30  # degrees
        angle = math.radians(max_angle * phase)

        arm_length = int(h * 0.5)
        pivot = QtCore.QPoint(mid, top + int(h * 0.05))
        end_x = pivot.x() + int(math.sin(angle) * arm_length)
        end_y = pivot.y() + int(math.cos(angle) * arm_length)
        end = QtCore.QPoint(end_x, end_y)

        pen_color = QtGui.QColor("#FFD447" if self._is_accent else "#B0BEC5")
        painter.setPen(QtGui.QPen(pen_color, 4))
        painter.drawLine(pivot, end)

        # Small weight on the arm
        weight_radius = 7
        painter.setBrush(pen_color)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(end, weight_radius, weight_radius)


class MetronomeUI(QtWidgets.QWidget):
    def __init__(self, initial_tempo: Optional[int] = None, initial_groove: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("Groove Metronome")
        self.setFixedWidth(500)

        self.threads: List[RhythmThread] = []
        self.wav = None
        self.leds = []
        self.sound_profile = "classic"
        # Persist user preferences locally for the metronome
        self.settings = QtCore.QSettings("bouzouki", "metronome")

        layout = QtWidgets.QVBoxLayout(self)

        # Physical metronome-style visual at the top
        self.visual = MetronomeVisual()
        layout.addWidget(self.visual)

        bpm_box = QtWidgets.QHBoxLayout()
        self.bpm_label = QtWidgets.QLabel("BPM: 120")
        self.bpm_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, minimum=40, maximum=300, value=120)
        self.bpm_slider.valueChanged.connect(self._update_bpm)
        bpm_box.addWidget(self.bpm_label)
        bpm_box.addWidget(self.bpm_slider, 1)
        layout.addLayout(bpm_box)

        preset_box = QtWidgets.QHBoxLayout()
        self.presets = QtWidgets.QComboBox()
        self.presets.addItem("— Select Rhythm —")
        self.presets.addItems(sorted(PRESETS.keys()))
        self.presets.currentTextChanged.connect(self._set_preset)
        preset_box.addWidget(self.presets, 1)
        layout.addLayout(preset_box)

        groove_form = QtWidgets.QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Groove name")
        self.pulses_input = QSpinBox()
        self.pulses_input.setRange(1, 32)
        self.pulses_input.setValue(4)
        self.accents_input = QLineEdit()
        self.accents_input.setPlaceholderText("e.g. 0 2")
        self.swing_check = QCheckBox("Swing")
        save_btn = QPushButton("Save Groove", clicked=self._save_groove)
        groove_form.addWidget(self.name_input)
        groove_form.addWidget(self.pulses_input)
        groove_form.addWidget(self.accents_input)
        groove_form.addWidget(self.swing_check)
        groove_form.addWidget(save_btn)
        layout.addLayout(groove_form)

        self.custom_list = QListWidget()
        self._refresh_custom_list()
        layout.addWidget(self.custom_list)
        self.custom_list.itemClicked.connect(self._preview_groove)

        delete_btn = QPushButton("Delete Selected Groove", clicked=self._delete_selected_groove)
        layout.addWidget(delete_btn)

        self.led_area = QtWidgets.QHBoxLayout()
        layout.addLayout(self.led_area)

        # Sound profile selection
        sound_box = QtWidgets.QHBoxLayout()
        sound_label = QtWidgets.QLabel("Sound:")
        self.sound_profile_combo = QtWidgets.QComboBox()
        self.sound_profile_combo.addItem("Classic", userData="classic")
        self.sound_profile_combo.addItem("Soft", userData="soft")
        self.sound_profile_combo.addItem("Wood", userData="wood")
        self.sound_profile_combo.addItem("Clave", userData="clave")
        self.sound_profile_combo.addItem("Metal", userData="metal")

        def _on_sound_profile_changed(index: int) -> None:
            data = self.sound_profile_combo.itemData(index)
            if data:
                self.sound_profile = str(data)
                self.settings.setValue("sound_profile", self.sound_profile)

        self.sound_profile_combo.currentIndexChanged.connect(_on_sound_profile_changed)
        sound_box.addWidget(sound_label)
        sound_box.addWidget(self.sound_profile_combo, 1)
        layout.addLayout(sound_box)

        file_box = QtWidgets.QHBoxLayout()
        self.file_label = QtWidgets.QLabel("Default click")
        file_btn = QPushButton("Choose WAV", clicked=self._select_wav)
        file_box.addWidget(self.file_label, 1)
        file_box.addWidget(file_btn)
        layout.addLayout(file_box)

        btn_box = QtWidgets.QHBoxLayout()
        self.start_btn = QPushButton("Start", clicked=self._start)
        self.stop_btn = QPushButton("Stop", clicked=self._stop, enabled=False)
        btn_box.addWidget(self.start_btn)
        btn_box.addWidget(self.stop_btn)
        layout.addLayout(btn_box)

        # Tempo trainer: gradually increase BPM over time for practice.
        trainer_row = QtWidgets.QHBoxLayout()
        self.tempo_trainer_check = QCheckBox("Tempo Trainer (+2 BPM every 10s)")
        trainer_row.addWidget(self.tempo_trainer_check)
        layout.addLayout(trainer_row)
        self.trainer_timer = QtCore.QTimer(self)
        self.trainer_timer.timeout.connect(self._trainer_step)

        # Apply initial tempo/groove if provided, otherwise use last/default
        if initial_tempo is not None:
            clamped = max(40, min(300, int(initial_tempo)))
            self.bpm_slider.setValue(clamped)
        else:
            # Fall back to last used tempo or app-level default if present
            saved_tempo = self.settings.value("last_tempo", None)
            if saved_tempo is not None:
                try:
                    clamped = max(40, min(300, int(saved_tempo)))
                    self.bpm_slider.setValue(clamped)
                except (TypeError, ValueError):
                    pass
        if initial_groove:
            idx = self.presets.findText(initial_groove)
            if idx != -1:
                self.presets.setCurrentIndex(idx)

        # Restore last used sound profile if present
        # Prefer app-level configured profile when available
        app_profile = QtCore.QSettings("bouzouki", "lessonplayer").value("metronome_sound_profile", None)
        saved_profile = app_profile or self.settings.value("sound_profile", "classic")
        if saved_profile not in ("classic", "soft", "wood", "clave", "metal"):
            saved_profile = "classic"
        self.sound_profile = saved_profile
        for i in range(self.sound_profile_combo.count()):
            if self.sound_profile_combo.itemData(i) == saved_profile:
                self.sound_profile_combo.setCurrentIndex(i)
                break

    def _update_bpm(self, bpm):
        self.bpm_label.setText(f"BPM: {bpm}")
        for t in self.threads:
            t.set_bpm(bpm)
        self.settings.setValue("last_tempo", int(bpm))

    def _set_preset(self, name):
        preset = PRESETS.get(name)
        if not preset:
            return
        self._stop()
        self._preview_rhythm(preset["pulses"], preset["accents"])

    def _save_groove(self):
        name = self.name_input.text().strip()
        if not name:
            return
        pulses = self.pulses_input.value()
        try:
            accents = list(map(int, self.accents_input.text().strip().split()))
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "Accents must be space-separated integers.")
            return
        swing = self.swing_check.isChecked()
        new_groove = {"pulses": pulses, "accents": accents, "swing": swing}
        try:
            grooves = load_custom_presets()
            grooves[name] = new_groove
            with open(GROOVE_FILE, "w") as f:
                json.dump(grooves, f, indent=2)
            PRESETS[name] = new_groove
            self.presets.addItem(name)
            self._refresh_custom_list()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save groove: {e}")

    def _refresh_custom_list(self):
        self.custom_list.clear()
        grooves = load_custom_presets()
        for name in sorted(grooves):
            self.custom_list.addItem(name)

    def _delete_selected_groove(self):
        item = self.custom_list.currentItem()
        if not item:
            return
        name = item.text()
        try:
            grooves = load_custom_presets()
            if name in grooves:
                del grooves[name]
                with open(GROOVE_FILE, "w") as f:
                    json.dump(grooves, f, indent=2)
                PRESETS.pop(name, None)
                self.presets.removeItem(self.presets.findText(name))
                self._refresh_custom_list()
                self._clear_leds()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to delete groove: {e}")

    def _preview_groove(self, item):
        name = item.text()
        groove = PRESETS.get(name)
        if groove:
            self._preview_rhythm(groove["pulses"], groove["accents"])

    def _preview_rhythm(self, pulses, accents):
        self._stop()
        self._clear_leds()
        color = COLORS[0]
        for i in range(pulses):
            led = QLabel()
            led.setFixedSize(24, 24)
            led.setStyleSheet(f"background:{color};border-radius:12px;")
            effect = QGraphicsOpacityEffect()
            opacity = 1.0 if i in accents else 0.3
            effect.setOpacity(opacity)
            led.setGraphicsEffect(effect)
            self.led_area.addWidget(led)
            self.leds.append((led, effect))

    def _select_wav(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select WAV", str(Path.home()), "WAV (*.wav)")
        self.wav = sa.WaveObject.from_wave_file(p) if p else None
        self.file_label.setText(Path(p).name if p else "Default click")

    def _resolve_wave_objects(self) -> Tuple[sa.WaveObject, sa.WaveObject]:
        """Return (regular, accent) WaveObjects based on current sound settings."""
        if self.wav:
            return self.wav, self.wav

        profile = getattr(self, "sound_profile", "classic")
        if profile == "soft":
            return SOFT_CLICK, SOFT_ACCENT
        if profile == "wood":
            return WOOD_CLICK, WOOD_ACCENT
        if profile == "clave":
            return CLAVE_CLICK, CLAVE_ACCENT
        if profile == "metal":
            return METAL_CLICK, METAL_ACCENT
        # Fallback to classic
        return CLICK, ACCENT

    def _start(self):
        preset = PRESETS.get(self.presets.currentText())
        if not preset:
            QtWidgets.QMessageBox.warning(self, "Select Preset", "Please select a valid preset.")
            return
        self._stop()
        pulses = preset["pulses"]
        accents = preset["accents"]
        swing = preset.get("swing", False)
        bpm = self.bpm_slider.value()
        w_r, w_a = self._resolve_wave_objects()
        thread = RhythmThread(pulses, accents, bpm, swing, w_r, w_a)
        thread.tick.connect(self._flash_led)
        thread.start()
        self.threads.append(thread)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def _flash_led(self, beat_idx: int, acc: bool):
        if not self.leds:
            return
        beat_idx %= len(self.leds)
        led, effect = self.leds[beat_idx]
        # Update physical visual as well
        if hasattr(self, "visual"):
            self.visual.set_beat(beat_idx, len(self.leds), acc)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(250)
        anim.setStartValue(1.0 if acc else 0.6)
        anim.setEndValue(0.3)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        if acc:
            self._flash_window_background()

    def _flash_window_background(self):
        self.setStyleSheet("background-color: #FFE066;")
        QtCore.QTimer.singleShot(150, lambda: self.setStyleSheet(""))

    def _stop(self):
        for t in self.threads:
            t.stop()
        self.threads.clear()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.trainer_timer.stop()

    def _clear_leds(self):
        while self.led_area.count():
            item = self.led_area.takeAt(0)
            item.widget().deleteLater()
        self.leds.clear()

    def closeEvent(self, e):
        self._stop()
        e.accept()

    def _trainer_step(self):
        """Increment tempo periodically when Tempo Trainer is enabled."""
        if not self.threads or not self.tempo_trainer_check.isChecked():
            self.trainer_timer.stop()
            return
        new_bpm = min(300, self.bpm_slider.value() + 2)
        self.bpm_slider.setValue(new_bpm)


def main(tempo: Optional[int] = None, groove: Optional[str] = None) -> None:
    """Start the metronome UI with optional initial tempo/groove."""
    try:
        app = QtWidgets.QApplication(sys.argv)
    except Exception as e:
        print(f"Failed to start Qt application: {e}")
        sys.exit(1)
    ui = MetronomeUI(initial_tempo=tempo, initial_groove=groove)
    ui.show()
    sys.exit(app.exec_())


def cli() -> None:
    """Entry point with dependency error handling.

    Separated from the `__main__` block so it can be tested directly.
    """
    parser = argparse.ArgumentParser(description="Groove Metronome")
    parser.add_argument(
        "--tempo",
        type=int,
        default=None,
        help="Initial tempo in BPM (optional)",
    )
    parser.add_argument(
        "--groove",
        type=str,
        default=None,
        help="Initial groove/preset name (optional)",
    )
    args = parser.parse_args()

    try:
        main(tempo=args.tempo, groove=args.groove)
    except ImportError as exc:
        # Handle missing runtime dependencies more gracefully
        print("Metronome dependencies are missing. Please install requirements including:")
        print("  numpy, simpleaudio, PyQt5")
        print(f"Details: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
