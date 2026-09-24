import json
from pathlib import Path
from typing import Callable, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup, QFont, QIcon
from PyQt6.QtWidgets import QMenu, QWidget


class PetContextMenu(QMenu):
    """Custom-styled dark mode right-click context menu for the desktop pet."""

    def __init__(
        self,
        parent: QWidget,
        pet_name: str,
        current_scale: int,
        current_speed: float,
        is_always_on_top: bool,
        is_click_through: bool,
        on_action: Callable[[str], None],
        on_scale_change: Callable[[int], None],
        on_speed_change: Callable[[float], None],
        on_toggle_always_on_top: Callable[[bool], None],
        on_toggle_click_through: Callable[[bool], None],
        on_open_manager: Callable[[], None],
        on_quit: Callable[[], None],
        pets_dir: Optional[Path] = None,
        active_pet_dir: Optional[Path] = None,
        on_switch_pet: Optional[Callable[[Path], None]] = None
    ):
        super().__init__(parent)
        self.setStyleSheet("""
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
                padding: 6px 24px 6px 28px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #3b82f6;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #2e3440;
                margin: 4px 8px;
            }
        """)

        # Title header
        title_action = self.addAction(f"🐾 {pet_name}")
        title_font = title_action.font()
        title_font.setBold(True)
        title_action.setFont(title_font)
        title_action.setEnabled(False)

        # Switch Pet Submenu
        if pets_dir and pets_dir.exists() and on_switch_pet:
            switch_menu = self.addMenu("🔄 Switch Pet")
            switch_menu.setStyleSheet(self.styleSheet())
            pet_group = QActionGroup(self)
            pet_group.setExclusive(True)

            for p in sorted(pets_dir.iterdir()):
                if p.is_dir() and (p / "pet.json").exists():
                    try:
                        with open(p / "pet.json", "r", encoding="utf-8") as f:
                            p_meta = json.load(f)
                        p_name = p_meta.get("name", p.name)
                        p_action = switch_menu.addAction(f"🐾 {p_name}")
                        p_action.setCheckable(True)
                        if active_pet_dir and p.resolve() == active_pet_dir.resolve():
                            p_action.setChecked(True)
                        p_action.triggered.connect(lambda checked, path=p: on_switch_pet(path))
                        pet_group.addAction(p_action)
                    except Exception:
                        pass

        self.addSeparator()

        # Actions Submenu
        actions_menu = self.addMenu("🎭 Actions")
        actions_menu.setStyleSheet(self.styleSheet())

        act_walk = actions_menu.addAction("🚶 Walk along taskbar")
        act_walk.triggered.connect(lambda: on_action("walk"))

        act_run = actions_menu.addAction("⚡ Run / Zoomies")
        act_run.triggered.connect(lambda: on_action("run"))

        act_jump = actions_menu.addAction("🦘 Hop / Jump")
        act_jump.triggered.connect(lambda: on_action("jump"))

        act_sleep = actions_menu.addAction("💤 Sleep (Zzz)")
        act_sleep.triggered.connect(lambda: on_action("sleep"))

        act_groom = actions_menu.addAction("🐾 Groom / Snack")
        act_groom.triggered.connect(lambda: on_action("groom"))

        act_idle = actions_menu.addAction("🧘 Sit Calmly")
        act_idle.triggered.connect(lambda: on_action("idle"))

        # Scale Submenu
        scale_menu = self.addMenu("🔍 Size / Scale")
        scale_menu.setStyleSheet(self.styleSheet())
        scale_group = QActionGroup(self)
        scale_group.setExclusive(True)

        for s, label in [(1, "1x (32px - Tiny)"), (2, "2x (64px - Normal)"), (3, "3x (96px - Large)"), (4, "4x (128px - Giant)")]:
            action = scale_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(s == current_scale)
            action.triggered.connect(lambda checked, sc=s: on_scale_change(sc))
            scale_group.addAction(action)

        # Speed Submenu
        speed_menu = self.addMenu("⚡ Speed")
        speed_menu.setStyleSheet(self.styleSheet())
        speed_group = QActionGroup(self)
        speed_group.setExclusive(True)

        for spd, label in [(0.5, "Relaxed (0.5x)"), (1.0, "Normal (1.0x)"), (1.8, "Fast / Zoomies (1.8x)")]:
            action = speed_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(abs(spd - current_speed) < 0.1)
            action.triggered.connect(lambda checked, s=spd: on_speed_change(s))
            speed_group.addAction(action)

        self.addSeparator()

        # Options
        top_action = self.addAction("📌 Always on Top")
        top_action.setCheckable(True)
        top_action.setChecked(is_always_on_top)
        top_action.triggered.connect(on_toggle_always_on_top)

        ghost_action = self.addAction("👻 Click-Through Mode")
        ghost_action.setCheckable(True)
        ghost_action.setChecked(is_click_through)
        ghost_action.triggered.connect(on_toggle_click_through)

        self.addSeparator()

        # Sprite Manager
        manager_action = self.addAction("🎨 Sprite & Pet Manager...")
        manager_action.triggered.connect(on_open_manager)

        self.addSeparator()

        # Quit
        quit_action = self.addAction("❌ Quit Pet")
        quit_action.triggered.connect(on_quit)
