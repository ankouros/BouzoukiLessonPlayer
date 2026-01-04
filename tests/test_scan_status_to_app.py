from ui.searchUpdateDatabase import FolderScannerWorker, propagate_status_to_app


class StubApp:
    def __init__(self):
        self.messages = []

    def _set_status_message(self, text: str):
        self.messages.append(text)


def test_propagate_status_to_app_calls_status_method():
    app = StubApp()

    propagate_status_to_app(app, "Scanning...")

    assert app.messages == ["Scanning..."]


def test_folder_scanner_worker_status_signal_can_propagate_to_app():
    """Directly emitting the worker's status signal should be able to
    propagate messages to an app reference via propagate_status_to_app."""
    app = StubApp()
    worker = FolderScannerWorker(db_path=":memory:", folder="/")

    # Connect status signal to propagator
    worker.status.connect(lambda msg: propagate_status_to_app(app, msg))

    # Emit a status update manually
    worker.status.emit("Indexing...")

    assert "Indexing..." in app.messages

