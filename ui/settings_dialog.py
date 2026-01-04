from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QDialogButtonBox,
    QFileDialog,
    QComboBox,
)
from PyQt5.QtCore import QSettings


class SettingsDialog(QDialog):
    """Application settings for paths, audio, scan folders, metronome, and telemetry."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = QSettings("bouzouki", "lessonplayer")
        self._init_ui()
        self._load()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # Media library path
        media_row = QHBoxLayout()
        media_row.addWidget(QLabel("Media library path:"))
        self.media_path_edit = QLineEdit()
        browse_media_btn = QPushButton("Browse...")
        browse_media_btn.clicked.connect(self._browse_media_path)
        media_row.addWidget(self.media_path_edit, 1)
        media_row.addWidget(browse_media_btn)
        layout.addLayout(media_row)

        # Default scan folder
        scan_row = QHBoxLayout()
        scan_row.addWidget(QLabel("Default scan folder:"))
        self.scan_path_edit = QLineEdit()
        browse_scan_btn = QPushButton("Browse...")
        browse_scan_btn.clicked.connect(self._browse_scan_path)
        scan_row.addWidget(self.scan_path_edit, 1)
        scan_row.addWidget(browse_scan_btn)
        layout.addLayout(scan_row)

        # Preferred audio device (name only; not wired yet)
        audio_row = QHBoxLayout()
        audio_row.addWidget(QLabel("Preferred audio device (name):"))
        self.audio_device_edit = QLineEdit()
        audio_row.addWidget(self.audio_device_edit, 1)
        layout.addLayout(audio_row)

        # External tools
        ext_row = QHBoxLayout()
        ext_row.addWidget(QLabel("External player command:"))
        self.external_player_edit = QLineEdit()
        ext_row.addWidget(self.external_player_edit, 1)
        layout.addLayout(ext_row)

        daw_row = QHBoxLayout()
        daw_row.addWidget(QLabel("DAW command:"))
        self.daw_command_edit = QLineEdit()
        daw_row.addWidget(self.daw_command_edit, 1)
        layout.addLayout(daw_row)

        # Metronome options
        metronome_row = QHBoxLayout()
        metronome_row.addWidget(QLabel("Metronome default tempo (BPM):"))
        self.metronome_tempo_spin = QSpinBox()
        self.metronome_tempo_spin.setRange(40, 300)
        metronome_row.addWidget(self.metronome_tempo_spin)
        layout.addLayout(metronome_row)

        metronome_sound_row = QHBoxLayout()
        metronome_sound_row.addWidget(QLabel("Metronome sound profile:"))
        self.metronome_sound_combo = QComboBox()
        self.metronome_sound_combo.addItem("Classic", "classic")
        self.metronome_sound_combo.addItem("Soft", "soft")
        self.metronome_sound_combo.addItem("Wood", "wood")
        self.metronome_sound_combo.addItem("Clave", "clave")
        self.metronome_sound_combo.addItem("Metal", "metal")
        metronome_sound_row.addWidget(self.metronome_sound_combo, 1)
        layout.addLayout(metronome_sound_row)

        self.metronome_count_in_check = QCheckBox("Enable metronome count-in (where supported)")
        layout.addWidget(self.metronome_count_in_check)

        # Audio enhancements / telemetry
        self.low_speed_eq_check = QCheckBox("Enhance clarity at low speeds (EQ hint)")
        layout.addWidget(self.low_speed_eq_check)

        self.telemetry_check = QCheckBox("Enable local usage telemetry")
        layout.addWidget(self.telemetry_check)

        # Layout options
        self.compact_layout_check = QCheckBox("Use compact layout (reduced margins)")
        layout.addWidget(self.compact_layout_check)

        # Language selection (infrastructure only; requires .qm files)
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("Language (requires restart):"))
        self.language_combo = QComboBox()
        self.language_combo.addItem("System default", "")
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Greek (placeholder)", "el")
        lang_row.addWidget(self.language_combo, 1)
        layout.addLayout(lang_row)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse_media_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Media Library")
        if path:
            self.media_path_edit.setText(path)

    def _browse_scan_path(self):
        base = self.media_path_edit.text() or ""
        path = QFileDialog.getExistingDirectory(self, "Select Default Scan Folder", base)
        if path:
            self.scan_path_edit.setText(path)

    def _load(self):
        self.media_path_edit.setText(self.settings.value("media_library_path", ""))
        self.scan_path_edit.setText(self.settings.value("default_scan_folder", ""))
        self.audio_device_edit.setText(self.settings.value("audio_device_name", ""))
        self.external_player_edit.setText(self.settings.value("external_player_command", ""))
        self.daw_command_edit.setText(self.settings.value("daw_command", ""))

        tempo = self.settings.value("metronome_default_tempo", 120)
        try:
            tempo = int(tempo)
        except (TypeError, ValueError):
            tempo = 120
        self.metronome_tempo_spin.setValue(tempo)

        sound_profile = self.settings.value("metronome_sound_profile", "classic")
        if sound_profile not in ("classic", "soft", "wood", "clave", "metal"):
            sound_profile = "classic"
        idx_sound = self.metronome_sound_combo.findData(sound_profile)
        if idx_sound != -1:
            self.metronome_sound_combo.setCurrentIndex(idx_sound)

        count_in = self.settings.value("metronome_count_in_enabled", False)
        if not isinstance(count_in, bool):
            count_in = str(count_in).lower() in ("true", "1", "yes")
        self.metronome_count_in_check.setChecked(count_in)

        low_speed_eq = self.settings.value("low_speed_eq_enabled", False)
        if not isinstance(low_speed_eq, bool):
            low_speed_eq = str(low_speed_eq).lower() in ("true", "1", "yes")
        self.low_speed_eq_check.setChecked(low_speed_eq)

        telemetry = self.settings.value("telemetry_enabled", False)
        if not isinstance(telemetry, bool):
            telemetry = str(telemetry).lower() in ("true", "1", "yes")
        self.telemetry_check.setChecked(telemetry)

        compact = self.settings.value("compact_layout_enabled", False)
        if not isinstance(compact, bool):
            compact = str(compact).lower() in ("true", "1", "yes")
        self.compact_layout_check.setChecked(compact)

        lang_code = self.settings.value("language_code", "")
        idx = self.language_combo.findData(lang_code)
        if idx != -1:
            self.language_combo.setCurrentIndex(idx)

    def accept(self):
        self._save()
        super().accept()

    def _save(self):
        self.settings.setValue("media_library_path", self.media_path_edit.text().strip())
        self.settings.setValue("default_scan_folder", self.scan_path_edit.text().strip())
        self.settings.setValue("audio_device_name", self.audio_device_edit.text().strip())
        self.settings.setValue("external_player_command", self.external_player_edit.text().strip())
        self.settings.setValue("daw_command", self.daw_command_edit.text().strip())
        self.settings.setValue("metronome_default_tempo", self.metronome_tempo_spin.value())
        self.settings.setValue("metronome_sound_profile", self.metronome_sound_combo.currentData())
        self.settings.setValue("metronome_count_in_enabled", self.metronome_count_in_check.isChecked())
        self.settings.setValue("low_speed_eq_enabled", self.low_speed_eq_check.isChecked())
        self.settings.setValue("telemetry_enabled", self.telemetry_check.isChecked())
        self.settings.setValue("compact_layout_enabled", self.compact_layout_check.isChecked())
        self.settings.setValue("language_code", self.language_combo.currentData())
