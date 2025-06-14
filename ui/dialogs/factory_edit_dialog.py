from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QWidget, QToolTip, QFrame
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt


class ModernLineEdit(QLineEdit):
    def __init__(self, text="", placeholder="", parent=None):
        super().__init__(text, parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #B0B0B0;
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 14px;
                background-color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 2px solid #4A90E2;
                padding: 7px 9px;
            }
        """)
        self.setMinimumHeight(35)


class LabeledInputGroup(QWidget):
    def __init__(self, label_text, initial_value="", placeholder="", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.label = QLabel(label_text)
        self.input = ModernLineEdit(initial_value, placeholder)

        layout.addWidget(self.label)
        layout.addWidget(self.input)
        self.setLayout(layout)


class FactoryEditDialog(QDialog):
    def __init__(self, current_name="", current_location="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Factory Information")
        self.setFixedSize(500, 260)
        self.setStyleSheet("""
            QDialog {
                background-color: #F9F9F9;
            }
            QLabel {
                font-family: Segoe UI;
                font-size: 14px;
                color: #333333;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)  # Space between groups

        # Group 1: Factory Name
        self.name_group = LabeledInputGroup(
            "Factory Name:",
            current_name,
            "Enter factory name"
        )

        # Group 2: Factory Location
        self.location_group = LabeledInputGroup(
            "Factory Location:",
            current_location,
            "Enter factory location"
        )

        main_layout.addWidget(self.name_group)
        main_layout.addWidget(self.location_group)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                font-size: 14px;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #F0F0F0;
            }
            QPushButton:default {
                background-color: #4A90E2;
                color: white;
                border: none;
            }
            QPushButton:cancel {
                background-color: #E74C3C;
                color: white;
                border: none;
            }
        """)
        button_box.accepted.connect(self.validate_inputs)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box, alignment=Qt.AlignmentFlag.AlignRight)

    def validate_inputs(self):
        name = self.name_group.input.text().strip()
        location = self.location_group.input.text().strip()

        if not name:
            QToolTip.showText(
                self.name_group.input.mapToGlobal(self.name_group.input.rect().topLeft()),
                "Factory Name is required",
                self.name_group.input
            )
            self.name_group.input.setFocus()
            return

        if not location:
            QToolTip.showText(
                self.location_group.input.mapToGlobal(self.location_group.input.rect().topLeft()),
                "Factory Location is required",
                self.location_group.input
            )
            self.location_group.input.setFocus()
            return

        self.accept()

    def get_factory_info(self):
        return (
            self.name_group.input.text().strip(),
            self.location_group.input.text().strip()
        )