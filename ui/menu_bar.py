import json
from pathlib import Path
import shutil
import zipfile
import subprocess
import sys

from PyQt5.QtWidgets import QMenuBar, QMenu, QAction, QMessageBox, QApplication, QFileDialog
from PyQt5.QtCore import QSettings

from ui.searchUpdateDatabase import FolderScannerWindow
from core.theme_manager import get_available_themes, load_theme
from core.config import USE_VLC_BACKEND
from core.lesson_sets import export_all_lessons, import_lessons
from ui.settings_dialog import SettingsDialog


def create_menu_bar(parent):
    menu_bar = QMenuBar(parent)

    # --- FILE Menu ---
    file_menu = QMenu("File", parent)

    search_media_action = file_menu.addAction(
        "Search Media", lambda: FolderScannerWindow(parent.db_path, parent).exec_()
    )
    search_media_action.setShortcut("Ctrl+F")

    manage_folders_action = file_menu.addAction(
        "Manage Scan Folders", lambda: FolderScannerWindow(parent.db_path, parent).exec_()
    )
    manage_folders_action.setShortcut("Ctrl+Shift+F")

    # Focus search bar in the master panel (if available)
    focus_search_action = file_menu.addAction(
        "Focus Search", lambda: getattr(parent, "search_bar", None)
        and parent.search_bar.setFocus()
    )
    focus_search_action.setShortcut("Ctrl+L")

    file_menu.addSeparator()

    backup_action = file_menu.addAction("Backup Library...", lambda: backup_library(parent))
    restore_action = file_menu.addAction("Restore Library...", lambda: restore_library(parent))
    file_menu.addSeparator()

    file_menu.addAction("Export Lessons...", lambda: export_lessons_from_ui(parent))
    file_menu.addAction("Import Lessons...", lambda: import_lessons_from_ui(parent))
    file_menu.addSeparator()

    file_menu.addAction("Settings...", lambda: open_settings_dialog(parent))
    file_menu.addSeparator()

    exit_action = file_menu.addAction("Exit", parent.close)
    exit_action.setShortcut("Ctrl+Q")
    menu_bar.addMenu(file_menu)

    # --- PLAYBACK Menu ---
    playback_menu = QMenu("Playback", parent)

    play_action = playback_menu.addAction("Play", parent.play_video)
    play_action.setShortcut("Space")

    pause_action = playback_menu.addAction("Pause", parent.pause_video)
    pause_action.setShortcut("Ctrl+Space")

    stop_action = playback_menu.addAction("Stop", parent.stop_video)
    stop_action.setShortcut("Ctrl+.")

    # Navigation and volume controls
    seek_forward_action = playback_menu.addAction("Seek Forward 5s", parent.seek_forward_5s)
    seek_forward_action.setShortcut("Ctrl+Right")

    seek_back_action = playback_menu.addAction("Seek Backward 5s", parent.seek_back_5s)
    seek_back_action.setShortcut("Ctrl+Left")

    volume_up_action = playback_menu.addAction("Volume Up", parent.volume_up_small)
    volume_up_action.setShortcut("Ctrl+Up")

    volume_down_action = playback_menu.addAction("Volume Down", parent.volume_down_small)
    volume_down_action.setShortcut("Ctrl+Down")

    transpose_menu = playback_menu.addMenu("Transpose")
    transpose_up_action = transpose_menu.addAction("Transpose Up", parent.transpose_up)
    transpose_up_action.setShortcut("Alt+Up")
    transpose_down_action = transpose_menu.addAction("Transpose Down", parent.transpose_down)
    transpose_down_action.setShortcut("Alt+Down")

    # VLC backend toggle (audio only)
    settings = QSettings("bouzouki", "lessonplayer")
    use_vlc = settings.value("use_vlc_backend", USE_VLC_BACKEND)
    if not isinstance(use_vlc, bool):
        use_vlc = str(use_vlc).lower() in ("true", "1", "yes")

    vlc_action = QAction("Pitch-Preserving Audio (VLC)", parent)
    vlc_action.setCheckable(True)
    vlc_action.setChecked(use_vlc)

    def _toggle_vlc(enabled: bool) -> None:
        settings.setValue("use_vlc_backend", enabled)
        QMessageBox.information(
            parent,
            "Audio Backend",
            "VLC audio backend will be used for new playback sessions."
            if enabled
            else "Qt audio backend will be used. Restart playback to apply.",
        )

    vlc_action.triggered.connect(_toggle_vlc)
    playback_menu.addSeparator()
    playback_menu.addAction(vlc_action)

    menu_bar.addMenu(playback_menu)

    # --- METRONOME Menu ---
    metronome_menu = QMenu("Metronome", parent)

    open_metronome_action = metronome_menu.addAction(
        "Open Metronome", lambda: open_metronome_from_menu(parent)
    )
    open_metronome_action.setShortcut("Ctrl+M")

    menu_bar.addMenu(metronome_menu)

    # --- THEME Menu ---
    theme_menu = QMenu("Theme", parent)
    current_theme = settings.value("theme", "dark_teal")
    app = QApplication.instance()

    for theme in get_available_themes():
        action = QAction(theme.capitalize(), parent)
        action.setCheckable(True)
        action.setChecked(theme == current_theme)
        action.triggered.connect(lambda _, t=theme: switch_theme(app, t, settings, theme_menu))
        theme_menu.addAction(action)

    menu_bar.addMenu(theme_menu)

    # --- HELP Menu ---
    help_menu = QMenu("Help", parent)
    help_menu.addAction("About", lambda: show_about_dialog(parent))
    menu_bar.addMenu(help_menu)

    return menu_bar


