from core.database_manager import DatabaseManager
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtCore import Qt

from core.database import connect_to_db
from ui.widgets.master import create_master_panel, update_master_list
from ui.widgets.detail import create_detail_panel


def init_master_detail(app):
    splitter = QSplitter(Qt.Horizontal)

    # Left Panel
    master_panel = create_master_panel(app)
    splitter.addWidget(master_panel)

    # Right Panel (creates and assigns app.right_panel_layout inside)
    detail_panel = create_detail_panel(app)
    splitter.addWidget(detail_panel)

    # Bias layout so the detail view gets more space on wide screens
    splitter.setStretchFactor(0, 1)
    splitter.setStretchFactor(1, 2)

    # Connect to DB and populate UI
    app.db = DatabaseManager(app.db_path)
    update_master_list(app)

    return splitter
