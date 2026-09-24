"""UI integration tests for PetWindow and Dialogs."""

import sys
from pathlib import Path
import pytest
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QApplication

from core.window import PetWindow
from ui.pet_manager import PetManagerDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def pet_window(qapp):
    base_dir = Path(__file__).resolve().parent.parent
    pets_dir = base_dir / "pets"
    active_pet_dir = pets_dir / "default_cat"

    config = {
        "active_pet": "default_cat",
        "scale": 2,
        "speed": 1.0,
        "always_on_top": True,
        "click_through": False
    }

    win = PetWindow(pets_dir, active_pet_dir, config)
    yield win
    win.close()


def test_pet_window_creation(pet_window):
    assert pet_window is not None
    assert pet_window.scale == 2
    assert pet_window.width() == 64
    # Height is sprite height (64) + PARTICLE_TOP_MARGIN (35) = 99
    assert pet_window.height() == 99
    assert pet_window.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)


def test_pet_window_scale_update(pet_window):
    pet_window.set_scale(3)
    assert pet_window.scale == 3
    assert pet_window.width() == 96
    assert pet_window.height() == 96 + 35

    # Reset back to 2
    pet_window.set_scale(2)
    assert pet_window.scale == 2


def test_pet_window_speed_update(pet_window):
    pet_window.set_speed(1.8)
    assert pet_window.speed == 1.8
    assert pet_window.state_machine.speed_multiplier == 1.8


def test_pet_window_tick_cycle(pet_window):
    # Run multiple ticks to verify smooth 60fps loop without exceptions
    for _ in range(60):
        pet_window._tick()

    assert pet_window.state_machine.x >= pet_window.state_machine.taskbar_info.min_x


def test_pet_manager_dialog(qapp, pet_window):
    dialog = PetManagerDialog(pet_window.pets_dir, pet_window.active_pet_dir)
    assert dialog.pets_list.count() >= 1

    # Verify tab navigation
    assert dialog.tabs.count() == 2
    dialog.tabs.setCurrentIndex(1)
    assert dialog.tabs.currentIndex() == 1
    dialog.close()


def test_pet_window_quit_application(qapp):
    base_dir = Path(__file__).resolve().parent.parent
    pets_dir = base_dir / "pets"
    active_pet_dir = pets_dir / "default_cat"

    config = {
        "active_pet": "default_cat",
        "scale": 2,
        "speed": 1.0,
        "always_on_top": True,
        "click_through": False
    }

    win = PetWindow(pets_dir, active_pet_dir, config)
    assert win.tick_timer.isActive() is True
    assert win.tray.isVisible() is True

    win.quit_application()

    assert win.tick_timer.isActive() is False
    assert win.tray.isVisible() is False
