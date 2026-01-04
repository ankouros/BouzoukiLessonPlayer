# BouzoukiLessonsPlayer – Open Issues

This file tracks known problems and improvements. Keep entries short
and link them back to relevant modules where possible.

## High Priority

1. **Robust file identity and multi-file lessons**  
   - `DatabaseManager.get_file_path()` and parts of the detail view
     (`ui/widgets/detail.py`) still rely on `file_name` as a lookup
     key.  
   - When multiple lessons share the same filename, context‑menu
     actions ("Open", "Delete", "Copy Path") can still be ambiguous.  
   - Introduce a consistent internal ID for each file (e.g. DB `id` or
     full `file_path` stored in `Qt.UserRole`) and use it across UI
     actions and practice‑preset lookups.

2. **Practice preset UX and persistence**  
   - `DatabaseManager` provides `practice_presets` helpers, and tests
     cover basic flows, but the UI only surfaces a subset of this
     power.  
   - Add a clear "Save Practice Preset" / "Reset to Default" affordance
     in the detail view and ensure presets follow files when they are
     renamed or moved.

3. **Metronome / groove UX in the main app**  
   - Metronome tools (`metronome/metronome.py`, `metronome/tap.py`) are
     well‑tested but remain visually separate from the lesson player.  
   - Tighten the integration so users can:  
     - Launch the metronome pre‑configured for the current lesson.  
     - See clearly when a custom groove has been saved/updated.  
   - Consider a small inline metronome status indicator in the main
     window.

## Medium Priority

4. **Theme selection and persistence polish**  
   - The Theme menu in `ui/menu_bar.py` relies on theme names from
     `qt_material.list_themes()` and `core/theme_manager.load_theme()`,
     but the persisted setting uses a raw theme string (e.g.
     `dark_teal`).  
   - Double-check that displayed names, stored values, and applied
     `.xml` files always match and handle missing themes gracefully.

5. **Error handling for media metadata**  
   - `core/media_utils.extract_audio_metadata()` depends on
     `ffprobe` being available on the system and logs a warning on
     failure.  
     - Document this external dependency and ensure the UI behaves
     sensibly when duration/bitrate are `None`.

## Low Priority / Nice-to-Have

6. **Configuration management**  
    - Centralize configurable paths (media library, DB location) in
      `core/config.py` and use them consistently across modules
      (`main.py`, `core/database.py`, `core/database_manager.py`,
      `ui/searchUpdateDatabase.py`).

7. **Logging improvements**  
    - Replace ad-hoc prints (e.g. in `metronome/tap.py`) with a
      consistent logging setup where appropriate.  
    - Consider rotating or trimming `bouzouki_player.log` so it does
      not grow indefinitely.

8. **Documentation gaps**  
    - Keep `README.md`, `AGENTS.md`, `ROADMAP.md`, and
      `OPEN-ISSUES.mg` in sync as the app evolves.  
    - Add user-facing documentation on how scanning works, where data
      is stored, and how to back it up (see `README.md` and
      `ROADMAP.md`).
