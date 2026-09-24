"""Unit tests for PetStateMachine, physics, autonomous AI, and micro-jumps."""

import sys
from pathlib import Path
import pytest
from PyQt6.QtCore import QRect
from PyQt6.QtWidgets import QApplication

from core.animator import SpriteAnimator
from core.state_machine import PetStateMachine
from core.taskbar import TaskbarInfo


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def state_machine(qapp):
    pet_dir = Path(__file__).resolve().parent.parent / "pets" / "default_cat"
    if not (pet_dir / "spritesheet.png").exists():
        from assets.generate_cat import generate_cat_pack
        generate_cat_pack(pet_dir)

    animator = SpriteAnimator(pet_dir, scale=2)
    fake_info = TaskbarInfo(
        screen_rect=QRect(0, 0, 1920, 1080),
        work_area=QRect(0, 0, 1920, 1032),
        taskbar_rect=QRect(0, 1032, 1920, 48),
        position="bottom",
        floor_y=1032,
        min_x=0,
        max_x=1920
    )
    return PetStateMachine(animator, fake_info)


def test_initial_state_and_floor(state_machine):
    assert state_machine.state == "idle"
    # Pet height is 64 (32 * scale 2)
    # floor_y for pet is 1032 - 64 = 968
    assert state_machine.floor_y == 968.0


def test_walk_movement_and_bounds(state_machine):
    state_machine.set_state("walk", duration=5.0)
    state_machine.direction = 1
    state_machine.x = 100.0
    initial_x = state_machine.x

    # Tick 1 second
    state_machine.tick(1.0)
    assert state_machine.x > initial_x
    assert state_machine.vx > 0


def test_micro_jump_physics(state_machine):
    state_machine.y = state_machine.floor_y
    state_machine.trigger_jump(micro=True)

    assert state_machine.state == "jump"
    assert state_machine.vy < 0  # Initial upwards velocity

    # Simulate physics over small intervals
    y_min = state_machine.y
    for _ in range(30):
        state_machine.tick(0.016)
        if state_machine.y < y_min:
            y_min = state_machine.y

    # Verify that the pet hopped upwards (y decreased by at least 2-8 pixels)
    assert y_min < state_machine.floor_y - 2.0


def test_drag_and_fall_physics(state_machine):
    # Click on the pet
    state_machine.start_drag(state_machine.x + 10, state_machine.y + 10)
    assert state_machine.state == "drag"
    assert state_machine.is_dragged is True

    # Drag pet up into mid-air (e.g. y = 300)
    state_machine.update_drag(500, 300)
    assert state_machine.y < state_machine.floor_y

    # Release in mid-air
    state_machine.end_drag()
    assert state_machine.state == "fall"
    assert state_machine.is_dragged is False

    # Simulate gravity fall until landing on floor
    for _ in range(120):  # ~2 seconds at 60 fps
        state_machine.tick(0.016)

    # Must land on floor
    assert state_machine.y == state_machine.floor_y


def test_pet_clicked_reaction(state_machine):
    num_particles_before = len(state_machine.animator.particles)
    state_machine.pet_clicked()

    # Heart particle emitted
    assert len(state_machine.animator.particles) == num_particles_before + 1
    assert state_machine.animator.particles[-1].kind == "heart"
