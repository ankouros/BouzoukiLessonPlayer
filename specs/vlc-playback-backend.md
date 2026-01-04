# VLC-Based Playback Backend

- **Status**: Draft  
- **Owner**: Unassigned  
- **Last Updated**: 2026-01-03

## 1. Problem Statement

Initial playback used `QMediaPlayer`, which ties playback speed directly to
pitch. Changing `playbackRate` slows down or speeds up both audio and pitch,
which conflicts with the requirement:

> When slowing down or increasing playback speed, do not alter pitch.

Qt 5's `QMediaPlayer` does not offer pitch-preserving time-stretch
functionality. We need an alternative backend that can change speed while
preserving pitch, and optionally apply true transpose on top.

## 2. Goals

- Provide a playback backend that supports:
  - Variable speed with **pitch preserved** (time-stretch).  
  - Independent transpose (pitch shifting) if desired.  
  - A minimal API compatible with the subset of `QMediaPlayer` that the
    UI currently uses.
- Keep the existing UI (`ui/widgets/detail.py`, `ui/widgets/player_controls.py`)
  largely unchanged by introducing a wrapper/adapter and attaching VLC
  video to the existing video area when enabled.
- Make the backend opt-in (feature flag + runtime toggle), so the
  QMediaPlayer path remains available when VLC is disabled or missing.

## 3. Non-Goals

- Full remote-control of all VLC features (subtitles, advanced filters).  
- Perfect audio/video sync across all platforms from day one.  
- Automatic installation of VLC or `python-vlc`.

## 4. User Experience

Behavior for users once the VLC backend is enabled (future wiring):

- Speed slider changes playback speed *without* shifting pitch.  
- Transpose controls adjust pitch by semitones while maintaining tempo.  
- If VLC or `python-vlc` is missing, the app should:
  - Fall back to the existing QMediaPlayer backend, or  
  - Show a clear error explaining that VLC is required for
    pitch-preserving playback.

This spec currently introduces the backend and test scaffolding, but does not
fully switch the UI to use VLC by default.

## 5. Architecture and Data

### Backend module (audio + embedded video)

- New module: `core/vlc_player.py`
- Responsibilities:
  - Wrap `python-vlc` (`vlc.Instance`, `vlc.MediaPlayer`) in a Python class
    with a minimal interface and optional video output attachment.
  - Configure VLC instance with audio filters suitable for
    pitch-preserving time-stretch (e.g. `--audio-filter=scaletempo`) when
    available.
  - Provide an adapter with a small subset of QMediaPlayer-like methods:
    - `set_media(path: str)`  
    - `play()`, `pause()`, `stop()`  
    - `set_rate(rate: float)`  
    - `set_volume(volume: int)`  
    - `set_video_output(window_id: int)` to attach video to a Qt widget

### Configuration

- Add a feature flag to `core/config.py`, e.g.:

  ```python
  USE_VLC_BACKEND = False
  ```

- When `True`, the UI can attempt to use the VLC backend; when `False`, the
  existing QMediaPlayer path remains.

## 6. API / Interfaces

`core/vlc_player.py`:

- `class VlcUnavailableError(Exception)`: Raised when `python-vlc` is not
  available.

- `class VlcMediaPlayer`:

  - `__init__(self)`:  
    - Requires `python-vlc` to be importable; otherwise raises
      `VlcUnavailableError`.
    - Creates a `vlc.Instance` with suitable audio-filter arguments.  
    - Creates an underlying `vlc.MediaPlayer`.

  - `set_media(self, path: str) -> None`:  
    - Sets the current media from a file path.

  - `play(self)`, `pause(self)`, `stop(self)`:  
    - Control playback.

  - `set_rate(self, rate: float) -> None`:  
    - Adjust playback rate (speed). The expectation is that VLC's
      `scaletempo` filter preserves pitch.

  - `set_volume(self, volume: int) -> None`:  
    - Adjust output volume (0–100).

## 7. Risks and Mitigations

- **Risk**: VLC integration is platform-dependent (different window handle
  APIs for video).  
  **Mitigation**: `VlcMediaPlayer.set_video_output()` encapsulates the
  platform-specific calls (`set_xwindow`, `set_hwnd`, `set_nsobject`).
  When attachment fails, the UI falls back to Qt video.

- **Risk**: `python-vlc` may not be installed.  
  **Mitigation**: Import `vlc` in a `try`/`except` block, and raise
  `VlcUnavailableError` if unavailable; UI can fall back to QMediaPlayer.
  A separate `probe_vlc_backend()` helper provides a lightweight runtime
  check that is exercised by automated tests.

- **Risk**: Time-stretch and transpose quality depend on VLC configuration
  and platform audio capabilities.  
  **Mitigation**: Configure `vlc.Instance` with `scaletempo` for
  pitch-preserving time-stretch, and express transpose and optional EQ
  profiles via dedicated wrapper methods (`set_pitch_semitones`,
  `set_eq_profile`). Exact filter chains remain tunable without changing
  the UI contract.

## 8. Rollout and Migration

- Phase 1 (initial change):
  - Implement `core/vlc_player.VlcMediaPlayer` with tests using a stubbed
    `vlc` module (no hard dependency on actual VLC at test time).
  - Add feature flag in `core/config.py`.

- Phase 2 (completed):
  - Wire `LessonPlayerApp` / detail view to use `VlcMediaPlayer` for audio
    and embedded video in the main player area, with Qt muted and driving
    progress when VLC is active.  
  - Provide a setting in the UI to toggle backends at runtime.

## 9. Implementation Plan

- [x] Add `specs/vlc-playback-backend.md` (this file).  
- [x] Implement `core/vlc_player.py` with guarded `vlc` import and a minimal
      API.  
- [x] Add tests `tests/test_vlc_player_wrapper.py` that monkeypatch a fake
      `vlc` module and validate the wrapper's behaviour.  
- [x] Wire VLC backend into the UI behind a feature flag and runtime toggle.  
- [x] Add a backend probe helper and tests
      (`core.vlc_player.probe_vlc_backend`,
      `tests/test_vlc_backend_availability_probe.py`).

## 10. Follow-Up and Open Questions

- Future work may adjust VLC filter chains (EQ/pitch) for specific
  platforms without changing the UI or DB contracts.  
- If cross-platform VLC video output needs further tuning, a follow-up
  spec can refine window-handle handling and sync without changing the
  public wrapper API.
