from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt, QEvent

class UpperCaseLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("font-family: 'Courier New';")
        self.textChanged.connect(self.force_uppercase)

    def force_uppercase(self, text):
        if text != text.upper():
            cursor_pos = self.cursorPosition()
            self.blockSignals(True)
            self.setText(text.upper())
            self.setCursorPosition(cursor_pos)
            self.blockSignals(False)

    def keyPressEvent(self, event: QKeyEvent):
        if event.text():
            upper_char = event.text().upper()
            modified_event = QKeyEvent(
                event.type(),
                event.key(),
                event.modifiers(),
                upper_char
            )
            super().keyPressEvent(modified_event)
            return
        super().keyPressEvent(event)

    def insertFromMimeData(self, source):
        if source.hasText():
            self.insertPlainText(source.text().upper())