from PyQt6.QtGui import QFont

class Styles:
    @staticmethod
    def get_factory_font():
        return QFont("Courier New", 15)
    
    @staticmethod
    def get_button_font():
        return QFont("Courier New", 12)
    
    SET_BUTTON_STYLE = """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
    """
    
    RESET_BUTTON_STYLE = """
        QPushButton {
            background-color: #f44336;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
        }
        QPushButton:hover {
            background-color: #d32f2f;
        }
    """