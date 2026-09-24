"""Taskbar and Screen WorkArea Tracking for Desktop Pet.
Handles Windows taskbar detection, multi-monitor bounds, and floor calculation.
"""

from dataclasses import dataclass
from typing import Optional, Literal
from PyQt6.QtCore import QRect, QObject, pyqtSignal
from PyQt6.QtGui import QGuiApplication, QScreen


@dataclass
class TaskbarInfo:
    screen_rect: QRect
    work_area: QRect
    taskbar_rect: QRect
    position: Literal["bottom", "top", "left", "right", "hidden"]
    floor_y: int
    min_x: int
    max_x: int


class TaskbarTracker(QObject):
    """Monitors screen work area and calculates walking floor and boundaries."""

    bounds_changed = pyqtSignal(TaskbarInfo)

    def __init__(self, screen_index: int = 0):
        super().__init__()
        self.screen_index = screen_index
        self._current_info: Optional[TaskbarInfo] = None
        self._connect_screen_signals()
        self.refresh()

    def _get_target_screen(self) -> Optional[QScreen]:
        screens = QGuiApplication.screens()
        if not screens:
            return None
        if 0 <= self.screen_index < len(screens):
            return screens[self.screen_index]
        return QGuiApplication.primaryScreen()

    def _connect_screen_signals(self):
        screen = self._get_target_screen()
        if screen:
            screen.availableGeometryChanged.connect(self._on_geometry_changed)
            screen.geometryChanged.connect(self._on_geometry_changed)

    def _on_geometry_changed(self, _rect: QRect):
        new_info = self.refresh()
        if new_info:
            self.bounds_changed.emit(new_info)

    def refresh(self) -> TaskbarInfo:
        """Calculate current taskbar and walking bounds."""
        screen = self._get_target_screen()
        if not screen:
            # Fallback safe defaults (e.g. headless/test environment)
            screen_rect = QRect(0, 0, 1920, 1080)
            work_area = QRect(0, 0, 1920, 1032)
        else:
            screen_rect = screen.geometry()
            work_area = screen.availableGeometry()

        # Determine taskbar position & rect
        pos: Literal["bottom", "top", "left", "right", "hidden"] = "bottom"
        taskbar_rect = QRect()

        if work_area.bottom() < screen_rect.bottom():
            pos = "bottom"
            taskbar_rect = QRect(
                screen_rect.left(),
                work_area.bottom() + 1,
                screen_rect.width(),
                screen_rect.bottom() - work_area.bottom()
            )
            floor_y = work_area.bottom()
        elif work_area.top() > screen_rect.top():
            pos = "top"
            taskbar_rect = QRect(
                screen_rect.left(),
                screen_rect.top(),
                screen_rect.width(),
                work_area.top() - screen_rect.top()
            )
            floor_y = screen_rect.bottom() - 10
        elif work_area.left() > screen_rect.left():
            pos = "left"
            taskbar_rect = QRect(
                screen_rect.left(),
                screen_rect.top(),
                work_area.left() - screen_rect.left(),
                screen_rect.height()
            )
            floor_y = work_area.bottom()
        elif work_area.right() < screen_rect.right():
            pos = "right"
            taskbar_rect = QRect(
                work_area.right() + 1,
                screen_rect.top(),
                screen_rect.right() - work_area.right(),
                screen_rect.height()
            )
            floor_y = work_area.bottom()
        else:
            # Auto-hidden or identical
            pos = "hidden"
            floor_y = screen_rect.bottom() - 40
            taskbar_rect = QRect(screen_rect.left(), screen_rect.bottom() - 40, screen_rect.width(), 40)

        min_x = work_area.left()
        max_x = work_area.right()

        info = TaskbarInfo(
            screen_rect=screen_rect,
            work_area=work_area,
            taskbar_rect=taskbar_rect,
            position=pos,
            floor_y=floor_y,
            min_x=min_x,
            max_x=max_x,
        )
        self._current_info = info
        return info

    @property
    def current_info(self) -> TaskbarInfo:
        if self._current_info is None:
            return self.refresh()
        return self._current_info
