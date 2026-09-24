"""Unit tests for TaskbarTracker and bounds calculations."""

from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication
import pytest
import sys

from core.taskbar import TaskbarTracker, TaskbarInfo


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_taskbar_tracker_initialization(qapp):
    tracker = TaskbarTracker()
    info = tracker.current_info

    assert isinstance(info, TaskbarInfo)
    assert info.screen_rect.width() > 0
    assert info.screen_rect.height() > 0
    assert info.work_area.width() > 0
    assert info.work_area.height() > 0
    assert info.position in ("bottom", "top", "left", "right", "hidden")
    assert info.min_x <= info.max_x
    assert info.floor_y > 0


def test_taskbar_info_math():
    # Test floor math for bottom taskbar
    screen = QRect(0, 0, 1920, 1080)
    work = QRect(0, 0, 1920, 1032)  # 48px bottom taskbar

    # Bottom taskbar
    assert work.bottom() < screen.bottom()
    floor_y = work.bottom()
    assert floor_y == 1031
