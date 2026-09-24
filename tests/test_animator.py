"""Unit tests for SpriteAnimator, frame slicing, scaling, and particles."""

import sys
from pathlib import Path
import pytest
from PyQt6.QtWidgets import QApplication

from core.animator import SpriteAnimator


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def default_cat_dir():
    target = Path(__file__).resolve().parent.parent / "pets" / "default_cat"
    if not (target / "spritesheet.png").exists():
        from assets.generate_cat import generate_cat_pack
        generate_cat_pack(target)
    return target


def test_animator_load_default_cat(qapp, default_cat_dir):
    animator = SpriteAnimator(default_cat_dir, scale=2)

    assert animator.meta["name"] == "Neko the Cat"
    assert animator.frame_width == 32
    assert animator.frame_height == 32
    assert animator.scale == 2
    assert animator.current_width == 64
    assert animator.current_height == 64

    # Verify all 8 states loaded
    expected_states = ["idle", "walk", "run", "jump", "sleep", "groom", "drag", "fall"]
    for s in expected_states:
        assert s in animator.animations, f"Missing state {s}"
        anim = animator.animations[s]
        assert len(anim.frames) > 0
        assert len(anim.flipped_frames) == len(anim.frames)
        # Verify frame dimensions match scaled size
        assert anim.frames[0].width() == 64
        assert anim.frames[0].height() == 64


def test_animator_scale_change(qapp, default_cat_dir):
    animator = SpriteAnimator(default_cat_dir, scale=1)
    assert animator.current_width == 32
    assert animator.current_height == 32

    animator.set_scale(3)
    assert animator.scale == 3
    assert animator.current_width == 96
    assert animator.current_height == 96


def test_animator_frame_advancement(qapp, default_cat_dir):
    animator = SpriteAnimator(default_cat_dir, scale=2)
    animator.set_state("walk")
    assert animator.frame_index == 0

    # Advance enough time to trigger next frame
    fps = animator.animations["walk"].fps
    frame_duration = 1.0 / fps
    animator.update(frame_duration + 0.01)

    assert animator.frame_index == 1


def test_particles_emission(qapp, default_cat_dir):
    animator = SpriteAnimator(default_cat_dir, scale=2)
    assert len(animator.particles) == 0

    animator.emit_heart(20, 20)
    assert len(animator.particles) == 1
    assert animator.particles[0].kind == "heart"

    animator.emit_zzz(20, 20)
    assert len(animator.particles) == 2

    animator.emit_dust(20, 20)
    assert len(animator.particles) == 5  # 2 + 3 dust particles

    # Updating with time decays particles
    animator.update(3.0)  # 3 seconds should decay dust
    dust_remaining = [p for p in animator.particles if p.kind == "dust"]
    assert len(dust_remaining) == 0
