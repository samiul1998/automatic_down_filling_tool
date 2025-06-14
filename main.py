import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import QTimer
from splash_screen import SplashScreen
from ui.main_window import DownAllocationApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Courier New", 10)
    app.setFont(font)

    splash_path = os.path.join(os.path.dirname(__file__), 'assets', 'splash_image.png')
    pixmap = QPixmap(os.path.abspath(splash_path))

    splash = SplashScreen(pixmap, version="1.0.0")
    splash.show_centered()
    splash.start_animation(2500)

    def transition_to_main():
        def show_main():
            splash.deleteLater()
            main_window = DownAllocationApp()
            main_window.showMaximized()

        splash.fade_out(callback=show_main)

    QTimer.singleShot(2700, transition_to_main)

    sys.exit(app.exec())