from ui.main_window import LessonPlayerApp


class DummyMediaPlayer:
    def __init__(self):
        self.playback_rate = None

    def setPlaybackRate(self, rate):
        self.playback_rate = rate


class DummyVlcPlayer:
    def __init__(self):
        self.rate = None
        self.pitch_semitones = None

    def set_rate(self, rate):
        self.rate = rate

    def set_pitch_semitones(self, semitones):
        self.pitch_semitones = semitones


class StubApp:
    """Minimal stand-in for LessonPlayerApp to exercise apply_transposition."""

    def __init__(self):
        self.current_speed = 1.0
        self.transpose_steps = 0
        self.media_player = DummyMediaPlayer()
        self.vlc_player = None

    # Reuse the real implementation logic
    apply_transposition = LessonPlayerApp.apply_transposition


def test_apply_transposition_with_vlc_separates_speed_and_pitch():
    app = StubApp()
    app.current_speed = 0.8
    app.transpose_steps = 3
    app.vlc_player = DummyVlcPlayer()

    # Call the shared implementation on our stub instance
    app.apply_transposition()

    # Video and VLC playback should use current_speed only
    assert app.media_player.playback_rate == 0.8
    assert app.vlc_player.rate == 0.8
    # Pitch shift is expressed separately in semitone steps
    assert app.vlc_player.pitch_semitones == 3


def test_apply_transposition_without_vlc_combines_speed_and_pitch():
    app = StubApp()
    app.current_speed = 0.8
    app.transpose_steps = 2
    app.vlc_player = None

    app.apply_transposition()

    # Qt-only path should still combine speed and transpose in playbackRate
    # HALF_TONE_UP_FACTOR ** 2 ~= 1.12246, so expected rate ~= 0.8 * 1.12246
    combined_rate = app.media_player.playback_rate
    assert combined_rate > 0.8
