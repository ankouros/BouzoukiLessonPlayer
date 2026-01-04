# Bouzouki Lesson Player

Bouzouki Lesson Player is a desktop application to help you organise
and practise bouzouki lessons. It combines a lesson library, audio
playback, and a metronome into a single tool built with Python and
PyQt5.

## Features

Current behaviour based on the codebase:

- **Lesson library backed by SQLite**  
  - Lessons are stored in `lessons.db` in a `lessons` table with
    `lesson_number`, `lesson_name`, `file_name`, `file_path`,
    `duration`, and `bitrate` columns (`core/database.py`,
    `core/database_manager.py`).  
  - A `folders` table keeps track of previously scanned directories.
- **Guided media scanning**  
  - `Search Media` opens a modal `FolderScannerWindow`
    (`ui/searchUpdateDatabase.py`).  
  - The user chooses one or more root folders; the app walks them and
    imports video/audio files (`.mp4`, `.mkv`, `.mp3`).  
  - Folder names like `001_Lesson_Name` are parsed into
    `lesson_number` and `lesson_name` via
    `core.media_utils.extract_metadata()`; otherwise lesson numbers are
    assigned automatically using `get_or_assign_lesson_number()`.
- **Master–detail library UI**  
  - The main window (`ui/main_window.py`) uses a horizontal splitter
    (`ui/widgets/master_detail.py`).  
  - The left **master panel** (`ui/widgets/master.py`) shows a list of
    lessons with a search bar and clickable logo.  
  - The right **detail panel** (`ui/widgets/detail.py`) shows a video
    player, transport controls, and the list of videos for the
    selected lesson.
- **Playback controls and feedback**  
  - Video is handled via `QMediaPlayer` + `QVideoWidget`.  
  - Controls include Play/Pause/Stop, volume, and speed adjustment
    (`ui/widgets/player_controls.py`).  
  - A keyboard overlay in `LessonPlayerApp` lets you control playback
    with Space/Arrow keys and displays on-screen feedback.
- **Pitch / speed control (transpose)**  
  - Playback rate is computed as a combination of speed
    (`current_speed`) and semitone transposition steps using
    `HALF_TONE_UP_FACTOR` from `core/media_utils.py`.  
  - Controls for transpose up/down are exposed both in the UI and the
    `Playback -> Transpose` menu.
- **Pitch-preserving audio backend (VLC by default)**  
  - By design, the app prefers VLC for audio when it is available so
    that changing speed does not change pitch.  
  - Audio playback can be handled by VLC via `core.vlc_player.VlcMediaPlayer`,
    using VLC's `scaletempo` filter for pitch-preserving time-stretch.  
  - Video remains in Qt; audio is muted in Qt and played via VLC.  
  - The backend can be toggled at runtime from the menu:
    **Playback → Pitch-Preserving Audio (VLC)**.
- **Theming**  
  - Themes are handled via `qt-material` and `QSettings` in
    `core/theme_manager.py`.  
  - A `Theme` menu in `ui/menu_bar.py` lists available themes and saves
    the selection.
- **Metronome and groove tools**  
  - `metronome/metronome.py` implements a polyrhythmic metronome with
    presets, custom grooves persisted in `metronome/grooves.json`, and
    animated LED-style visual feedback.  
  - `metronome/tap.py` allows tapping rhythms to create new grooves,
    which are merged into existing groove files.

See `ROADMAP.md` for planned work and `OPEN-ISSUES.mg` for known
issues and technical follow‑ups.

### How scanning and storage work

- The media library is stored in a local SQLite database at
  `lessons.db` (see `core/database.py`, `core/database_manager.py`).  
- Scans are initiated from the **Search Media** action, which opens
  the `FolderScannerWindow` (`ui/searchUpdateDatabase.py`):  
  - You choose one or more root folders to scan; these are stored in
    the `folders` table for easy reuse.  
  - The scanner walks the selected folder, ignoring any directory
    named `Downloads`.  
  - Supported media files (`.mp4`, `.mkv`, `.mp3`) are imported into
    the `lessons` table with parsed lesson number/name, file name and
    full path, and optional duration/bitrate from `ffprobe`.  
  - Progress and status are shown in the scan dialog and propagated to
    the main window status bar.
- The database also stores per‑file practice presets (tempo, transpose,
  loop points, metronome groove) in `practice_presets`, and settings
  such as compact layout and metronome options are persisted via
  `QSettings`.

### Backups and safety

- The single most important file is `lessons.db`, which contains the
  lesson library and practice presets.  
- You can create a backup simply by copying `lessons.db` while the app
  is closed; see tests under `tests/test_backup_restore_library.py`
  for the expected behaviour.  
