"""Main Transparent Desktop Pet Window.
Provides frameless ARGB rendering, mouse interaction (dragging, petting, context menu),
and smooth 60 FPS animation loop.
"""

import time
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QPoint, QRect, Qt, QTimer
from PyQt6.QtGui import QMouseEvent, QPainter
from PyQt6.QtWidgets import QWidget, QApplication

from core.animator import SpriteAnimator
from core.state_machine import PetStateMachine
from core.taskbar import TaskbarInfo, TaskbarTracker
from ui.context_menu import PetContextMenu
from ui.pet_manager import PetManagerDialog
from ui.tray import PetTrayIcon


class PetWindow(QWidget):
    """Transparent overlay window hosting the animated desktop pet."""

    PARTICLE_TOP_MARGIN = 35  # Extra room above pet for floating hearts and Zzz

    def __init__(self, pets_dir: Path, active_pet_dir: Path, config: dict):
        super().__init__()
        self.pets_dir = Path(pets_dir)
        self.active_pet_dir = Path(active_pet_dir)
        self.config = config

        self.scale = config.get("scale", 2)
        self.speed = config.get("speed", 1.0)
        self.always_on_top = config.get("always_on_top", True)
        self.click_through = config.get("click_through", False)

        # 1. Initialize tracker, animator, state machine
        self.tracker = TaskbarTracker()
        self.animator = SpriteAnimator(self.active_pet_dir, scale=self.scale)
        self.state_machine = PetStateMachine(self.animator, self.tracker.current_info)
        self.state_machine.speed_multiplier = self.speed

        # 2. Window setup
        self._configure_window_flags()
        self._update_window_size()

        # 3. Connect signals
        self.tracker.bounds_changed.connect(self._on_bounds_changed)
        self.state_machine.position_changed.connect(self._on_position_changed)

        # 4. Drag & click interaction state
        self._mouse_press_pos: Optional[QPoint] = None
        self._mouse_press_time: float = 0.0
        self._is_dragging_mouse: bool = False

        # 5. Tray icon setup
        pet_name = self.animator.meta.get("name", "Neko")
        self.tray = PetTrayIcon(
            parent=self,
            pet_name=pet_name,
            on_open_manager=self.open_pet_manager,
            on_trigger_action=self.state_machine.force_action,
            on_toggle_click_through=self.set_click_through,
            on_toggle_always_on_top=self.set_always_on_top,
            is_click_through=self.click_through,
            is_always_on_top=self.always_on_top,
            on_quit=self.quit_application
        )
        self.tray.show()

        # 6. Main 60 FPS tick timer
        self.last_tick_time = time.perf_counter()
        self.tick_timer = QTimer(self)
        self.tick_timer.timeout.connect(self._tick)
        self.tick_timer.start(16)  # ~60 FPS

        # Initial placement on taskbar
        self.state_machine.y = self.state_machine.floor_y
        self._on_position_changed(self.state_machine.x, self.state_machine.y)

    def _configure_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.SubWindow
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        if self.click_through:
            flags |= Qt.WindowType.WindowTransparentForInput

        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)

    def _update_window_size(self):
        w = self.animator.current_width
        h = self.animator.current_height + self.PARTICLE_TOP_MARGIN
        self.setFixedSize(w, h)

    def _on_bounds_changed(self, info: TaskbarInfo):
        self.state_machine.update_taskbar_info(info)

    def _on_position_changed(self, x: float, y: float):
        # Shift Y up by PARTICLE_TOP_MARGIN so the pet's feet sit precisely on floor_y
        screen_x = int(round(x))
        screen_y = int(round(y - self.PARTICLE_TOP_MARGIN))
        self.move(screen_x, screen_y)

    def _tick(self):
        now = time.perf_counter()
        dt = min(0.05, now - self.last_tick_time)
        self.last_tick_time = now

        self.state_machine.tick(dt)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Shift painter down so particles can float above the pet
        painter.save()
        painter.translate(0, self.PARTICLE_TOP_MARGIN)
        self.animator.render(painter)
        painter.restore()

    # ----------------------------------------------------
    # Mouse Interactions
    # ----------------------------------------------------
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_press_pos = event.globalPosition().toPoint()
            self._mouse_press_time = time.perf_counter()
            self._is_dragging_mouse = False
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._mouse_press_pos is not None:
            curr_pos = event.globalPosition().toPoint()
            dist = (curr_pos - self._mouse_press_pos).manhattanLength()
            if dist > 6 and not self._is_dragging_mouse:
                self._is_dragging_mouse = True
                self.state_machine.start_drag(curr_pos.x(), curr_pos.y())

            if self._is_dragging_mouse:
                self.state_machine.update_drag(curr_pos.x(), curr_pos.y())

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            press_duration = time.perf_counter() - self._mouse_press_time
            if not self._is_dragging_mouse and press_duration < 0.35:
                # Petting / Clicked!
                self.state_machine.pet_clicked()
            elif self._is_dragging_mouse:
                self.state_machine.end_drag()

            self._mouse_press_pos = None
            self._is_dragging_mouse = False

    def _show_context_menu(self, global_pos: QPoint):
        menu = PetContextMenu(
            parent=self,
            pet_name=self.animator.meta.get("name", "Neko"),
            current_scale=self.scale,
            current_speed=self.speed,
            is_always_on_top=self.always_on_top,
            is_click_through=self.click_through,
            on_action=self.state_machine.force_action,
            on_scale_change=self.set_scale,
            on_speed_change=self.set_speed,
            on_toggle_always_on_top=self.set_always_on_top,
            on_toggle_click_through=self.set_click_through,
            on_open_manager=self.open_pet_manager,
            on_quit=self.quit_application
        )
        menu.exec(global_pos)

    # ----------------------------------------------------
    # Settings & User Controls
    # ----------------------------------------------------
    def set_scale(self, new_scale: int):
        self.scale = new_scale
        self.animator.set_scale(new_scale)
        self._update_window_size()
        self.state_machine.y = self.state_machine.floor_y
        self.state_machine.clamp_x()
        self.update()

    def set_speed(self, new_speed: float):
        self.speed = new_speed
        self.state_machine.speed_multiplier = new_speed

    def set_always_on_top(self, enable: bool):
        self.always_on_top = enable
        self._configure_window_flags()
        self.show()

    def set_click_through(self, enable: bool):
        self.click_through = enable
        self._configure_window_flags()
        self.show()

    def open_pet_manager(self):
        dialog = PetManagerDialog(self.pets_dir, self.active_pet_dir, self)
        dialog.pet_selected.connect(self.switch_pet)
        dialog.exec()

    def switch_pet(self, pet_dir: Path):
        self.active_pet_dir = Path(pet_dir)
        self.animator.load_pet(self.active_pet_dir)
        self._update_window_size()
        self.state_machine.y = self.state_machine.floor_y
        self.state_machine.clamp_x()

        new_name = self.animator.meta.get("name", "Neko")
        self.tray.update_pet_name(new_name)
        self.update()

    def quit_application(self):
        """Properly shuts down timers, hides tray icon, and terminates the application process."""
        self.tick_timer.stop()
        if hasattr(self, "tray") and self.tray:
            self.tray.hide()
            self.tray.deleteLater()
        self.close()
        app = QApplication.instance()
        if app:
            app.quit()

    def closeEvent(self, event):
        """Handle window close event cleanly."""
        self.tick_timer.stop()
        if hasattr(self, "tray") and self.tray:
            self.tray.hide()
            self.tray.deleteLater()
        event.accept()
        app = QApplication.instance()
        if app:
            app.quit()
