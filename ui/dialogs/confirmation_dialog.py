from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
from PyQt6.QtCore import Qt

class ConfirmationDialog(QDialog):
    def __init__(self, title="Confirm Action", message="Are you sure you want to proceed?", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 200)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowCloseButtonHint)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        self.label = QLabel(message)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI';
                font-size: 14px;
                color: #333;
                padding: 20px;
            }
        """)
        layout.addWidget(self.label)
        
        button_box = QDialogButtonBox()
        button_box.setCenterButtons(True)
        
        self.yes_btn = button_box.addButton("Yes", QDialogButtonBox.ButtonRole.AcceptRole)
        self.no_btn = button_box.addButton("No", QDialogButtonBox.ButtonRole.RejectRole)
        
        self.yes_btn.clicked.connect(self.accept)
        self.no_btn.clicked.connect(self.reject)
        
        button_style = """
            QPushButton {
                font-family: 'Segoe UI';
                font-size: 13px;
                min-width: 80px;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            QPushButton[text="Yes"] {
                background-color: #4285F4;
                color: white;
            }
            QPushButton[text="Yes"]:hover {
                background-color: #3367D6;
            }
            QPushButton[text="No"] {
                background-color: #F1F3F4;
                color: #3C4043;
            }
            QPushButton[text="No"]:hover {
                background-color: #E8EAED;
            }
        """
        button_box.setStyleSheet(button_style)
        
        layout.addWidget(button_box)
        
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 8px;
            }
        """)