- Application logs live in `bouzouki_player.log` with rotation, which
  can help diagnose scanning or playback issues.

### Local-only metadata and cleanup guidance

- Several folders and documents are deliberately kept out of the shared
  repository to avoid leaking large media bundles or personal notes:
  `Downloads/`, `Zips/`, `specs/`, `AGENTS.md`, `CONTRACTS.md`,
  `REVIEW.md`, `ROADMAP.md`, and `OPEN-ISSUES.mg` are ignored via
  `.gitignore`.  Your local `lessons.db` and any other `*.db` files stay
  on disk but are never tracked upstream.
- If a file accidentally landed in the index, use
  `git rm --cached <path>` and commit the removal; this preserves your
  working copy while expunging it from the remote history.  After the
  commit, the `.gitignore` entry keeps the file untracked going forward.

## Getting Started

### Requirements

Target platforms:

- Ubuntu/Debian-based Linux distributions.  
- Windows (PowerShell + Python).

Runtime requirements:

- Python 3.10+ (recommended to match the existing `.venv`).  
- A working Qt environment (installed via `PyQt5`).  
- External tools:
  - `ffprobe` from FFmpeg for media metadata extraction
    (`core/media_utils.extract_audio_metadata()`).  
  - VLC + `python-vlc` for pitch-preserving audio playback.

Python packages are listed in `requirements.txt`:

- `PyQt5` – GUI framework.  
- `psutil` – system information utilities for scanning drives.  
- `mutagen` – audio metadata handling.  
- `qt-material` – additional Qt styling.  
- `pytest` – testing framework.  
- `numpy`, `simpleaudio` – audio handling for the metronome.  
- `python-vlc` – VLC bindings used by the audio backend.

### Installation (Ubuntu/Debian)

From the project root:

```bash
cd /path/to/BouzoukiLessonsPlayer

# Make the installer executable
chmod +x install.sh

# Run the installer (creates .venv, installs deps, checks ffprobe/VLC)
./install.sh
```

If you prefer manual setup:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg vlc

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Installation (Windows)

From PowerShell in the project root:

```powershell
cd C:\path\to\BouzoukiLessonsPlayer

# Allow script execution for this session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Run the installer (creates .venv, installs deps)
.\install.ps1
```

Manual setup steps (if you prefer):

