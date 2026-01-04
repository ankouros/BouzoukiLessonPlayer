# Library Identity and Practice UX

- **Status**: Draft  
- **Owner**: Unassigned  
- **Last Updated**: 2026-01-03

## 1. Problem Statement

The current lesson library and practice workflow are functional but
have several consistency gaps:

- Media files are sometimes identified by `file_name` only (e.g. in
  `DatabaseManager.get_file_path()` and older UI flows), which is
  ambiguous when multiple lessons share the same filename.  
- The detail view (`ui/widgets/detail.py`) now correctly stores the
  `file_path` in `Qt.UserRole` for most operations, but this contract
  is implicit rather than explicit and not uniformly applied across
  the stack.  
- Practice presets are persisted in the `practice_presets` table and
  applied when selecting a video, yet the UI does not clearly expose
  when a preset is active or how to reset it, and behaviour under
  renames/moves is only partially defined.  
- The metronome tools (`metronome/metronome.py`, `metronome/tap.py`)
  are well-tested and loosely integrated via a context menu action,
  but they feel like a separate app rather than part of a cohesive
  practice flow.

These gaps can lead to confusing behaviour (operations targeting the
wrong file, "mystery" presets, or unclear metronome state) and make
future features harder to build.

## 2. Goals

- Use a stable, unambiguous file identity (DB `id` or `file_path`) for
  all library-related actions and practice presets.  
- Make practice presets an explicit, understandable part of the UX
  (clear save/reset flows and visible state).  
- Tighten integration between the lesson player and the metronome so
  that metronome settings feel like a first-class part of practice.  
- Keep behaviour backwards compatible for existing `lessons.db`
  installations.

## 3. Non-Goals

- No major redesign of the main window layout or navigation.  
- No changes to the underlying metronome audio engine or groove file
  format beyond what is needed for better integration.  
- No remote sync or multi-user features for the library.

## 4. User Experience

- **Stable file identity**  
  - The detail list continues to show human-friendly filenames.  
  - Context menu actions (Play, Open in File Manager, Rename, Delete,
    Copy Path, External Player, DAW, Re-link) all operate on a stable
    identity attached to the list item (DB `id` or `file_path`).  
  - Renaming or re-linking a file updates both the filesystem and the
    underlying DB entry, and the UI refreshes to reflect the change.

- **Practice preset UX**  
  - When a preset is active for the selected media, a small indicator
    (e.g. "Preset: On") appears near the transport controls or in the
    status bar.  
  - A "Save Practice Preset" action stores the current transpose,
    loop points, and relevant tempo/groove information.  
  - A "Reset Practice Preset" action clears the preset for that file
    and updates the indicator.  
  - Renaming or re-linking a file preserves the associated preset.

- **Metronome integration**  
  - Selecting "Open Metronome" from the context menu launches the
    metronome pre-configured with the current lesson's tempo and
    groove when available.  
  - Changes made in the metronome (e.g. selecting a different groove)
    can be stored in a practice preset or reflected back into lesson
    metadata (tags) when the user chooses to save.

## 5. Architecture and Data

- **File identity**  
  - Continue to treat `lessons.file_path` as unique in the DB and the
    primary key for practice presets (`practice_presets.file_path`).  
  - Ensure all UI code that operates on media items reads/writes
    `file_path` from `Qt.UserRole` instead of reconstructing or
    looking up by `file_name`.  
  - Keep `DatabaseManager.get_file_path(file_name)` for backward
    compatibility in non-UI code paths, but avoid introducing new
    usage sites and prefer identity-based helpers.

- **Practice presets**  
  - Reuse the existing `practice_presets` table.  
  - Ensure `rename_file`, `delete_file`, and `relink_file` in
    `ui/widgets/detail.py` keep `practice_presets` in sync where
    needed (e.g. delete presets when files are deleted if that is the
    desired behaviour).  
  - Preserve the current behaviour where presets are keyed by
    `file_path` while allowing internal refactors to use DB `id` later
    if necessary.

- **Metronome**  
  - Continue to invoke the metronome via `python -m metronome.metronome`
    with `--tempo` and `--groove` arguments.  
  - Use practice presets as the primary source of tempo/groove, falling
    back to lesson metadata when no preset exists.

## 6. API / Interfaces

- `ui/widgets/detail.py`  
  - Contract: every `QListWidgetItem` in `video_list` must have
    `Qt.UserRole` set to the canonical `file_path` for that row.  
  - All helper functions (`play_selected_video`, `open_file_in_explorer`,
    `open_in_external_player`, `send_to_daw`, `rename_file`,
    `delete_file`, `relink_file`, `save_practice_preset`,
    `copy_path_to_clipboard`, `open_metronome_for_item`,
    `apply_practice_preset`) read `file_path` from `Qt.UserRole`.

- `core/database_manager.DatabaseManager`  
  - Existing methods (`get_practice_preset`, `save_practice_preset`,
    `get_lesson_metadata`, `update_lesson_metadata`,
    `update_file_entry`, `delete_file_entry`) remain the primary DB
    surface for library and practice features.  
  - New callers should prefer these identity-based helpers over raw
    SQL.

## 7. Risks and Mitigations

- **Risk: Data inconsistency during rename/relink**  
  - Mitigation: keep DB updates and UI refreshes together, reuse
    `update_file_entry` everywhere, and add tests that simulate
    rename/relink flows.

- **Risk: Confusing preset behaviour**  
  - Mitigation: always show a visible indicator when a preset is
    active and provide an explicit reset action.

- **Risk: Metronome integration surprises**  
  - Mitigation: treat metronome launches and argument passing as
    best-effort; if the metronome cannot be started, surface a clear
    dialog and log the failure.

## 8. Rollout and Migration

- No schema changes are required; existing `lessons.db` files remain
  valid.  
- Behavioural changes are implemented incrementally behind the current
  UI, preserving existing workflows where possible.  
- If unexpected regressions occur, it is straightforward to revert to
  the previous `ui/widgets/detail.py` behaviour (with the caveat of
  reintroducing ambiguity around file identity).

## 9. Implementation Plan

- [x] Document identity and practice UX goals in this spec.  
- [x] Ensure the detail view consistently stores `file_path` in
      `Qt.UserRole` and uses it for all context-menu actions.  
- [x] Add a visible preset indicator and a "Reset Practice Preset"
      action in the detail view.  
- [x] Audit metronome integration and align argument passing with
      practice presets/lesson metadata (best-effort status text).  
- [ ] Extend tests to cover rename/relink/delete flows with practice
      presets and metronome launches.

## 10. Follow-Up and Open Questions

- Should practice presets be deleted automatically when a file is
  removed from disk, or should they be kept to assist in future
  re-link operations?  
- Is `file_path` sufficient as the long-term identity, or do we want a
  separate stable key (e.g. a "track UUID") for future multi-device
  sync scenarios?  
- Should metronome changes be automatically written back into lesson
  metadata/tags, or only when the user explicitly saves a preset?
