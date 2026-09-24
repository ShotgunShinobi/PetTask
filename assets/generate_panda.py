"""Procedural Pixel Art Panda Generator for Desktop Pet.
Generates an adorable 32x32 animated Giant Panda ("Bao") spritesheet with 8 complete states:
idle, walk, run, jump, sleep, groom (eating bamboo), drag, fall.
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

# Color Palette for Giant Panda
OUTLINE = (20, 22, 26, 255)         # Very dark charcoal outline
BLACK_FUR = (35, 38, 44, 255)       # Main black fur (ears, patches, arms, legs)
BLACK_SHADOW = (22, 24, 28, 255)    # Shadow on black fur
WHITE_FUR = (252, 252, 254, 255)    # Clean white body & face
WHITE_SHADOW = (225, 230, 238, 255) # Soft bluish-gray shading on white fur
PINK = (255, 170, 180, 255)         # Cute tongue / nose highlight
EYE_WHITE = (255, 255, 255, 255)    # Eye shine
BAMBOO_GREEN = (34, 197, 94, 255)   # Fresh bamboo green
BAMBOO_DARK = (21, 128, 61, 255)    # Bamboo shadow
TRANSPARENT = (0, 0, 0, 0)

FRAME_SIZE = 32
ROWS = 8
COLS = 4


def draw_pixel(draw: ImageDraw.ImageDraw, x: int, y: int, color, ox: int = 0, oy: int = 0):
    px, py = ox + x, oy + y
    if 0 <= px < FRAME_SIZE * COLS and 0 <= py < FRAME_SIZE * ROWS:
        draw.point((px, py), fill=color)


def draw_rect(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, color, ox: int = 0, oy: int = 0):
    for x in range(x1, x2 + 1):
        for y in range(y1, y2 + 1):
            draw_pixel(draw, x, y, color, ox, oy)


def create_panda_frame(state: str, frame_idx: int, ox: int, oy: int, draw: ImageDraw.ImageDraw):
    """Draw a single 32x32 frame of the panda at offset (ox, oy)."""

    if state == "idle":
        # Sitting chubby panda. Breathing chest, ear twitch, blink on frame 3.
        breathe = 1 if frame_idx in (1, 2) else 0
        blink = (frame_idx == 3)
        ear_twitch = 1 if frame_idx == 1 else 0

        # Body (chubby white tummy with black legs)
        draw_rect(draw, 9, 17 - breathe, 23, 27, WHITE_FUR, ox, oy)
        draw_rect(draw, 10, 25, 22, 27, WHITE_SHADOW, ox, oy)
        draw_rect(draw, 8, 17 - breathe, 8, 27, OUTLINE, ox, oy)
        draw_rect(draw, 24, 17 - breathe, 24, 27, OUTLINE, ox, oy)
        draw_rect(draw, 9, 28, 23, 28, OUTLINE, ox, oy)

        # Black shoulders / chest band
        draw_rect(draw, 9, 17 - breathe, 23, 19 - breathe, BLACK_FUR, ox, oy)

        # Head (round white chubby cheeks)
        draw_rect(draw, 7, 8 - breathe, 21, 17 - breathe, WHITE_FUR, ox, oy)
        draw_rect(draw, 6, 9 - breathe, 6, 16 - breathe, OUTLINE, ox, oy)
        draw_rect(draw, 22, 9 - breathe, 22, 16 - breathe, OUTLINE, ox, oy)
        draw_rect(draw, 7, 7 - breathe, 21, 7 - breathe, OUTLINE, ox, oy)
        draw_rect(draw, 8, 17 - breathe, 20, 17 - breathe, WHITE_SHADOW, ox, oy)

        # Ears (round black)
        # Left ear
        draw_rect(draw, 6, 4 - breathe - ear_twitch, 10, 7 - breathe, BLACK_FUR, ox, oy)
        draw_pixel(draw, 7, 3 - breathe - ear_twitch, OUTLINE, ox, oy)
        draw_pixel(draw, 8, 3 - breathe - ear_twitch, OUTLINE, ox, oy)
        draw_pixel(draw, 9, 3 - breathe - ear_twitch, OUTLINE, ox, oy)
        # Right ear
        draw_rect(draw, 18, 4 - breathe, 22, 7 - breathe, BLACK_FUR, ox, oy)
        draw_pixel(draw, 19, 3 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 20, 3 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 21, 3 - breathe, OUTLINE, ox, oy)

        # Panda Eye Patches (classic tilted oval dark patches)
        draw_rect(draw, 8, 10 - breathe, 11, 13 - breathe, BLACK_FUR, ox, oy)
        draw_rect(draw, 17, 10 - breathe, 20, 13 - breathe, BLACK_FUR, ox, oy)

        if blink:
            draw_rect(draw, 9, 11 - breathe, 11, 11 - breathe, OUTLINE, ox, oy)
            draw_rect(draw, 17, 11 - breathe, 19, 11 - breathe, OUTLINE, ox, oy)
        else:
            # Cute eye shine inside black patch
            draw_pixel(draw, 10, 11 - breathe, EYE_WHITE, ox, oy)
            draw_pixel(draw, 18, 11 - breathe, EYE_WHITE, ox, oy)

        # Muzzle & Nose
        draw_pixel(draw, 14, 13 - breathe, OUTLINE, ox, oy)  # Nose
        draw_pixel(draw, 14, 14 - breathe, OUTLINE, ox, oy)  # Mouth

        # Chubby front paws resting on tummy
        draw_rect(draw, 9, 20 - breathe, 12, 23 - breathe, BLACK_FUR, ox, oy)
        draw_rect(draw, 16, 20 - breathe, 19, 23 - breathe, BLACK_FUR, ox, oy)

        # Back feet
        draw_rect(draw, 9, 26, 12, 27, BLACK_FUR, ox, oy)
        draw_rect(draw, 20, 26, 23, 27, BLACK_FUR, ox, oy)

    elif state == "walk":
        # 4-frame adorable waddling walk cycle
        leg_offsets = [
            (0, 0, 0, 0),
            (-1, 1, 1, -1),
            (0, 0, 0, 0),
            (1, -1, -1, 1)
        ][frame_idx]
        bob = 1 if frame_idx in (1, 3) else 0

        # Body (horizontal chubby oval)
        draw_rect(draw, 7, 14 - bob, 24, 23 - bob, WHITE_FUR, ox, oy)
        draw_rect(draw, 6, 14 - bob, 6, 23 - bob, OUTLINE, ox, oy)
        draw_rect(draw, 25, 14 - bob, 25, 23 - bob, OUTLINE, ox, oy)
        draw_rect(draw, 7, 13 - bob, 24, 13 - bob, OUTLINE, ox, oy)

        # Black shoulder band
        draw_rect(draw, 15, 14 - bob, 20, 23 - bob, BLACK_FUR, ox, oy)

        # Head (forward facing right)
        draw_rect(draw, 17, 8 - bob, 28, 18 - bob, WHITE_FUR, ox, oy)
        draw_rect(draw, 16, 8 - bob, 16, 18 - bob, OUTLINE, ox, oy)
        draw_rect(draw, 29, 8 - bob, 29, 18 - bob, OUTLINE, ox, oy)
        draw_rect(draw, 17, 7 - bob, 28, 7 - bob, OUTLINE, ox, oy)

        # Ears
        draw_rect(draw, 17, 4 - bob, 21, 7 - bob, BLACK_FUR, ox, oy)
        draw_rect(draw, 24, 4 - bob, 28, 7 - bob, BLACK_FUR, ox, oy)

        # Eye patch & eye
        draw_rect(draw, 22, 10 - bob, 26, 13 - bob, BLACK_FUR, ox, oy)
        draw_pixel(draw, 24, 11 - bob, EYE_WHITE, ox, oy)

        # Muzzle & nose
        draw_pixel(draw, 28, 13 - bob, OUTLINE, ox, oy)
        draw_pixel(draw, 27, 14 - bob, OUTLINE, ox, oy)

        # Legs (black chubby waddling limbs)
        fl, fr, bl, br = leg_offsets
        # Back legs
        draw_rect(draw, 8 + bl, 23, 11 + bl, 27, BLACK_FUR, ox, oy)
        draw_rect(draw, 12 + br, 23, 15 + br, 27, BLACK_SHADOW, ox, oy)
        # Front legs
        draw_rect(draw, 18 + fl, 23, 21 + fl, 27, BLACK_FUR, ox, oy)
        draw_rect(draw, 22 + fr, 23, 25 + fr, 27, BLACK_SHADOW, ox, oy)

        # Little round tail
        draw_rect(draw, 5, 16 - bob, 6, 18 - bob, BLACK_FUR, ox, oy)

    elif state == "run":
        # 4 frame energetic panda gallop
        stretch = [0, 2, 1, -1][frame_idx]
        y_lift = [0, -2, -3, -1][frame_idx]

        # Stretched chubby body
        draw_rect(draw, 6 - stretch, 15 + y_lift, 24 + stretch, 22 + y_lift, WHITE_FUR, ox, oy)
        draw_rect(draw, 15, 15 + y_lift, 21, 22 + y_lift, BLACK_FUR, ox, oy)  # Shoulder band
        draw_rect(draw, 6 - stretch, 14 + y_lift, 24 + stretch, 14 + y_lift, OUTLINE, ox, oy)

        # Head forward
        draw_rect(draw, 21 + stretch, 10 + y_lift, 30 + stretch, 19 + y_lift, WHITE_FUR, ox, oy)
        draw_rect(draw, 22 + stretch, 6 + y_lift, 25 + stretch, 9 + y_lift, BLACK_FUR, ox, oy)  # Ear
        draw_rect(draw, 27 + stretch, 6 + y_lift, 30 + stretch, 9 + y_lift, BLACK_FUR, ox, oy)  # Ear

        # Eye patch
        draw_rect(draw, 25 + stretch, 12 + y_lift, 29 + stretch, 15 + y_lift, BLACK_FUR, ox, oy)
        draw_pixel(draw, 27 + stretch, 13 + y_lift, EYE_WHITE, ox, oy)
        draw_pixel(draw, 30 + stretch, 15 + y_lift, OUTLINE, ox, oy)

        # Legs bounding
        if frame_idx in (1, 2):  # Mid-air roll
            draw_rect(draw, 3 - stretch, 18 + y_lift, 6 - stretch, 21 + y_lift, BLACK_FUR, ox, oy)
            draw_rect(draw, 26 + stretch, 20 + y_lift, 30 + stretch, 23 + y_lift, BLACK_FUR, ox, oy)
        else:
            draw_rect(draw, 8, 22 + y_lift, 12, 26 + y_lift, BLACK_FUR, ox, oy)
            draw_rect(draw, 21, 22 + y_lift, 25, 26 + y_lift, BLACK_FUR, ox, oy)

        # Tail
        draw_rect(draw, 3 - stretch, 17 + y_lift, 5 - stretch, 19 + y_lift, BLACK_FUR, ox, oy)

    elif state == "jump":
        # 3 frames: 0=crouch bounce, 1=leap with paws up, 2=landing squish
        if frame_idx == 0:  # Crouch
            draw_rect(draw, 7, 19, 25, 26, WHITE_FUR, ox, oy)
            draw_rect(draw, 14, 19, 20, 26, BLACK_FUR, ox, oy)
            draw_rect(draw, 16, 12, 28, 20, WHITE_FUR, ox, oy)
            draw_rect(draw, 19, 8, 22, 11, BLACK_FUR, ox, oy)
            draw_rect(draw, 24, 8, 27, 11, BLACK_FUR, ox, oy)
            draw_rect(draw, 22, 13, 26, 16, BLACK_FUR, ox, oy)
            draw_pixel(draw, 24, 14, EYE_WHITE, ox, oy)
            draw_rect(draw, 9, 25, 13, 27, BLACK_FUR, ox, oy)
            draw_rect(draw, 20, 25, 24, 27, BLACK_FUR, ox, oy)
        elif frame_idx == 1:  # Leap up in air
            draw_rect(draw, 9, 7, 23, 17, WHITE_FUR, ox, oy)
            draw_rect(draw, 13, 7, 19, 17, BLACK_FUR, ox, oy)
            draw_rect(draw, 14, 2, 26, 10, WHITE_FUR, ox, oy)
            draw_rect(draw, 16, 0, 19, 2, BLACK_FUR, ox, oy)
            draw_rect(draw, 22, 0, 25, 2, BLACK_FUR, ox, oy)
            draw_rect(draw, 20, 4, 24, 7, BLACK_FUR, ox, oy)
            draw_pixel(draw, 22, 5, EYE_WHITE, ox, oy)
            # Chubby outstretched paws
            draw_rect(draw, 6, 15, 9, 20, BLACK_FUR, ox, oy)
            draw_rect(draw, 23, 10, 27, 14, BLACK_FUR, ox, oy)
        else:  # Landing squish
            draw_rect(draw, 6, 17, 26, 26, WHITE_FUR, ox, oy)
            draw_rect(draw, 13, 17, 20, 26, BLACK_FUR, ox, oy)
            draw_rect(draw, 16, 11, 28, 19, WHITE_FUR, ox, oy)
            draw_rect(draw, 18, 7, 21, 10, BLACK_FUR, ox, oy)
            draw_rect(draw, 24, 7, 27, 10, BLACK_FUR, ox, oy)
            draw_rect(draw, 22, 13, 26, 16, BLACK_FUR, ox, oy)
            draw_pixel(draw, 24, 14, EYE_WHITE, ox, oy)
            draw_rect(draw, 8, 25, 13, 27, BLACK_FUR, ox, oy)
            draw_rect(draw, 21, 25, 26, 27, BLACK_FUR, ox, oy)

    elif state == "sleep":
        # Sleeping round panda on tummy with breathing animation
        breathe = 1 if frame_idx in (1, 2) else 0
        draw_rect(draw, 6, 17 - breathe, 26, 27, WHITE_FUR, ox, oy)
        draw_rect(draw, 13, 17 - breathe, 20, 27, BLACK_FUR, ox, oy)  # Shoulder band
        draw_rect(draw, 5, 18 - breathe, 14, 27, WHITE_FUR, ox, oy)   # Head resting down
        draw_rect(draw, 5, 14 - breathe, 9, 17 - breathe, BLACK_FUR, ox, oy) # Ear flat

        # Closed curved cute eye inside black patch
        draw_rect(draw, 7, 20 - breathe, 11, 23 - breathe, BLACK_FUR, ox, oy)
        draw_pixel(draw, 8, 22 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 9, 23 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 10, 22 - breathe, OUTLINE, ox, oy)

        # Paws tucked in comfortably
        draw_rect(draw, 6, 25, 10, 27, BLACK_FUR, ox, oy)
        draw_rect(draw, 22, 25, 26, 27, BLACK_FUR, ox, oy)
        # Tail
        draw_rect(draw, 25, 20 - breathe, 27, 22 - breathe, BLACK_FUR, ox, oy)

    elif state == "groom":
        # Sitting upright happily eating a fresh green bamboo stalk!
        bamboo_bite = [0, 1, 2, 1][frame_idx]

        # Chubby body
        draw_rect(draw, 9, 16, 23, 27, WHITE_FUR, ox, oy)
        draw_rect(draw, 9, 16, 23, 19, BLACK_FUR, ox, oy)
        draw_rect(draw, 7, 8, 21, 16, WHITE_FUR, ox, oy)

        # Ears
        draw_rect(draw, 6, 4, 10, 7, BLACK_FUR, ox, oy)
        draw_rect(draw, 18, 4, 22, 7, BLACK_FUR, ox, oy)

        # Eye patches with happy closed smiling eyes (^)
        draw_rect(draw, 8, 10, 11, 13, BLACK_FUR, ox, oy)
        draw_rect(draw, 17, 10, 20, 13, BLACK_FUR, ox, oy)
        draw_pixel(draw, 9, 11, EYE_WHITE, ox, oy)
        draw_pixel(draw, 10, 10, EYE_WHITE, ox, oy)
        draw_pixel(draw, 18, 10, EYE_WHITE, ox, oy)
        draw_pixel(draw, 19, 11, EYE_WHITE, ox, oy)

        # Nose & happy mouth
        draw_pixel(draw, 14, 13, OUTLINE, ox, oy)
        draw_pixel(draw, 14, 14, PINK, ox, oy)

        # Green Bamboo Stalk held in paws!
        # Bamboo stem
        draw_rect(draw, 13, 11 + bamboo_bite, 15, 24, BAMBOO_GREEN, ox, oy)
        draw_rect(draw, 13, 17, 15, 17, BAMBOO_DARK, ox, oy)  # Bamboo joint
        # Bamboo leaves
        draw_pixel(draw, 12, 10 + bamboo_bite, BAMBOO_GREEN, ox, oy)
        draw_pixel(draw, 11, 9 + bamboo_bite, BAMBOO_DARK, ox, oy)
        draw_pixel(draw, 16, 12 + bamboo_bite, BAMBOO_GREEN, ox, oy)
        draw_pixel(draw, 17, 11 + bamboo_bite, BAMBOO_DARK, ox, oy)

        # Paws holding the bamboo
        draw_rect(draw, 10, 18, 13, 21, BLACK_FUR, ox, oy)
        draw_rect(draw, 15, 18, 18, 21, BLACK_FUR, ox, oy)

        # Back feet
        draw_rect(draw, 8, 25, 12, 27, BLACK_FUR, ox, oy)
        draw_rect(draw, 20, 25, 24, 27, BLACK_FUR, ox, oy)

    elif state == "drag":
        # Picked up by the scruff! Dangling chubby paws, surprised eyes
        blink = (frame_idx == 1)
        draw_rect(draw, 10, 10, 22, 22, WHITE_FUR, ox, oy)
        draw_rect(draw, 10, 10, 22, 14, BLACK_FUR, ox, oy)  # Shoulder band
        draw_rect(draw, 9, 3, 23, 11, WHITE_FUR, ox, oy)

        # Ears
        draw_rect(draw, 8, 0, 11, 3, BLACK_FUR, ox, oy)
        draw_rect(draw, 21, 0, 24, 3, BLACK_FUR, ox, oy)

        # Big surprised eye patches
        draw_rect(draw, 10, 5, 13, 8, BLACK_FUR, ox, oy)
        draw_rect(draw, 19, 5, 22, 8, BLACK_FUR, ox, oy)
        if blink:
            draw_rect(draw, 11, 6, 12, 6, OUTLINE, ox, oy)
            draw_rect(draw, 20, 6, 21, 6, OUTLINE, ox, oy)
        else:
            draw_pixel(draw, 11, 6, EYE_WHITE, ox, oy)
            draw_pixel(draw, 20, 6, EYE_WHITE, ox, oy)

        draw_pixel(draw, 16, 8, OUTLINE, ox, oy)  # Nose

        # Dangling paws
        draw_rect(draw, 10, 22, 13, 27, BLACK_FUR, ox, oy)
        draw_rect(draw, 19, 22, 22, 27, BLACK_FUR, ox, oy)

    elif state == "fall":
        # Parachute / star fall through the air
        draw_rect(draw, 10, 10, 22, 21, WHITE_FUR, ox, oy)
        draw_rect(draw, 10, 10, 22, 15, BLACK_FUR, ox, oy)
        draw_rect(draw, 11, 4, 21, 12, WHITE_FUR, ox, oy)
        draw_rect(draw, 9, 1, 13, 4, BLACK_FUR, ox, oy)
        draw_rect(draw, 19, 1, 23, 4, BLACK_FUR, ox, oy)

        draw_rect(draw, 11, 7, 14, 9, BLACK_FUR, ox, oy)
        draw_rect(draw, 18, 7, 21, 9, BLACK_FUR, ox, oy)
        draw_pixel(draw, 12, 7, EYE_WHITE, ox, oy)
        draw_pixel(draw, 19, 7, EYE_WHITE, ox, oy)
        draw_pixel(draw, 16, 9, OUTLINE, ox, oy)

        # Splayed out paws
        draw_rect(draw, 5, 8, 9, 12, BLACK_FUR, ox, oy)
        draw_rect(draw, 23, 8, 27, 12, BLACK_FUR, ox, oy)
        draw_rect(draw, 6, 20, 10, 24, BLACK_FUR, ox, oy)
        draw_rect(draw, 22, 20, 26, 24, BLACK_FUR, ox, oy)


def generate_panda_pack(output_dir: Path):
    """Generate the spritesheet and pet.json metadata for Bao the Panda."""
    output_dir.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (FRAME_SIZE * COLS, FRAME_SIZE * ROWS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    states = [
        ("idle", 4),
        ("walk", 4),
        ("run", 4),
        ("jump", 3),
        ("sleep", 4),
        ("groom", 4),
        ("drag", 2),
        ("fall", 2),
    ]

    for row_idx, (state_name, frame_count) in enumerate(states):
        for col_idx in range(frame_count):
            ox = col_idx * FRAME_SIZE
            oy = row_idx * FRAME_SIZE
            create_panda_frame(state_name, col_idx, ox, oy, draw)

    spritesheet_path = output_dir / "spritesheet.png"
    img.save(spritesheet_path, "PNG")

    meta = {
        "name": "Bao the Panda",
        "description": "A delightful chubby giant panda who loves bamboo shoots, cozy naps, and waddling along your taskbar.",
        "author": "Antigravity",
        "version": "1.0",
        "frame_width": FRAME_SIZE,
        "frame_height": FRAME_SIZE,
        "spritesheet": "spritesheet.png",
        "default_scale": 2,
        "states": {
            "idle":  {"row": 0, "frames": 4, "fps": 4, "loop": True,  "speed": 0.0},
            "walk":  {"row": 1, "frames": 4, "fps": 6, "loop": True,  "speed": 1.0},
            "run":   {"row": 2, "frames": 4, "fps": 10, "loop": True, "speed": 2.6},
            "jump":  {"row": 3, "frames": 3, "fps": 5, "loop": False, "speed": 1.2},
            "sleep": {"row": 4, "frames": 4, "fps": 2, "loop": True,  "speed": 0.0},
            "groom": {"row": 5, "frames": 4, "fps": 4, "loop": True,  "speed": 0.0},
            "drag":  {"row": 6, "frames": 2, "fps": 3, "loop": True,  "speed": 0.0},
            "fall":  {"row": 7, "frames": 2, "fps": 6, "loop": True,  "speed": 0.0}
        }
    }

    config_path = output_dir / "pet.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Generated panda spritesheet at: {spritesheet_path}")
    print(f"Generated pet config at: {config_path}")


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "pets" / "default_panda"
    generate_panda_pack(target)
