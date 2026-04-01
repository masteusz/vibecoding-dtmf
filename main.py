from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from dtmf.audio import AudioInitError, init as audio_init
from dtmf.ui import KeypadWidget


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("DTMF Explorer")

    audio_error: str | None = None
    try:
        audio_init()
    except AudioInitError as exc:
        audio_error = str(exc)

    window = QMainWindow()
    window.setWindowTitle("DTMF Explorer")

    keypad = KeypadWidget(audio_error=audio_error)
    window.setCentralWidget(keypad)
    window.setMinimumSize(460, 400)
    window.show()

    keypad.setFocus()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
