# ui/widgets/player_controls.py

from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QLabel, QSlider, QVBoxLayout
from PyQt5.QtCore import Qt

from core.media_utils import HALF_TONE_UP_FACTOR


def init_player_controls(app):
    layout = QVBoxLayout()

    # Progress Slider
    app.progress_bar = QSlider(Qt.Horizontal)
    app.progress_bar.setMinimum(0)
    def _on_slider_moved(pos: int):
        # Always update the Qt media player position so existing loop
        # and positionChanged logic continue to work.
        if hasattr(app, "media_player"):
            app.media_player.setPosition(pos)
        # When VLC backend is active, also seek the VLC player so the
        # visible video follows the slider.
        if hasattr(app, "vlc_player") and getattr(app, "vlc_player", None):
            vlc_obj = app.vlc_player
            if hasattr(vlc_obj, "set_position_ms"):
                vlc_obj.set_position_ms(pos)

    app.progress_bar.sliderMoved.connect(_on_slider_moved)
    if hasattr(app, "handle_position_changed"):
        app.media_player.positionChanged.connect(app.handle_position_changed)
    else:
        app.media_player.positionChanged.connect(lambda pos: app.progress_bar.setValue(pos))
    app.media_player.durationChanged.connect(lambda dur: app.progress_bar.setMaximum(dur))
    layout.addWidget(app.progress_bar)

    # Controls
    controls = QHBoxLayout()

    play_btn = QPushButton("Play")
    play_btn.clicked.connect(app.play_video)
    controls.addWidget(play_btn)

    pause_btn = QPushButton("Pause")
    pause_btn.clicked.connect(app.pause_video)
    controls.addWidget(pause_btn)

    stop_btn = QPushButton("Stop")
    stop_btn.clicked.connect(app.stop_video)
    controls.addWidget(stop_btn)

    # Volume
    app.volume_slider = QSlider(Qt.Horizontal)
    app.volume_slider.setRange(0, 100)
    app.volume_slider.setValue(70)
    app.volume_slider.setToolTip("Master volume (0–100)")

    def on_volume(val):
        # When VLC backend is present, mute Qt audio and control VLC volume;
        # otherwise control Qt volume directly.
        if hasattr(app, "vlc_player") and getattr(app, "vlc_player", None):
            app.media_player.setVolume(0)
            app.vlc_player.set_volume(val)
        else:
            app.media_player.setVolume(val)

    app.volume_slider.valueChanged.connect(on_volume)
    # Apply initial volume to current backend
    on_volume(app.volume_slider.value())
    controls.addWidget(QLabel("Volume:"))
    controls.addWidget(app.volume_slider)

    # Speed
    app.speed_slider = QSlider(Qt.Horizontal)
    app.speed_slider.setRange(50, 200)
    app.speed_slider.setValue(100)
    app.speed_slider.valueChanged.connect(lambda val: update_speed_display(app, val))
    controls.addWidget(QLabel("Speed:"))
    controls.addWidget(app.speed_slider)

    app.speed_label = QLabel("1.0x")
    controls.addWidget(app.speed_label)

    # Transpose
    transpose_layout = QHBoxLayout()
    down_btn = QPushButton("\u25BC")
    down_btn.setFixedWidth(30)
    down_btn.clicked.connect(lambda: transpose_step(app, -1))
    transpose_layout.addWidget(down_btn)

    app.transpose_label = QLabel("0")
    app.transpose_label.setFixedWidth(30)
    app.transpose_label.setAlignment(Qt.AlignCenter)
    transpose_layout.addWidget(app.transpose_label)

    up_btn = QPushButton("\u25B2")
    up_btn.setFixedWidth(30)
    up_btn.clicked.connect(lambda: transpose_step(app, 1))
    transpose_layout.addWidget(up_btn)

    controls.addLayout(transpose_layout)

    # Loop / A–B repeat controls (only when supported by app)
    if hasattr(app, "set_loop_start") and hasattr(app, "set_loop_end") and hasattr(app, "toggle_loop"):
        loop_layout = QHBoxLayout()

        loop_a_btn = QPushButton("A")
        loop_a_btn.setFixedWidth(30)
        loop_a_btn.setToolTip("Set loop start (A)")
        loop_a_btn.clicked.connect(app.set_loop_start)
        loop_layout.addWidget(loop_a_btn)

        loop_b_btn = QPushButton("B")
        loop_b_btn.setFixedWidth(30)
        loop_b_btn.setToolTip("Set loop end (B)")
        loop_b_btn.clicked.connect(app.set_loop_end)
        loop_layout.addWidget(loop_b_btn)

        loop_toggle_btn = QPushButton("Loop")
        loop_toggle_btn.setCheckable(True)

        def on_loop_toggled():
            app.toggle_loop()
            loop_toggle_btn.setChecked(getattr(app, "loop_enabled", False))

        loop_toggle_btn.clicked.connect(on_loop_toggled)
        loop_layout.addWidget(loop_toggle_btn)

        controls.addLayout(loop_layout)

    layout.addLayout(controls)
    return layout


def update_speed_display(app, value):
    app.current_speed = value / 100.0
    # Delegate to app-level implementation when available to keep
    # backend-specific logic (Qt vs VLC) in one place.
    if hasattr(app, "apply_transposition"):
        app.apply_transposition()
    else:
        apply_transposition(app)
    app.speed_label.setText(f"{app.current_speed:.1f}x")


def transpose_step(app, delta):
    app.transpose_steps += delta
    if hasattr(app, "apply_transposition"):
        app.apply_transposition()
    else:
        apply_transposition(app)


def apply_transposition(app):
    rate = app.current_speed * (HALF_TONE_UP_FACTOR ** app.transpose_steps)
    app.media_player.setPlaybackRate(rate)
    if hasattr(app, "vlc_player") and getattr(app, "vlc_player", None):
        app.vlc_player.set_rate(rate)
    sign = "+" if app.transpose_steps > 0 else ""
    app.transpose_label.setText(f"{sign}{app.transpose_steps}")