def switch_theme(app, theme_name, settings, theme_menu):
    settings.setValue("theme", theme_name)
    load_theme(app, theme=theme_name)
    for action in theme_menu.actions():
        action.setChecked(action.text().lower() == theme_name.lower())


def show_about_dialog(parent):
    QMessageBox.information(
        parent,
        "About Lesson Player",
        "🎶 Bouzouki Lesson Player\nVersion 1.0\n\nA custom lesson management and playback tool.\nBuilt with ❤️ and PyQt5.",
    )


def open_settings_dialog(parent):
    dialog = SettingsDialog(parent)
    dialog.exec_()


def _build_metronome_cmd_from_settings() -> list:
    """Build the CLI command used to launch the standalone metronome.

    Uses the same Python interpreter as the main app and forwards the
    app-level default tempo when configured.
    """
    cmd = [sys.executable or "python", "-m", "metronome.metronome"]
    settings = QSettings("bouzouki", "lessonplayer")
    tempo_val = settings.value("metronome_default_tempo", None)
    if tempo_val is not None:
        try:
            tempo_int = int(tempo_val)
        except (TypeError, ValueError):
            tempo_int = None
        if tempo_int is not None:
            cmd.extend(["--tempo", str(tempo_int)])
    return cmd


def open_metronome_from_menu(app):
    """Launch the standalone metronome process from the menu bar."""
    cmd = _build_metronome_cmd_from_settings()
    try:
        subprocess.Popen(cmd)
    except Exception as e:
        QMessageBox.warning(
            app,
            "Metronome Error",
            f"Could not start metronome:\n{e}",
        )


def _build_backup_payload(app) -> dict:
    """Collect paths and settings that make up a basic library backup."""
    db_path = Path(getattr(app, "db_path", "lessons.db"))
    root_dir = db_path.parent
    grooves_path = root_dir / "metronome" / "grooves.json"

    settings = QSettings("bouzouki", "lessonplayer")
    settings_data = {key: settings.value(key) for key in settings.allKeys()}

    return {
        "db_path": str(db_path),
        "grooves_path": str(grooves_path),
        "settings": settings_data,
    }


