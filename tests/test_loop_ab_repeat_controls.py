from ui.main_window import LessonPlayerApp


class DummyMediaPlayer:
    def __init__(self, initial_pos=0):
        self._position = initial_pos
        self.set_position_calls = []

    def position(self):
        return self._position

    def setPosition(self, pos):
        self.set_position_calls.append(pos)
        self._position = pos


class DummyProgressBar:
    def __init__(self):
        self.values = []

    def setValue(self, v):
        self.values.append(v)


class StubApp:
    def __init__(self):
        self.media_player = DummyMediaPlayer()
        self.progress_bar = DummyProgressBar()
        self.loop_enabled = False
        self.loop_start_ms = None
        self.loop_end_ms = None
        self.feedback = []
        self.status_messages = []

    def show_feedback(self, msg: str):
        self.feedback.append(msg)

    def _set_status_message(self, msg: str):
        self.status_messages.append(msg)


def test_set_loop_start_and_end_record_positions():
    app = StubApp()
    # Current position simulating media playback
    app.media_player._position = 1000
    LessonPlayerApp.set_loop_start(app)
    assert app.loop_start_ms == 1000

    app.media_player._position = 3000
    LessonPlayerApp.set_loop_end(app)
    assert app.loop_end_ms == 3000


def test_set_loop_end_rejects_before_start():
    app = StubApp()
    app.loop_start_ms = 3000
    app.media_player._position = 2000

    LessonPlayerApp.set_loop_end(app)

    # loop_end_ms should remain unset and feedback should indicate an error
    assert app.loop_end_ms is None
    assert any("must be after" in msg for msg in app.feedback)


def test_toggle_loop_requires_start_and_end_then_toggles_flag():
    app = StubApp()
    # No A/B yet
    LessonPlayerApp.toggle_loop(app)
    assert app.loop_enabled is False
    assert any("Set A and B" in msg for msg in app.feedback)

    # Provide A/B and enable loop
    app.loop_start_ms = 1000
    app.loop_end_ms = 3000
    LessonPlayerApp.toggle_loop(app)
    assert app.loop_enabled is True
    assert any("Loop enabled" in msg for msg in app.status_messages)

    # Disable loop again
    LessonPlayerApp.toggle_loop(app)
    assert app.loop_enabled is False
    assert any("Loop disabled" in msg for msg in app.status_messages)


def test_handle_position_changed_loops_back_to_start_when_enabled():
    app = StubApp()
    app.loop_enabled = True
    app.loop_start_ms = 1000
    app.loop_end_ms = 3000

    # Simulate playback reaching beyond loop end
    LessonPlayerApp.handle_position_changed(app, 3500)

    # Progress bar updated and media position jumped back to start
    assert app.progress_bar.values[-1] == 3500
    assert app.media_player.set_position_calls[-1] == 1000