1. Install VLC from the official installer (https://www.videolan.org).  
2. Install Python 3.10+ and ensure `python` is on your PATH.  
3. In PowerShell:

   ```powershell
   cd C:\path\to\BouzoukiLessonsPlayer
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

### Running the Application

From the project root (Ubuntu/Debian):

```bash
cd /path/to/BouzoukiLessonsPlayer
source .venv/bin/activate
python main.py
```

From PowerShell (Windows):

```powershell
cd C:\path\to\BouzoukiLessonsPlayer
.\.venv\Scripts\Activate.ps1
python main.py
```

On startup, the app will:

- Configure logging with rotation to `bouzouki_player.log`.  
- Create a `QApplication` and load the saved theme via
  `core.theme_manager.load_theme()`.  
- Instantiate the main window `ui.main_window.LessonPlayerApp` with
  `db_path="./lessons.db"`.

### Pitch-preserving audio (VLC)

To take advantage of the VLC backend for pitch-preserving speed changes and
embedded video:

1. Install VLC and `python-vlc` (already listed in `requirements.txt`).  
2. Launch the app.  
3. Open the **Playback** menu and ensure
   **Pitch-Preserving Audio (VLC)** is checked.  
4. Play a lesson video:
   - When VLC is available and enabled, audio **and** video are handled by
     VLC, embedded inside the main player area.  
   - Qt’s `QMediaPlayer` runs muted in the background to keep progress and
     controls in sync, but it no longer shows a separate video.

The status bar indicates which backend is active, for example:

- `[VLC] Play` – VLC audio/video backend active.  
- `[Qt] Play` – Qt-only backend (VLC unavailable or disabled).

You can toggle the backend at runtime; the choice is remembered between
sessions via `QSettings` (`use_vlc_backend` under the `bouzouki/lessonplayer`
namespace).

### Troubleshooting VLC setup

If you expect VLC to be active but see `[Qt]` in the status bar:

- On Ubuntu/Debian:

  ```bash
  which vlc
  which ffprobe
  source .venv/bin/activate
  python -c "import vlc; print('VLC ok:', vlc.Instance() is not None)"
  ```

  - If `which vlc` prints nothing, install VLC with
    `sudo apt-get install vlc`.  
  - If the Python check fails, ensure `python-vlc` is installed in the
    `.venv` and matches your system VLC.

- On Windows (PowerShell):

  ```powershell
  where vlc
  .\.venv\Scripts\Activate.ps1
  python -c "import vlc; import vlc as v; print('VLC ok')"
  ```

  - If `where vlc` prints nothing, install VLC from
    https://www.videolan.org and ensure it is on your PATH.  
  - If Python cannot import `vlc`, run `python -m pip install python-vlc`
    inside your `.venv`.

## Project Structure

- `main.py` – Entry point, Qt app setup, logging (with rotation), and
  main window creation.  
- `core/` – Non-UI logic:
  - `config.py` – Configuration helpers and constants (supported file
    types, FS types, DB path, backend flag).  
  - `database.py`, `database_manager.py` – Database access and models.  
  - `media_utils.py` – Audio and media utilities, including
    `ffprobe`-based metadata extraction.  
  - `theme_manager.py` – Theme loading and listing.  
  - `vlc_player.py` – VLC-based audio backend wrapper.
- `ui/` – User interface code:
  - `main_window.py` – Main window and high-level layout.  
  - `menu_bar.py` – Menu bar (File/Playback/Theme/Help) and VLC toggle.  
  - `searchUpdateDatabase.py` – Folder selection and scanning dialog.  
  - `widgets/master_detail.py` – Master/detail splitter wiring and DB
    manager creation.  
  - `widgets/master.py` – Lesson search and master list.  
  - `widgets/detail.py` – Video list, playback, and context menu
    actions; optional VLC audio integration.  
  - `widgets/player_controls.py` – Transport, volume, speed, and
    transpose controls, aware of VLC when present.
- `metronome/` – Metronome logic, groove presets and tapping tools.  
- `resources/` – Static assets (QSS themes, icons).  
- `lessons.db` – Local SQLite database with lesson information.  
- `grooves.json` / `metronome/grooves.json` – Rhythm definitions used
  by the metronome.

## Release and Dependency Management

### Release steps and versioning

This project uses simple, incremental versioning aligned with `ROADMAP.md`
milestones (e.g. `0.4`, `0.5`, `0.6`). A lightweight release process:

1. Ensure dependencies are installed in `.venv` and up to date (see
   *Dependency review* below).  
2. Run the full check pipeline locally:

   ```bash
   make check
   make smoke-check
   ```

3. Verify the GUI manually:
   - App starts without errors.  
   - Library scanning, playback, metronome, and presets work as expected.  
4. Update documentation if needed:
   - `ROADMAP.md` and `OPEN-ISSUES.mg` for what shipped and what remains.  
   - This `README.md` for any user-visible changes.  
5. Tag the release in your VCS with the roadmap version (e.g. `v0.5.0`)
   and include a short changelog referencing the relevant roadmap items.

### Dependency review using `requirements.txt`

Dependencies are pinned in `requirements.txt` and should be reviewed
regularly, especially before releases:

1. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

2. Check for outdated packages:

   ```bash
   make deps-review
   ```

3. For each outdated dependency you choose to upgrade:
   - Update `requirements.txt`.  
   - Reinstall into `.venv` (e.g. `pip install -r requirements.txt`).  
   - Re-run `make check` and basic GUI smoke checks.

Runtime auto-installs (e.g. `pip install` from inside application code)
have been removed; any new dependencies should be added to
`requirements.txt` and installed via the normal environment setup.

## Development and Contribution

This repository is configured for both human and automated
contributors. Key documents:

- `AGENTS.md` – Guidelines for agents working on this repo.  
- `ROADMAP.md` – High-level roadmap and milestones.  
- `OPEN-ISSUES.mg` – Known issues and improvement ideas.  
- `REVIEW.md` – Code review checklist and expectations.  
- `specs/` – Design contracts and detailed feature specs (including
  the VLC backend spec).  
- `CONTRACTS.md` – Overview of design and process contracts.

### Basic Workflow

1. Open or create a spec in `specs/` for non-trivial changes.  
2. Make code changes in `core/`, `ui/`, `metronome/` following
   existing patterns.  
3. Run `make check` (docs, code, lint, tests) to validate changes.  
4. Update `ROADMAP.md` and `OPEN-ISSUES.mg` if appropriate.  
5. Use `REVIEW.md` as a checklist before merging or finalizing changes.

## Data and Safety Notes

- `lessons.db` is important user data: avoid destructive changes or
  schema modifications without a clear migration plan.  
- Media files in `Downloads/` or other local folders are user-owned and
  should not be deleted or moved automatically without confirmation.  
- Logs (`bouzouki_player.log`) are helpful for debugging; rotation is
  configured, but still be mindful of log volume.

## License

No explicit license file is included in this repository yet. If you
plan to share or open-source this project, consider adding a
`LICENSE` file with the appropriate terms.
