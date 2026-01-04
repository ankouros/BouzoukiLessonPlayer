# BouzoukiLessonsPlayer – Roadmap

This roadmap is intentionally lightweight and focused on practical,
short iterations. It should be updated whenever meaningful work lands.

Legend:
- `[x]` Completed
- `[ ]` Planned / in progress

## 0.1 – Stabilize Current App (Completed)

- [x] Review existing features and remove dead code
      (removed the unused/broken global scanner in favour of the
      `ui/searchUpdateDatabase.py` flow).
- [x] Fix obvious crashes and unhandled exceptions in `main.py`,
      `core/`, and `ui/` (including safer DB handling and startup
      error paths).
- [x] Ensure metronome works reliably without runtime auto-installs in
      `metronome/metronome.py` (explicit imports + CLI error handling).
- [x] Add logging around database operations and startup
      (`core/database_manager.py`, `main.py`), including log rotation
      for `bouzouki_player.log`.

## 0.2 – UX and Navigation (Current Focus)

- [x] Use the main window status bar for playback feedback
      (`ui/main_window.py`).
- [x] Propagate scan status from `FolderScannerWorker` to the main
      status bar (`ui/searchUpdateDatabase.py`).
- [x] Add clear error messages when media files are missing or paths
      cannot be determined (`ui/widgets/detail.py`).
- [x] Validate theme selection and About dialog content via tests
      (`ui/menu_bar.py`, `tests/test_theme_manager.py`,
      `tests/test_menu_bar_theme_and_about.py`).
- [x] Further polish main window layout and responsiveness
      (`ui/main_window.py`).
- [x] Refine menus and keyboard shortcuts (`ui/menu_bar.py`,
      `ui/widgets/master.py`, `ui/widgets/detail.py`) for smoother
      navigation and easier discovery of controls.
- [x] Make lesson search and filtering more intuitive by aligning UI
      behaviour (`ui/widgets/master.py`) with the DB search semantics
      in `DatabaseManager.fetch_lessons()` (e.g. better highlighting and
      filtering UX).

## 0.3 – Library and Lesson Management

- [x] Consolidate filesystem scanning and library refresh into a
      single implementation based on `ui/searchUpdateDatabase.py`
      (removed `core/scanner.py`).
- [x] Ensure rename/delete operations keep the lessons DB in sync with
      filesystem changes (`ui/widgets/detail.py`,
      `core/database_manager.py`).
- [x] Handle empty-folder scans and DB errors gracefully in
      `FolderScannerWorker` (status messages instead of crashes, tests
      for DB errors and malformed folders).
- [x] Add tools to re-link missing audio files when
      `app.db.get_file_path()` points to non-existent paths, with a
      guided UI to locate replacements.
- [x] Provide basic metadata editing (title, tempo, tags) using
      `core/media_utils.py` where possible, with an emphasis on making
      it easy to organise practice material.
- [x] Offer simple backup/restore options for `lessons.db` and essential
      configuration, optimised for safety and ease of use.
- [x] Expose the `folders` table more clearly in the UI so users can
      manage scan locations and exclude unwanted folders.

## 0.4 – Practice Features and Controls

- [x] Tighten integration between lessons and metronome:
      - Use lesson tempo or tags to pre-select metronome presets.  
      - Allow opening `metronome/metronome.py` with a lesson-specific
        groove directly from the UI.
- [x] Add loop / A–B repeat controls for audio playback (and optionally
      video), with simple UI to set start/end points and visual
      indicators.
- [x] Provide configurable count-in / pickup bar and visual cues before
      playback starts.
- [x] Allow saving practice presets per song (tempo, transpose, loop
      section, preferred metronome groove) in the database.
- [x] Refine keyboard and mouse controls for practice (e.g. quick
      shortcuts to jump back a few seconds, toggle loop, adjust tempo
      in small steps) to maximise ease of use.

## 0.5 – Playback Quality and Quality of Life

