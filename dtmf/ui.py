from __future__ import annotations

from functools import partial

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QFocusEvent, QFont, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dtmf.audio import DTMF_KEYS, DTMFKey, play_tone, stop_tone

# Qt key → DTMF button label
_KEY_MAP: dict[int, str] = {
    Qt.Key.Key_0: "0",
    Qt.Key.Key_1: "1",
    Qt.Key.Key_2: "2",
    Qt.Key.Key_3: "3",
    Qt.Key.Key_4: "4",
    Qt.Key.Key_5: "5",
    Qt.Key.Key_6: "6",
    Qt.Key.Key_7: "7",
    Qt.Key.Key_8: "8",
    Qt.Key.Key_9: "9",
    Qt.Key.Key_Asterisk: "*",
    Qt.Key.Key_NumberSign: "#",
    Qt.Key.Key_A: "A",
    Qt.Key.Key_B: "B",
    Qt.Key.Key_C: "C",
    Qt.Key.Key_D: "D",
}

_MONO_FONT = QFont("Courier New")
_MONO_FONT.setStyleHint(QFont.StyleHint.TypeWriter)
_MONO_FONT.setPointSize(10)

_BUTTON_STYLE_IDLE = (
    "QPushButton {"
    "  background-color: #3c3c3c;"
    "  color: #f0f0f0;"
    "  border: 2px solid #222;"
    "  border-radius: 6px;"
    "}"
    "QPushButton:hover:enabled {"
    "  background-color: #505050;"
    "  border-color: #555;"
    "}"
    "QPushButton:disabled {"
    "  background-color: #2a2a2a;"
    "  color: #555;"
    "  border-color: #1a1a1a;"
    "}"
)

_BUTTON_STYLE_ACTIVE = (
    "QPushButton {"
    "  background-color: #d07000;"
    "  color: #fff;"
    "  border: 3px solid #a05000;"
    "  border-radius: 6px;"
    "}"
)

_LABEL_STYLE = "color: #aaa; background: transparent;"
_ERROR_STYLE = (
    "background-color: #cc2222;"
    "color: white;"
    "padding: 8px 12px;"
    "border-radius: 4px;"
    "font-weight: bold;"
)


class KeyButton(QPushButton):
    """A single DTMF key button. Emits key_pressed on left-click; release is
    handled globally by KeypadWidget's event filter."""

    key_pressed = Signal(object)  # emits DTMFKey

    def __init__(self, dtmf_key: DTMFKey, parent: QWidget | None = None) -> None:
        super().__init__(dtmf_key.label, parent)
        self.dtmf_key = dtmf_key
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.setFont(font)
        self.setMinimumSize(70, 70)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(_BUTTON_STYLE_IDLE)

    def set_active(self, active: bool) -> None:
        self.setStyleSheet(_BUTTON_STYLE_ACTIVE if active else _BUTTON_STYLE_IDLE)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.key_pressed.emit(self.dtmf_key)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        # Handled by KeypadWidget.eventFilter — accept to suppress Qt default
        event.accept()


class KeypadWidget(QWidget):
    """4×4 DTMF keypad with column/row frequency labels."""

    def __init__(self, audio_error: str | None = None) -> None:
        super().__init__()
        self._active_button: KeyButton | None = None
        self._active_kbd_label: str | None = None
        self._mouse_pressed: bool = False
        self._buttons: dict[str, KeyButton] = {}
        self._disabled = audio_error is not None

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("background-color: #1e1e1e;")
        self._build_layout(audio_error)

        # Global event filter to catch mouse release anywhere on screen
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self, audio_error: str | None) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        if audio_error:
            banner = QLabel(f"⚠  Audio unavailable: {audio_error}")
            banner.setStyleSheet(_ERROR_STYLE)
            banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            outer.addWidget(banner)

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)

        col_freqs = sorted({k.col_freq for k in DTMF_KEYS})
        row_freqs = sorted({k.row_freq for k in DTMF_KEYS})

        # Column frequency headers — "1209 Hz" across the top
        for col_idx, freq in enumerate(col_freqs):
            lbl = QLabel(f"{int(freq)} Hz")
            lbl.setFont(_MONO_FONT)
            lbl.setStyleSheet(_LABEL_STYLE)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedHeight(22)
            grid.addWidget(lbl, 0, col_idx + 1)

        # Row frequency labels — just the number to keep the column narrow
        for row_idx, freq in enumerate(row_freqs):
            lbl = QLabel(str(int(freq)))
            lbl.setFont(_MONO_FONT)
            lbl.setStyleSheet(_LABEL_STYLE)
            lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            lbl.setContentsMargins(0, 0, 6, 0)
            grid.addWidget(lbl, row_idx + 1, 0)

        # Buttons
        for key in DTMF_KEYS:
            btn = KeyButton(key)
            if self._disabled:
                btn.setEnabled(False)
            btn.key_pressed.connect(partial(self._activate_from_mouse, btn))
            grid.addWidget(btn, key.row_index + 1, key.col_index + 1)
            self._buttons[key.label] = btn

        # Label column and header row stay compact; button area gets all extra space
        grid.setColumnStretch(0, 0)
        grid.setRowStretch(0, 0)
        for i in range(1, 5):
            grid.setColumnStretch(i, 1)
            grid.setRowStretch(i, 1)

        outer.addWidget(grid_widget)

    # ------------------------------------------------------------------
    # Activation / deactivation
    # ------------------------------------------------------------------

    def _activate(self, button: KeyButton, dtmf_key: DTMFKey) -> None:
        if self._active_button is not None and self._active_button is not button:
            self._active_button.set_active(False)
        button.set_active(True)
        self._active_button = button
        play_tone(dtmf_key.row_freq, dtmf_key.col_freq)

    def _deactivate(self) -> None:
        if self._active_button is not None:
            self._active_button.set_active(False)
            self._active_button = None
        self._active_kbd_label = None
        stop_tone()

    def _activate_from_mouse(self, button: KeyButton, key: object) -> None:
        self._mouse_pressed = True
        if isinstance(key, DTMFKey):
            self._activate(button, key)

    # ------------------------------------------------------------------
    # Global mouse-release event filter
    # ------------------------------------------------------------------

    def eventFilter(self, _watched: QObject, event: QEvent) -> bool:
        if (
            self._mouse_pressed
            and event.type() == QEvent.Type.MouseButtonRelease
            and isinstance(event, QMouseEvent)
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self._mouse_pressed = False
            self._deactivate()
        return False  # never consume the event

    # ------------------------------------------------------------------
    # Keyboard events
    # ------------------------------------------------------------------

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return
        label = _KEY_MAP.get(event.key())
        if label is None:
            super().keyPressEvent(event)
            return
        if label == self._active_kbd_label:
            return
        self._active_kbd_label = label
        self._mouse_pressed = False
        btn = self._buttons.get(label)
        if btn is not None and btn.isEnabled():
            self._activate(btn, btn.dtmf_key)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return
        label = _KEY_MAP.get(event.key())
        if label is not None and label == self._active_kbd_label:
            self._deactivate()
        else:
            super().keyReleaseEvent(event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self._deactivate()
        super().focusOutEvent(event)