def backup_library(app):
    payload = _build_backup_payload(app)
    db_path = Path(payload["db_path"])

    default_name = db_path.with_suffix(".backup.zip").name
    target_path, _ = QFileDialog.getSaveFileName(
        app,
        "Backup Library",
        default_name,
        "Backup Files (*.zip);;All Files (*)",
    )
    if not target_path:
        return

    try:
        with zipfile.ZipFile(target_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if db_path.exists():
                zf.write(db_path, arcname="lessons.db")

            grooves_path = Path(payload["grooves_path"])
            if grooves_path.exists():
                zf.write(grooves_path, arcname="grooves.json")

            zf.writestr("settings.json", json.dumps(payload["settings"]))

        QMessageBox.information(
            app,
            "Backup Complete",
            f"Library backup saved to:\n{target_path}",
        )
    except Exception as e:
        QMessageBox.warning(
            app,
            "Backup Failed",
            f"Could not create backup:\n{e}",
        )


def restore_library(app):
    db_path = Path(getattr(app, "db_path", "lessons.db"))
    root_dir = db_path.parent

    source_path, _ = QFileDialog.getOpenFileName(
        app,
        "Restore Library",
        "",
        "Backup Files (*.zip);;All Files (*)",
    )
    if not source_path:
        return

    confirm = QMessageBox.question(
        app,
        "Restore Library",
        "Restoring a backup will overwrite your current lessons and settings.\n"
        "A copy of the existing database will be saved with a .bak suffix.\n\n"
        "Continue?",
        QMessageBox.Yes | QMessageBox.No,
    )
    if confirm != QMessageBox.Yes:
        return

    try:
        with zipfile.ZipFile(source_path, "r") as zf:
            # Restore DB
            if "lessons.db" in zf.namelist():
                if db_path.exists():
                    backup_path = db_path.with_suffix(db_path.suffix + ".bak")
                    shutil.copy2(db_path, backup_path)
                zf.extract("lessons.db", path=db_path.parent)

            # Restore grooves
            grooves_dest = root_dir / "metronome" / "grooves.json"
            if "grooves.json" in zf.namelist():
                grooves_dest.parent.mkdir(parents=True, exist_ok=True)
                zf.extract("grooves.json", path=grooves_dest.parent)

            # Restore settings
            if "settings.json" in zf.namelist():
                settings_data = json.loads(zf.read("settings.json").decode("utf-8"))
                settings = QSettings("bouzouki", "lessonplayer")
                for key, value in settings_data.items():
                    settings.setValue(key, value)

        QMessageBox.information(
            app,
            "Restore Complete",
            "Library restore finished.\n"
            "Please restart the application to ensure all changes take effect.",
        )
    except Exception as e:
        QMessageBox.warning(
            app,
            "Restore Failed",
            f"Could not restore backup:\n{e}",
        )


def export_lessons_from_ui(app):
    if not hasattr(app, "db"):
        QMessageBox.warning(app, "Export Lessons", "No database is loaded.")
        return

    default_name = "lessons-export.json"
    target_path, _ = QFileDialog.getSaveFileName(
        app,
        "Export Lessons",
        default_name,
        "JSON Files (*.json);;All Files (*)",
    )
    if not target_path:
        return

    try:
        export_all_lessons(app.db, target_path)
        QMessageBox.information(
            app,
            "Export Complete",
            f"Lessons and presets exported to:\n{target_path}",
        )
    except Exception as e:
        QMessageBox.warning(
            app,
            "Export Failed",
            f"Could not export lessons:\n{e}",
        )


def import_lessons_from_ui(app):
    if not hasattr(app, "db"):
        QMessageBox.warning(app, "Import Lessons", "No database is loaded.")
        return

    source_path, _ = QFileDialog.getOpenFileName(
        app,
        "Import Lessons",
        "",
        "JSON Files (*.json);;All Files (*)",
    )
    if not source_path:
        return

    confirm = QMessageBox.question(
        app,
        "Import Lessons",
        "Importing lessons will merge new lesson metadata and practice presets\n"
        "into your existing library. Existing lessons are not removed.\n\n"
        "Continue?",
        QMessageBox.Yes | QMessageBox.No,
    )
    if confirm != QMessageBox.Yes:
        return

    try:
        import_lessons(app.db, source_path)
        QMessageBox.information(
            app,
            "Import Complete",
            "Lessons and presets have been imported.\n"
            "Paths must still match media files on disk.",
        )
    except Exception as e:
        QMessageBox.warning(
            app,
            "Import Failed",
            f"Could not import lessons:\n{e}",
        )