- [x] Add configurable logging with rotation to prevent unbounded log
      growth (`main.configure_logging`).
- [x] Introduce a VLC-based audio backend wrapper (`core/vlc_player`)
      with tests, using VLC's `scaletempo` filter for pitch-preserving
      time-stretch where available.
- [x] Wire the detail view to use VLC for audio by default when
      available, while keeping Qt for video
      (`config.USE_VLC_BACKEND`, `ui/widgets/detail.py`,
      `ui/widgets/player_controls.py`, `ui/main_window.py`).
- [x] Add a user-accessible runtime toggle to enable/disable the VLC
      backend via the **Playback → Pitch-Preserving Audio (VLC)** menu,
      persisted in `QSettings`.
- [x] Expose the active backend in the UI via the status bar
      (e.g. `[VLC] Play` vs `[Qt] Play`).
- [x] Fine-tune default audio levels and error messages so speed and
      transpose adjustments preserve clarity and loudness as much as
      possible.
- [x] Settings page for paths, audio devices, default scan folders,
      and metronome options.
- [x] Optional telemetry toggle (local-only usage stats if desired).

## 0.6 – Tonality, Speed, and Audio Clarity

- [x] Design and implement true pitch-only transpose on top of
      time-stretch (e.g. using VLC audio filters), so users can change
      tonality by half-steps without altering tempo.
- [x] Refine speed control so that slowing down or speeding up preserves
      both pitch and as much clarity as possible, including testing
      across a variety of source material.
- [x] Consider optional EQ or simple audio enhancements to improve
      clarity at low speeds (where artifacts are more noticeable).

## 0.7 – Testing and Maintenance

- [x] Introduce a pytest-based automated test suite for critical
      `core/` and `ui/` logic (DB, scanning, metadata, UI behaviour,
      metronome, tap grooves, VLC wrapper).
- [x] Ensure tests cover corrupted DB files and startup error handling
      (`tests/test_corrupted_db.py`, `tests/test_main_db_error_handling.py`).
- [x] Add coverage for logging behaviour and rotation
      (`tests/test_logging_error_paths.py`,
      `tests/test_logging_rotation.py`).
- [x] Add coverage for scanner DB error paths and malformed folders
      (`tests/test_folder_scanner_db_errors.py`).
- [x] Add a simple smoke-check script that starts and closes the app to
      catch import/runtime errors outside pytest.
- [x] Document release steps and versioning.
- [x] Regular dependency review using `requirements.txt` and removal of
      any new runtime auto-installs.

## 0.8 – Future VLC Integration and Advanced Playback

- [ ] Decide on cross-platform video output via VLC and how (or if) to
      integrate it with Qt's `QVideoWidget`, aiming for smooth user
      experience without regressions.
- [ ] Explore VLC audio filters for true pitch-only transpose (on top
      of time-stretch), wired to the existing transpose controls, and
      evaluate audio quality.
- [ ] Add tests or automated checks to validate basic VLC backend
      availability and behaviour on target platforms.

## 0.9 – Library UX and Metronome Integration

- [ ] Make file identity robust across the stack by using DB IDs or
      `file_path` as the primary key in UI actions (open, rename,
      delete, copy path) and practice presets.
- [ ] Expose a clear "Save / Reset Practice Preset" flow in the detail
      view so users can quickly store per-song tempo, transpose, loop,
      and metronome settings.
- [ ] Tighten metronome integration by allowing the main app to launch
      `metronome/metronome.py` pre-configured for the currently
      selected lesson, and by surfacing groove changes more clearly in
      the UI.

## Long-Term Ideas

- [x] Export/import lesson sets to share with other users.
- [x] Integration with external audio players or DAWs.
- [x] Advanced rhythm training modes (complex polyrhythms,
      subdivisions, exercise plans).
- [x] Multi-language UI support.
- [x] Additional UI polish (e.g. theme presets for different lighting
      conditions, compact vs. expanded layouts) to enhance overall ease
      of use and visual appeal.
