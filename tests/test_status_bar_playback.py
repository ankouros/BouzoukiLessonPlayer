from ui.main_window import LessonPlayerApp


class DummyMediaPlayer:
    def __init__(self):
        self.play_called = False
        self.pause_called = False
        self.stop_called = False

    def play(self):
        self.play_called = True

    def pause(self):
        self.pause_called = True

    def stop(self):
        self.stop_called = True


class StubApp:
    """Lightweight stand-in with only the attributes play/pause/stop expect."""

    def __init__(self):
        self.media_player = DummyMediaPlayer()
        self.status_messages = []

    def _set_status_message(self, text: str):
        self.status_messages.append(text)

    # From newer LessonPlayerApp implementations
    def _start_playback_immediately(self):
        self.media_player.play()
        self._set_status_message("Play")


def test_play_video_calls_media_player_and_sets_status():
    app = StubApp()

    # Call the unbound method on our stub instance
    LessonPlayerApp.play_video(app)

    assert app.media_player.play_called is True
    assert any("Play" in msg for msg in app.status_messages)


def test_pause_video_calls_media_player_and_sets_status():
    app = StubApp()

    LessonPlayerApp.pause_video(app)

    assert app.media_player.pause_called is True
    assert any("Pause" in msg for msg in app.status_messages)


def test_stop_video_calls_media_player_and_sets_status_and_resets_transpose():
    app = StubApp()
    app.transpose_steps = 5

    # Provide apply_transposition so the method can call it
    def fake_apply_transposition(self):
        # record that it was called by appending a special marker
        app.status_messages.append("apply_transposition_called")

    app.apply_transposition = fake_apply_transposition.__get__(app, StubApp)

    LessonPlayerApp.stop_video(app)

    assert app.media_player.stop_called is True
    assert app.transpose_steps == 0
    assert any("Stop" in msg for msg in app.status_messages)
    assert "apply_transposition_called" in app.status_messages


class DummyLabel:
    def __init__(self):
        self.text = ""

    def setText(self, text):
        self.text = text


class StubAppWithEq:
    def __init__(self):
        self.status_message = DummyLabel()
        self.vlc_player = object()
        self.eq_profile_active = True


def test_status_bar_shows_eq_suffix_when_active():
    app = StubAppWithEq()

    # Invoke the real helper on a stub instance
    LessonPlayerApp._set_status_message(app, "Play")

    assert app.status_message.text.startswith("[VLC+EQ]")


class DummyMediaPlayerWithPosition:
    def __init__(self, start_pos=1000):
        self._pos = start_pos

    def position(self):
        return self._pos

    def setPosition(self, new_pos):
        self._pos = new_pos


class StubAppWithFeedback:
    def __init__(self, media_player, initial_volume=50):
        self.media_player = media_player
        self.feedback_messages = []
        # Minimal slider-like object for volume tests
        class Slider:
            def __init__(self, value):
                self._value = value

            def value(self):
                return self._value

            def setValue(self_inner, val):
                self_inner._value = val

        self.volume_slider = Slider(initial_volume)

    def show_feedback(self, message: str):
        self.feedback_messages.append(message)


def test_seek_forward_5s_increases_position_and_shows_feedback():
    app = StubAppWithFeedback(DummyMediaPlayerWithPosition(start_pos=1000))

    LessonPlayerApp.seek_forward_5s(app)

    assert app.media_player.position() == 6000
    assert any("⏩" in msg for msg in app.feedback_messages)


def test_seek_back_5s_does_not_go_below_zero_and_shows_feedback():
    app = StubAppWithFeedback(DummyMediaPlayerWithPosition(start_pos=3000))

    LessonPlayerApp.seek_back_5s(app)
    assert app.media_player.position() == 0

    app.media_player._pos = 8000
    LessonPlayerApp.seek_back_5s(app)
    assert app.media_player.position() == 3000
    assert any("⏪" in msg for msg in app.feedback_messages)


def test_volume_up_and_down_adjust_slider_and_show_feedback():
    app = StubAppWithFeedback(DummyMediaPlayerWithPosition(), initial_volume=90)

    LessonPlayerApp.volume_up_small(app)
    assert app.volume_slider.value() == 95

    LessonPlayerApp.volume_up_small(app)
    # Should clamp at 100
    assert app.volume_slider.value() == 100

    LessonPlayerApp.volume_down_small(app)
    assert app.volume_slider.value() == 95

    # Step down to zero and clamp
    app.volume_slider.setValue(3)
    LessonPlayerApp.volume_down_small(app)
    assert app.volume_slider.value() == 0

    assert any("Volume" in msg for msg in app.feedback_messages)
