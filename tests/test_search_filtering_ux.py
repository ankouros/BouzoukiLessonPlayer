from PyQt5.QtCore import Qt

import ui.widgets.master as master_mod


class DummyDB:
    def __init__(self):
        self.last_query = None

    def fetch_lessons(self, query):
        self.last_query = query
        if query is None:
            return [(1, "Alpha"), (2, "Beta")]
        if "none" in query:
            return []
        return [(3, "Matching Lesson")]


class DummySearchBar:
    def __init__(self):
        self._text = ""

    def setText(self, text):
        self._text = text

    def text(self):
        return self._text


class DummyItem:
    def __init__(self, text):
        self._text = text
        self._flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        self._data = {}

    def text(self):
        return self._text

    def setText(self, text):
        self._text = text

    def flags(self):
        return self._flags

    def setFlags(self, flags):
        self._flags = flags

    def setData(self, role, value):
        self._data[role] = value

    def data(self, role):
        return self._data.get(role)

    def isSelectable(self):
        return bool(self._flags & Qt.ItemIsSelectable)


class DummyMasterList:
    def __init__(self):
        self._items = []
        self._current = None

    def currentItem(self):
        return self._current

    def currentRow(self):
        if self._current in self._items:
            return self._items.index(self._current)
        return -1

    def count(self):
        return len(self._items)

    def clear(self):
        self._items.clear()
        self._current = None

    def addItem(self, item):
        self._items.append(item)

    def setCurrentItem(self, item):
        self._current = item

    def item(self, index):
        return self._items[index]


class DummyApp:
    def __init__(self):
        self.search_bar = DummySearchBar()
        self.master_list = DummyMasterList()
        self.db = DummyDB()


def test_update_master_list_uses_search_query_and_placeholder_includes_query(monkeypatch):
    # Avoid constructing real Qt list items
    monkeypatch.setattr(master_mod, "QListWidgetItem", DummyItem)
    app = DummyApp()

    # Case 1: non-empty query with results
    app.search_bar.setText("match")
    master_mod.update_master_list(app)
    assert app.db.last_query == "match"
    assert app.master_list.count() == 1
    assert "Matching Lesson" in app.master_list.item(0).text()

    # Case 2: non-empty query with no results
    app.search_bar.setText("none-here")
    master_mod.update_master_list(app)
    assert app.db.last_query == "none-here"
    assert app.master_list.count() == 1
    placeholder = app.master_list.item(0)
    assert "none-here" in placeholder.text()
    assert not (placeholder.flags() & Qt.ItemIsSelectable)


def test_focus_first_lesson_selects_item_and_updates_detail(monkeypatch):
    monkeypatch.setattr(master_mod, "QListWidgetItem", DummyItem)
    app = DummyApp()

    # Populate with default lessons (query=None)
    app.search_bar.setText("")

    calls = {}

    def fake_update_detail_view(app_arg, item):
        calls["called"] = True
        calls["text"] = item.text()

    monkeypatch.setattr(master_mod, "update_detail_view", fake_update_detail_view)

    master_mod.update_master_list(app)
    assert app.master_list.count() == 2

    master_mod.focus_first_lesson(app)

    assert calls.get("called") is True
    assert app.master_list.currentRow() == 0
    assert calls["text"] == app.master_list.item(0).text()
