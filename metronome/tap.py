import sys
import time
import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt

GROOVE_FILE = "metronome/grooves.json"

class TapGroove(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tap Groove Creator")
        self.setGeometry(300, 300, 400, 200)
        self.label = QLabel("Left click = regular, Right click = accent\nSpace = undo, Enter = save", self)
        self.label.setGeometry(20, 60, 360, 80)
        self.clicks = []
        self.timestamps = []
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._tap(False)
        elif event.button() == Qt.RightButton:
            self._tap(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space and self.timestamps:
            self.clicks.pop()
            self.timestamps.pop()
            print("Undo last tap")
        elif event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self._save_groove()

    def _tap(self, accent):
        now = time.time()
        self.timestamps.append(now)
        self.clicks.append(accent)
        print("Tap", "Accent" if accent else "Regular", f"at {now:.2f}s")

    def _save_groove(self):
        if len(self.timestamps) < 2:
            print("Not enough taps to compute tempo.")
            return

        intervals = [t2 - t1 for t1, t2 in zip(self.timestamps, self.timestamps[1:])]
        avg_interval = sum(intervals) / len(intervals)
        bpm = 60.0 / avg_interval
        accents = [i for i, a in enumerate(self.clicks) if a]

        groove = {
            "pulses": len(self.clicks),
            "accents": accents,
            "swing": False
        }

        name = f"Tapped Groove {int(time.time())}"
        print(f"\nSaved '{name}' with {groove['pulses']} pulses, BPM: {bpm:.1f}, Accents: {accents}")

        # Save to grooves.json
        try:
            grooves = json.load(open(GROOVE_FILE)) if Path(GROOVE_FILE).exists() else {}
            grooves[name] = groove
            with open(GROOVE_FILE, "w") as f:
                json.dump(grooves, f, indent=2)
            print("✔️ Groove saved to grooves.json")
        except Exception as e:
            print("❌ Failed to save:", e)

        self.clicks.clear()
        self.timestamps.clear()


def main():
    app = QApplication(sys.argv)
    window = TapGroove()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
