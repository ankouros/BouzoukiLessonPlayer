import types

from core import theme_manager


def test_load_theme_appends_xml_suffix(monkeypatch):
    recorded = {}

    def fake_apply_stylesheet(app, theme):
        recorded["theme"] = theme

    monkeypatch.setattr(theme_manager, "apply_stylesheet", fake_apply_stylesheet)

    theme_manager.load_theme(app=None, theme="dark_teal")

    assert recorded["theme"] == "dark_teal.xml"


def test_load_theme_does_not_double_append_xml(monkeypatch):
    recorded = {}

    def fake_apply_stylesheet(app, theme):
        recorded["theme"] = theme

    monkeypatch.setattr(theme_manager, "apply_stylesheet", fake_apply_stylesheet)

    theme_manager.load_theme(app=None, theme="light_blue.xml")

    assert recorded["theme"] == "light_blue.xml"

