"""System Tray Icon & Notification Area integration for Desktop Pet.
Ensures persistent access to settings and pet recovery even in click-through mode.
"""

from typing import Callable
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


def create_default_tray_icon() -> QIcon:
    """Generates a cute 32x32 paw/cat icon for the Windows system tray."""
    pm = QPixmap(32, 32)
    pm.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Cute cat head icon
    painter.setBrush(QColor(245, 142, 54))
    painter.setPen(QColor(55, 30, 20))

    # Ears
    from PyQt6.QtGui import QPolygon
    from PyQt6.QtCore import QPoint
    left_ear = QPolygon([QPoint(5, 14), QPoint(10, 4), QPoint(15, 14)])
    right_ear = QPolygon([QPoint(17, 14), QPoint(22, 4), QPoint(27, 14)])
    painter.drawPolygon(left_ear)
    painter.drawPolygon(right_ear)

    # Face circle
    painter.drawEllipse(4, 10, 24, 20)

    # Eyes
    painter.setBrush(QColor(38, 42, 53))
    painter.drawEllipse(9, 17, 4, 4)
    painter.drawEllipse(19, 17, 4, 4)

    # Nose
    painter.setBrush(QColor(255, 175, 175))
    painter.drawEllipse(14, 21, 4, 3)

    painter.end()
    return QIcon(pm)


class PetTrayIcon(QSystemTrayIcon):
    """System tray controller."""

    def __init__(
        self,
        parent: QWidget,
        pet_name: str,
        on_open_manager: Callable[[], None],
        on_trigger_action: Callable[[str], None],
        on_toggle_click_through: Callable[[bool], None],
        on_toggle_always_on_top: Callable[[bool], None],
        is_click_through: bool,
        is_always_on_top: bool,
        on_quit: Callable[[], None]
    ):
        super().__init__(create_default_tray_icon(), parent)
        self.setToolTip(f"🐾 {pet_name} - Desktop Companion")

        self.menu = QMenu()
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e24;
                color: #e2e8f0;
                border: 1px solid #3b4252;
                border-radius: 8px;
                padding: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
        """)

        title_act = self.menu.addAction(f"🐾 {pet_name}")
        font = title_act.font()
        font.setBold(True)
        title_act.setFont(font)
        title_act.setEnabled(False)

        self.menu.addSeparator()

        manager_act = self.menu.addAction("🎨 Sprite & Pet Manager...")
        manager_act.triggered.connect(on_open_manager)

        self.menu.addSeparator()

        act_jump = self.menu.addAction("🦘 Hop / Jump")
        act_jump.triggered.connect(lambda: on_trigger_action("jump"))

        act_run = self.menu.addAction("⚡ Run / Zoomies")
        act_run.triggered.connect(lambda: on_trigger_action("run"))

        act_nap = self.menu.addAction("💤 Take a Nap")
        act_nap.triggered.connect(lambda: on_trigger_action("sleep"))

        self.menu.addSeparator()

        self.act_ghost = self.menu.addAction("👻 Click-Through Mode")
        self.act_ghost.setCheckable(True)
        self.act_ghost.setChecked(is_click_through)
        self.act_ghost.triggered.connect(on_toggle_click_through)

        self.act_top = self.menu.addAction("📌 Always on Top")
        self.act_top.setCheckable(True)
        self.act_top.setChecked(is_always_on_top)
        self.act_top.triggered.connect(on_toggle_always_on_top)

        self.menu.addSeparator()

        quit_act = self.menu.addAction("❌ Exit Pet")
        quit_act.triggered.connect(on_quit)

        self.setContextMenu(self.menu)
        self.activated.connect(self._on_tray_activated)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.menu.actions()[3].trigger()  # trigger hop

    def update_pet_name(self, new_name: str):
        self.setToolTip(f"🐾 {new_name} - Desktop Companion")
        self.menu.actions()[0].setText(f"🐾 {new_name}")
