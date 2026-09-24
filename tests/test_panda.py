"""Unit tests for Bao the Panda pet profile, spritesheet slicing, and switching."""

import json
from pathlib import Path
import pytest
from PyQt6.QtWidgets import QApplication

from core.animator import SpriteAnimator


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        import sys
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def panda_dir():
    target = Path(__file__).resolve().parent.parent / "pets" / "default_panda"
    if not (target / "spritesheet.png").exists():
        from assets.generate_panda import generate_panda_pack
        generate_panda_pack(target)
    return target


def test_panda_pet_json_validity(panda_dir):
    config_file = panda_dir / "pet.json"
    assert config_file.exists()

    with open(config_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    assert meta["name"] == "Bao the Panda"
    assert meta["frame_width"] == 32
    assert meta["frame_height"] == 32
    assert meta["spritesheet"] == "spritesheet.png"

    required_states = ["idle", "walk", "run", "jump", "sleep", "groom", "drag", "fall"]
    for state in required_states:
        assert state in meta["states"], f"Missing {state} state"
        assert meta["states"][state]["frames"] >= 2


def test_panda_animator_load_and_scaling(qapp, panda_dir):
    animator = SpriteAnimator(panda_dir, scale=2)

    assert animator.meta["name"] == "Bao the Panda"
    assert animator.current_width == 64
    assert animator.current_height == 64

    # Check that all states load scaled frames
    for s in ["idle", "walk", "run", "jump", "sleep", "groom", "drag", "fall"]:
        anim = animator.animations[s]
        assert len(anim.frames) > 0
        assert len(anim.flipped_frames) == len(anim.frames)
        assert anim.frames[0].width() == 64
        assert anim.frames[0].height() == 64

    # Test scaling to 3x
    animator.set_scale(3)
    assert animator.current_width == 96
    assert animator.current_height == 96


def test_panda_bamboo_groom_state(qapp, panda_dir):
    animator = SpriteAnimator(panda_dir, scale=2)
    animator.set_state("groom")
    assert animator.current_state == "groom"

    # Verify frame advancement during eating bamboo
    animator.update(0.3)
    assert animator.frame_index >= 1


def test_switch_between_cat_and_panda(qapp):
    pets_dir = Path(__file__).resolve().parent.parent / "pets"
    cat_dir = pets_dir / "default_cat"
    panda_dir = pets_dir / "default_panda"

    animator = SpriteAnimator(cat_dir, scale=2)
    assert animator.meta["name"] == "Neko the Cat"

    animator.load_pet(panda_dir)
    assert animator.meta["name"] == "Bao the Panda"

    animator.load_pet(cat_dir)
    assert animator.meta["name"] == "Neko the Cat"
