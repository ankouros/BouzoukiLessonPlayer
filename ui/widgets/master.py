from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QMessageBox,
)
from PyQt5.QtGui import QPixmap, QIcon, QCursor
from PyQt5.QtCore import Qt
import os
from ui.widgets.detail import update_detail_view


def create_master_panel(app):
    widget = QWidget()
    layout = QVBoxLayout(widget)

    # --- Top row: Logo + Search input + Voice button ---
    top_row = QHBoxLayout()

    # Clickable logo
    logo_label = QLabel()
    icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "bouzouki.png")
    pixmap = QPixmap(icon_path).scaledToHeight(30, Qt.SmoothTransformation)
    logo_label.setPixmap(pixmap)
    logo_label.setCursor(QCursor(Qt.PointingHandCursor))
    logo_label.setToolTip("About Bouzouki Lesson Player")
    logo_label.mousePressEvent = lambda event: show_about_dialog(app)
    top_row.addWidget(logo_label)

    # Search bar with icon (search + clear)
    search_icon = QIcon(os.path.join(os.path.dirname(__file__), "..", "..", "resources", "search.png"))
    app.search_bar = QLineEdit()
    app.search_bar.setPlaceholderText("Search lessons or videos...")
    app.search_bar.setClearButtonEnabled(True)
    app.search_bar.setStyleSheet("""
        QLineEdit {
            padding-left: 24px;
        }
    """)
    app.search_bar.textChanged.connect(lambda: update_master_list(app))
    app.search_bar.returnPressed.connect(lambda: focus_first_lesson(app))
    top_row.addWidget(app.search_bar, stretch=1)

    # Place icon on top of line edit
    search_icon_label = QLabel()
    search_icon_label.setPixmap(search_icon.pixmap(16, 16))
    search_icon_label.setStyleSheet("margin-left: -24px;")
    search_icon_label.setFixedSize(20, 20)
    top_row.addWidget(search_icon_label)

    # Voice search button (placeholder)
    voice_icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "microphone.png")
    voice_btn = QPushButton()
    voice_btn.setIcon(QIcon(voice_icon_path))
    voice_btn.setFixedSize(30, 30)
    voice_btn.setCursor(QCursor(Qt.PointingHandCursor))
    voice_btn.setToolTip("Voice search (coming soon)")
    voice_btn.clicked.connect(lambda: QMessageBox.information(app, "Voice Search", "Voice search coming soon!"))
    top_row.addWidget(voice_btn)

    layout.addLayout(top_row)

    # --- Master list ---
    app.master_list = QListWidget()
    app.master_list.itemClicked.connect(lambda item: update_detail_view(app, item))
    layout.addWidget(app.master_list)

    return widget


def format_lesson_label(lesson_number, lesson_name):
    """Format the label shown in the master list for a lesson.

    If lesson_number is None or falsy, use only the name.
    """
    return f"{lesson_number}: {lesson_name}" if lesson_number else lesson_name


def update_master_list(app):
    search_query = app.search_bar.text().strip()
    lessons = app.db.fetch_lessons(search_query or None)

    # Preserve current selection by lesson_number if possible
    selected_number = None
    current_item = app.master_list.currentItem()
    if current_item is not None:
        selected_number = current_item.data(Qt.UserRole)

    app.master_list.clear()

    if not lessons:
        placeholder_text = "No lessons found"
        if search_query:
            placeholder_text = f"No lessons found for '{search_query}'"
        placeholder = QListWidgetItem(placeholder_text)
        placeholder.setFlags(placeholder.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
        app.master_list.addItem(placeholder)
        return

    for lesson_number, lesson_name in lessons:
        label = format_lesson_label(lesson_number, lesson_name)
        item = QListWidgetItem(label)
        item.setData(Qt.UserRole, lesson_number)
        app.master_list.addItem(item)
        if selected_number is not None and lesson_number == selected_number:
            app.master_list.setCurrentItem(item)


def focus_first_lesson(app):
    """Select and show the first lesson in the list, if any.

    This is used to make the search bar's Enter key behaviour more
    intuitive: after typing a query, pressing Enter jumps to the first
    matching lesson and updates the detail view.
    """
    if not hasattr(app, "master_list") or app.master_list.count() == 0:
        return
    first_item = app.master_list.item(0)
    if not first_item or not first_item.isSelectable():
        return
    app.master_list.setCurrentItem(first_item)
    update_detail_view(app, first_item)


def show_about_dialog(parent):
    QMessageBox.information(
        parent,
        "About Bouzouki Lesson Player",
        "Bouzouki Lesson Player\nVersion 1.0\n\nCrafted with passion for music and code."
    )
