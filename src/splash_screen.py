import os
import sys
from PyQt6.QtWidgets import (
    QSplashScreen, QProgressBar, QVBoxLayout, QWidget, QApplication,
    QGraphicsOpacityEffect
)
from PyQt6.QtGui import QPixmap, QColor, QFont, QPainter
from PyQt6.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve

class SplashScreen(QSplashScreen):
    def __init__(self, pixmap=None, version="1.0.0"):
        if pixmap and not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                600, 400, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            super().__init__(scaled_pixmap, Qt.WindowType.WindowStaysOnTopHint)
        else:
            blank_pixmap = QPixmap(600, 400)
            blank_pixmap.fill(Qt.GlobalColor.white)
            super().__init__(blank_pixmap, Qt.WindowType.WindowStaysOnTopHint)

        self.version = version
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setEnabled(False)

        self.setup_ui()
        self.setup_fade_effect()

    def setup_ui(self):
        self.container = QWidget(self)
        self.container.setGeometry(self.rect())

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 20, 20)
        layout.setSpacing(0)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 3px;
                background-color: rgba(0, 0, 0, 20);
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 150),
                    stop:1 rgba(200, 200, 255, 200)
                );
                border-radius: 2px;
            }
        """)
        layout.addStretch()
        layout.addWidget(self.progress)

        self.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        self.showMessage(
            f"Version {self.version}",
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
            color=QColor(255, 255, 255, 180)
        )

        self.progress_value = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)

    def setup_fade_effect(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(800)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def fade_in(self):
        self.opacity_effect.setOpacity(0.0)
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def fade_out(self, callback=None):
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.finished.connect(callback)
        self.fade_anim.start()

    def start_animation(self, duration=2500):
        self.progress_value = 0
        self.progress.setValue(0)
        interval = duration // 100
        self.timer.start(interval)
        self.fade_in()

    def update_progress(self):
        if self.progress_value < 100:
            self.progress_value += 1
            self.progress.setValue(self.progress_value)
        else:
            self.timer.stop()

    def show_centered(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        splash_geometry = self.frameGeometry()
        splash_geometry.moveCenter(screen_geometry.center())
        self.move(splash_geometry.topLeft())
        self.show()

    def drawContents(self, painter):
        shadow_rect = QRect(5, 5, self.width()-10, self.height()-10)
        painter.fillRect(shadow_rect, QColor(0, 0, 0, 30))
        main_rect = QRect(0, 0, self.width()-5, self.height()-5)
        painter.drawPixmap(main_rect, self.pixmap())
        super().drawContents(painter)