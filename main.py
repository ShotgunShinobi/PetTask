"""Main Entry Point for Desktop Pet Application.
Loads configuration, initializes Qt application, and starts the pet.
"""

import atexit
import json
import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from core.window import PetWindow

CONFIG_FILE = Path(__file__).resolve().parent / "config.json"
BASE_DIR = Path(__file__).resolve().parent
PETS_DIR = BASE_DIR / "pets"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
    return {
        "active_pet": "default_cat",
        "scale": 2,
        "speed": 1.0,
        "always_on_top": True,
        "click_through": False
    }


def save_config(window: PetWindow):
    try:
        cfg = {
            "active_pet": window.active_pet_dir.name,
            "scale": window.scale,
            "speed": window.speed,
            "always_on_top": window.always_on_top,
            "click_through": window.click_through
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"Warning: Failed to save config: {e}")


def main():
    # Enable High DPI rendering
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName("DesktopPet")
    app.setQuitOnLastWindowClosed(False)

    config = load_config()
    active_pet_name = config.get("active_pet", "default_cat")
    active_pet_dir = PETS_DIR / active_pet_name

    if not active_pet_dir.exists():
        active_pet_dir = PETS_DIR / "default_cat"

    # Make sure default cat is generated if not exists
    if not (active_pet_dir / "spritesheet.png").exists():
        from assets.generate_cat import generate_cat_pack
        generate_cat_pack(active_pet_dir)

    window = PetWindow(
        pets_dir=PETS_DIR,
        active_pet_dir=active_pet_dir,
        config=config
    )
    window.show()

    # Save settings on clean exit
    atexit.register(lambda: save_config(window))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
