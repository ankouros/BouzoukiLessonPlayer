# BouzoukiLessonsPlayer – Agent Guide

This document describes how automated agents (like Codex) should work
in this repository: what the project does, how to run it, and how to
modify it safely.

## Project Overview

- **App type**: Desktop app for practising bouzouki lessons.  
- **Tech stack**: Python 3, PyQt5, qt-material, mutagen, psutil,
  SQLite, FFmpeg/ffprobe, NumPy + simpleaudio (for the metronome).  
- **Entry point**: `main.py`.  
- **Core modules**: under `core/` and `ui/` (plus `metronome/`).

The app manages lessons stored in a local SQLite database
(`lessons.db`) and associated audio/video resources (`.mp4`, `.mkv`,
`.mp3`) found via guided scans. A separate `metronome/` tool provides
polyrhythmic practice support with user-defined grooves.

## How to Run the App

- **Recommended interpreter**: Use the existing virtual environment
  in `.venv` if present.  
- **Install dependencies** (if needed):
  - `pip install -r requirements.txt`
- **Run the application**:
  - `python main.py`  
  - or use the helper script: `bash start.sh`

Agents should assume a local, interactive GUI environment is available
when reasoning about UI behaviour, but should not rely on being able
to *automatically* drive the GUI in tests.

## Files and Directories

- `main.py` – Application entry point and top-level setup.  
- `core/`:
  - `config.py` – Configuration constants (supported file systems,
    file types, DB path).  
  - `database.py` – Low-level DB helpers used by scanning logic
    (`connect_to_db`, `ensure_lesson_mapping_table`, etc.).  
  - `database_manager.py` – OO wrapper (`DatabaseManager`) used by the
    UI (master/detail panels).  
  - `media_utils.py` – Metadata helpers (folder name parsing, ffprobe
    duration/bitrate extraction, transposition factor).  
  - `theme_manager.py` – Theme loading and listing via `qt-material`.
- `ui/`:
  - `main_window.py` – Main window, master/detail layout, keyboard
    shortcuts, and feedback overlay.  
  - `menu_bar.py` – Menus (`File`, `Playback`, `Theme`, `Help`).  
  - `searchUpdateDatabase.py` – Folder scanning dialog with threaded
    worker and progress feedback.  
  - `widgets/master_detail.py` – Connects `LessonPlayerApp` to the DB
    and wires master/detail widgets.  
  - `widgets/master.py` – Search bar, logo, voice-search placeholder,
    and lesson list.  
  - `widgets/detail.py` – Video list, playback, context menu (open,
    rename, delete, copy path).  
  - `widgets/player_controls.py` – Transport, volume, speed, and
    transpose controls.
- `metronome/` – Standalone metronome UI and tap-to-groove tool.  
- `resources/` – Static assets (icons, QSS theme files).  
- `lessons.db` – Local SQLite database with lesson information.
- `tests/` – Automated tests (pytest-based) that should evolve with
  the code.

Agents should **not** modify files under `Downloads/` or other
non-source data directories unless explicitly instructed.

## Git and Ignore Rules

- `.gitignore` ignores:  
  - Python build artifacts and `__pycache__/`.  
  - Virtual environments (e.g. `.venv/`).  
  - Logs (`*.log`) and databases (`*.db`, `*.sqlite3`).  
  - IDE/editor metadata and OS-specific clutter.

Agents should **not** commit `lessons.db`, downloaded media, or other
large binary assets. Keep changes focused on source files.

## Test-Driven Design Rule

This project treats automated tests and their artifacts as first-class
inputs to design and implementation decisions.

- For any non-trivial change, agents should **add or update pytest
  tests** under `tests/` to cover the new behaviour.  
- Decisions about refactors, fixes, or follow-up work should be based
  on **observed test results** (e.g. new failures, passing smoke
  checks), not only on reasoning.  
- Before considering a feature "done", agents should run at least:
  - `make code-check`  
  - `make test`  
  - optionally `make lint` if available
- When tests fail, agents should treat failures as primary evidence and
  adjust design/implementation until tests express the desired
  behaviour.

## Testing and Validation

- Tests live under `tests/` and are run with `pytest` via
  `make test`.  
- A minimal DB smoke test exists (`tests/test_database_schema.py`) and
  should be extended as core behaviour evolves.

Agents should validate changes by:

- Performing targeted manual reasoning on code paths touched.  
- Running `make check` where feasible to produce test artifacts
  (`docs-check`, `code-check`, `lint`, `test`).  
- Optionally running the app (`python main.py`) to verify that:  
  - It starts without exceptions.  
  - Library scanning (`Search Media`) completes without errors.  
  - Lesson selection and playback work as expected.  
  - Metronome tools behave sensibly.

## Safe Change Guidelines for Agents

- **Scope changes narrowly** to the user request.  
- **Preserve behaviour** unless the user explicitly asks for a change;
  avoid refactors that are not needed.  
- **Avoid breaking the GUI**:
  - When editing signal/slot connections or widget names, make sure
    all references are updated.  
  - Long-running work (scans, metadata extraction) must stay off the
    main thread (see `FolderScannerWorker` for a pattern).  
- **Database safety**:
  - Treat `lessons.db` as important user data.  
  - Avoid destructive operations on `lessons` and `folders` tables
    unless explicitly requested.  
  - Prefer additive schema changes over destructive ones and document
    them in a spec.
- **File operations**:
  - Be careful when renaming or deleting files; update DB records in
    addition to touching the filesystem.  
  - Do not automatically scan or modify all mounted drives; respect
    user-chosen folders.

## Shell Command Guidance for Agents

When using shell commands in this repo, agents should:

- Prefer **read-only** commands when exploring (`ls`, `find`, `rg`,
  `sed -n`, `cat`).  
- Use `python main.py` to run the main app.  
- Run `python metronome/metronome.py` or `python metronome/tap.py`
  only when working specifically on metronome features.  
- Avoid installing new global tools unless requested; prefer using the
  existing `.venv` and `requirements.txt`.  
- Avoid manipulating the `Downloads/` directory or large media
  archives.

## When in Doubt

If something is ambiguous, agents should:

- Default to the least destructive option.  
- Clearly explain assumptions in their responses.  
- Propose options to the user instead of making irreversible
  structural changes.  
- Prefer decisions that are supported by automated test results over
  untested assumptions.

