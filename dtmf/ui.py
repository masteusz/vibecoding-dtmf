from __future__ import annotations

from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFocusEvent, QFont, QKeyEvent, QMouseEvent
from PySide6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout, QWidget

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
    """A single DTMF key button. Emits signals on press and release."""

    key_pressed = Signal(object)  # emits DTMFKey
    key_released = Signal()

    def __init__(self, dtmf_key: DTMFKey, parent: QWidget | None = None) -> None:
        super().__init__(dtmf_key.label, parent)
        self.dtmf_key = dtmf_key
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.setFont(font)
        self.setMinimumSize(70, 70)
        # Keyboard focus goes to the KeypadWidget, not individual buttons
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(_BUTTON_STYLE_IDLE)

    def set_active(self, active: bool) -> None:
        self.setStyleSheet(_BUTTON_STYLE_ACTIVE if active else _BUTTON_STYLE_IDLE)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.grabMouse()
            self.key_pressed.emit(self.dtmf_key)
        event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.releaseMouse()
            self.key_released.emit()
        event.accept()


class KeypadWidget(QWidget):
    """4×4 DTMF keypad with column/row frequency labels."""

    def __init__(self, audio_error: str | None = None) -> None:
        super().__init__()
        self._active_button: KeyButton | None = None
        self._active_kbd_label: str | None = None
        # label → button, for keyboard dispatch
        self._buttons: dict[str, KeyButton] = {}
        self._disabled = audio_error is not None

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setStyleSheet("background-color: #1e1e1e;")
        self._build_layout(audio_error)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self, audio_error: str | None) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        if audio_error:
            banner = QLabel(f"\u26a0\ufe0f  Audio unavailable: {audio_error}")
            banner.setStyleSheet(_ERROR_STYLE)
            banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
            outer.addWidget(banner)

        grid_widget = QWidget()
        grid_widget.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_widget)
        grid.setSpacing(6)
        grid.setContentsMargins(0, 0, 0, 0)

        # Derive unique sorted col/row freqs from DTMF_KEYS
        col_freqs = sorted({k.col_freq for k in DTMF_KEYS})
        row_freqs = sorted({k.row_freq for k in DTMF_KEYS})

        # Column frequency headers (row 0, cols 1–4)
        for col_idx, freq in enumerate(col_freqs):
            lbl = QLabel(f"{int(freq)} Hz")
            lbl.setFont(_MONO_FONT)
            lbl.setStyleSheet(_LABEL_STYLE)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(lbl, 0, col_idx + 1)

        # Row frequency labels (rows 1–4, col 0)
        for row_idx, freq in enumerate(row_freqs):
            lbl = QLabel(f"{int(freq)} Hz")
            lbl.setFont(_MONO_FONT)
            lbl.setStyleSheet(_LABEL_STYLE)
            lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            lbl.setContentsMargins(0, 0, 6, 0)
            grid.addWidget(lbl, row_idx + 1, 0)

        # Buttons (rows 1–4, cols 1–4)
        for key in DTMF_KEYS:
            btn = KeyButton(key)
            if self._disabled:
                btn.setEnabled(False)
            btn.key_pressed.connect(partial(self._on_button_pressed, btn))
            btn.key_released.connect(self._on_button_released)
            grid.addWidget(btn, key.row_index + 1, key.col_index + 1)
            self._buttons[key.label] = btn

        outer.addWidget(grid_widget)

    # ------------------------------------------------------------------
    # Activation logic
    # ------------------------------------------------------------------

    def _on_button_pressed(self, button: KeyButton, key: object) -> None:
        dtmf_key = key  # Signal emits DTMFKey as object
        if self._active_button is not None and self._active_button is not button:
            self._active_button.set_active(False)
        button.set_active(True)
        self._active_button = button
        if isinstance(dtmf_key, DTMFKey):
            play_tone(dtmf_key.row_freq, dtmf_key.col_freq)

    def _on_button_released(self) -> None:
        if self._active_button is not None:
            self._active_button.set_active(False)
            self._active_button = None
        self._active_kbd_label = None
        stop_tone()

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
        # Ignore if this key is already the active keyboard key
        if label == self._active_kbd_label:
            return
        self._active_kbd_label = label
        btn = self._buttons.get(label)
        if btn is not None and btn.isEnabled():
            self._on_button_pressed(btn, btn.dtmf_key)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return
        label = _KEY_MAP.get(event.key())
        if label is not None and label == self._active_kbd_label:
            self._on_button_released()
        else:
            super().keyReleaseEvent(event)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        # Stop tone if window loses focus while a key is held
        self._on_button_released()
        super().focusOutEvent(event)
