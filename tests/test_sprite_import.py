"""Unit tests for custom sprite uploading and pet import validation."""

import json
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageDraw
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
def temp_custom_pet(tmp_path):
    pet_dir = tmp_path / "custom_dog"
    pet_dir.mkdir(parents=True)

    # 1. Create a dummy 2-frame 32x32 sprite sheet (64x32)
    img = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([4, 4, 28, 28], fill=(120, 80, 40, 255))
    draw.rectangle([36, 4, 60, 28], fill=(150, 100, 50, 255))
    sprite_path = pet_dir / "spritesheet.png"
    img.save(sprite_path, "PNG")

    # 2. Create pet.json
    meta = {
        "name": "Custom Dog",
        "description": "A loyal puppy friend.",
        "author": "Tester",
        "version": "1.0",
        "frame_width": 32,
        "frame_height": 32,
        "spritesheet": "spritesheet.png",
        "default_scale": 2,
        "states": {
            "idle": {"row": 0, "frames": 2, "fps": 4, "loop": True, "speed": 0.0},
            "walk": {"row": 0, "frames": 2, "fps": 6, "loop": True, "speed": 1.0}
        }
    }
    with open(pet_dir / "pet.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)

    return pet_dir


def test_import_custom_spritesheet(qapp, temp_custom_pet):
    animator = SpriteAnimator(temp_custom_pet, scale=2)

    assert animator.meta["name"] == "Custom Dog"
    assert animator.frame_width == 32
    assert animator.frame_height == 32
    assert "idle" in animator.animations
    assert "walk" in animator.animations
    assert len(animator.animations["idle"].frames) == 2


def test_import_animated_gif(qapp, tmp_path):
    pet_dir = tmp_path / "gif_pet"
    pet_dir.mkdir(parents=True)

    # Create a 3-frame animated GIF
    frames = []
    for c in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
        im = Image.new("RGBA", (32, 32), c)
        frames.append(im)

    gif_path = pet_dir / "pet.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=100, loop=0)

    # pet.json referencing the GIF
    meta = {
        "name": "Rainbow Slime",
        "frame_width": 32,
        "frame_height": 32,
        "spritesheet": "pet.gif",
        "states": {}
    }
    with open(pet_dir / "pet.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)

    animator = SpriteAnimator(pet_dir, scale=1)
    assert animator.meta["name"] == "Rainbow Slime"
    assert "idle" in animator.animations
    assert len(animator.animations["idle"].frames) == 3
