from types import SimpleNamespace

from ui.widgets.master import format_lesson_label
from ui.widgets.detail import extract_lesson_number_from_item
from PyQt5.QtCore import Qt


class StubItem:
    """Minimal stub to emulate the parts of QListWidgetItem we use."""

    def __init__(self, text, user_role_value=None):
        self._text = text
        self._user_role_value = user_role_value

    def text(self):
        return self._text

    def data(self, role):
        if role == Qt.UserRole:
            return self._user_role_value
        return None


def test_format_lesson_label_with_number():
    assert format_lesson_label(5, "Intro") == "5: Intro"


def test_format_lesson_label_without_number():
    assert format_lesson_label(None, "Orphan Lesson") == "Orphan Lesson"


def test_extract_lesson_number_prefers_user_role():
    item = StubItem("999: Something", user_role_value=7)
    assert extract_lesson_number_from_item(item) == 7


def test_extract_lesson_number_parses_text_prefix():
    item = StubItem("12: My Lesson", user_role_value=None)
    assert extract_lesson_number_from_item(item) == 12


def test_extract_lesson_number_handles_missing_or_invalid():
    assert extract_lesson_number_from_item(StubItem("No number", None)) is None
    assert extract_lesson_number_from_item(StubItem("abc: Not numeric", None)) is None
