from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtGui import QKeyEvent, QPalette, QColor, QIntValidator, QDoubleValidator
from PyQt6.QtCore import Qt, QEvent
from ui.utils.upper_case_line_edit import UpperCaseLineEdit

class TableItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        if index.row() == 0 or index.row() == self.parent().rowCount() - 1:
            return None
        if index.row() == 1 and index.column() >= 2:
            editor = super().createEditor(parent, option, index)
            return editor
        if index.row() >= 2 and index.row() < self.parent().rowCount() - 1:
            editor = super().createEditor(parent, option, index)
            if index.column() == 1:
                validator = QIntValidator(1, 9, parent)
                editor.setValidator(validator)
            elif index.column() >= 2:
                validator = QDoubleValidator(0, 9999, 2, parent)
                validator.setNotation(
                    QDoubleValidator.Notation.StandardNotation)
                editor.setValidator(validator)
            return editor
        return None

    def eventFilter(self, editor, event):
        if isinstance(event, QKeyEvent):
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right,
                               Qt.Key.Key_Up, Qt.Key.Key_Down):
                self.commitData.emit(editor)
                self.closeEditor.emit(
                    editor, QStyledItemDelegate.EndEditHint.NoHint)
                return True
        return super().eventFilter(editor, event)

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter
        if not index.data(Qt.ItemDataRole.DisplayRole):
            option.palette.setColor(
                QPalette.ColorRole.Text, QColor(150, 150, 150))
            if index.row() == 1 and index.column() >= 2:
                option.text = f"SIZE {index.column()-1}"
            elif index.row() >= 2 and index.row() < self.parent().rowCount() - 1:
                if index.column() == 0:
                    option.text = "PANEL NAME"
                elif index.column() == 1:
                    option.text = "0"
                elif index.column() >= 2:
                    option.text = "0.00"

class UpperCaseItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index):
        if index.column() == 0 or (index.row() == 1 and index.column() >= 2):
            editor = UpperCaseLineEdit(parent)
            return editor
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, UpperCaseLineEdit):
            editor.blockSignals(True)
            editor.setText(index.data(Qt.ItemDataRole.DisplayRole) or "")
            editor.blockSignals(False)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, UpperCaseLineEdit):
            model.setData(index, editor.text().strip().upper(),
                          Qt.ItemDataRole.EditRole)
        else:
            super().setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def eventFilter(self, editor, event):
        if isinstance(editor, UpperCaseLineEdit):
            if event.type() == QEvent.Type.KeyPress:
                if event.text():
                    editor.keyPressEvent(event)
                    self.commitData.emit(editor)
                    return True
            elif event.type() == QEvent.Type.FocusOut:
                self.commitData.emit(editor)
                self.closeEditor.emit(
                    editor, QStyledItemDelegate.EndEditHint.NoHint)
                return True
        return super().eventFilter(editor, event)