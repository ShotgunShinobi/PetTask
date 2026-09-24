"""Procedural Pixel Art Cat Generator for Desktop Pet.
Generates an adorable 32x32 animated cat spritesheet with 8 complete states:
idle, walk, run, jump, sleep, groom, drag, fall.
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw

# Color Palette (Crisp retro kawaii palette)
OUTLINE = (55, 30, 20, 255)       # Dark chocolate outline
BODY = (245, 142, 54, 255)        # Warm ginger orange
BODY_DARK = (212, 107, 28, 255)   # Tabby stripes / shadow
BELLY = (255, 248, 235, 255)      # Creamy white chest & muzzle
PINK = (255, 175, 175, 255)       # Inner ears & cute nose
EYE = (38, 42, 53, 255)           # Dark kawaii eyes
EYE_SHINE = (255, 255, 255, 255)  # White eye shine
PAW = (255, 250, 240, 255)        # White paws
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


def create_cat_frame(state: str, frame_idx: int, ox: int, oy: int, draw: ImageDraw.ImageDraw):
    """Draw a single 32x32 frame of the cat at offset (ox, oy)."""

    if state == "idle":
        # Sitting/standing peacefully. Tail wags, chest breathes, blink on frame 3.
        breathe = 1 if frame_idx in (1, 2) else 0
        blink = (frame_idx == 3)
        tail_y = [17, 16, 15, 16][frame_idx]

        # Body
        draw_rect(draw, 10, 16 - breathe, 22, 27, BODY, ox, oy)
        draw_rect(draw, 12, 18 - breathe, 18, 26, BELLY, ox, oy)
        # Outline
        draw_rect(draw, 9, 16 - breathe, 9, 27, OUTLINE, ox, oy)
        draw_rect(draw, 23, 16 - breathe, 23, 27, OUTLINE, ox, oy)
        draw_rect(draw, 10, 28, 22, 28, OUTLINE, ox, oy)

        # Tabby stripes
        draw_rect(draw, 20, 17 - breathe, 22, 18 - breathe, BODY_DARK, ox, oy)
        draw_rect(draw, 19, 21 - breathe, 22, 22 - breathe, BODY_DARK, ox, oy)

        # Head
        draw_rect(draw, 7, 9 - breathe, 19, 17 - breathe, BODY, ox, oy)
        draw_rect(draw, 6, 10 - breathe, 6, 16 - breathe, OUTLINE, ox, oy)
        draw_rect(draw, 20, 10 - breathe, 20, 16 - breathe, OUTLINE, ox, oy)
        draw_rect(draw, 7, 8 - breathe, 19, 8 - breathe, OUTLINE, ox, oy)

        # Ears
        # Left ear
        draw_rect(draw, 7, 5 - breathe, 10, 8 - breathe, BODY, ox, oy)
        draw_pixel(draw, 8, 4 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 9, 4 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 8, 6 - breathe, PINK, ox, oy)
        draw_pixel(draw, 9, 6 - breathe, PINK, ox, oy)
        # Right ear
        draw_rect(draw, 15, 5 - breathe, 18, 8 - breathe, BODY, ox, oy)
        draw_pixel(draw, 16, 4 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 17, 4 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 16, 6 - breathe, PINK, ox, oy)
        draw_pixel(draw, 17, 6 - breathe, PINK, ox, oy)

        # Face
        draw_rect(draw, 9, 14 - breathe, 14, 16 - breathe, BELLY, ox, oy)
        draw_pixel(draw, 11, 14 - breathe, PINK, ox, oy)  # Nose

        if blink:
            draw_rect(draw, 8, 12 - breathe, 10, 12 - breathe, OUTLINE, ox, oy)
            draw_rect(draw, 14, 12 - breathe, 16, 12 - breathe, OUTLINE, ox, oy)
        else:
            # Eyes
            draw_rect(draw, 8, 11 - breathe, 10, 13 - breathe, EYE, ox, oy)
            draw_pixel(draw, 8, 11 - breathe, EYE_SHINE, ox, oy)
            draw_rect(draw, 14, 11 - breathe, 16, 13 - breathe, EYE, ox, oy)
            draw_pixel(draw, 14, 11 - breathe, EYE_SHINE, ox, oy)

        # Paws
        draw_rect(draw, 10, 26, 13, 27, PAW, ox, oy)
        draw_rect(draw, 17, 26, 20, 27, PAW, ox, oy)

        # Tail
        draw_rect(draw, 23, tail_y, 27, tail_y + 1, BODY, ox, oy)
        draw_pixel(draw, 27, tail_y - 1, BODY, ox, oy)
        draw_pixel(draw, 27, tail_y - 2, BODY_DARK, ox, oy)
        draw_pixel(draw, 26, tail_y - 3, OUTLINE, ox, oy)

    elif state == "walk":
        # 4 frame walking cycle
        leg_offsets = [
            (0, 0, 0, 0),      # Neutral
            (-1, 1, 1, -1),    # Step 1
            (0, 0, 0, 0),      # Neutral
            (1, -1, -1, 1)     # Step 2
        ][frame_idx]
        bob = 1 if frame_idx in (1, 3) else 0

        # Body (horizontal elongated)
        draw_rect(draw, 8, 15 - bob, 23, 23 - bob, BODY, ox, oy)
        draw_rect(draw, 10, 19 - bob, 18, 23 - bob, BELLY, ox, oy)
        draw_rect(draw, 7, 15 - bob, 7, 23 - bob, OUTLINE, ox, oy)
        draw_rect(draw, 24, 15 - bob, 24, 23 - bob, OUTLINE, ox, oy)
        draw_rect(draw, 8, 14 - bob, 23, 14 - bob, OUTLINE, ox, oy)

        # Tabby stripes
        draw_rect(draw, 14, 15 - bob, 15, 17 - bob, BODY_DARK, ox, oy)
        draw_rect(draw, 19, 15 - bob, 20, 17 - bob, BODY_DARK, ox, oy)

        # Head (forward facing right)
        draw_rect(draw, 17, 9 - bob, 28, 18 - bob, BODY, ox, oy)
        draw_rect(draw, 16, 9 - bob, 16, 18 - bob, OUTLINE, ox, oy)
        draw_rect(draw, 29, 9 - bob, 29, 18 - bob, OUTLINE, ox, oy)
        draw_rect(draw, 17, 8 - bob, 28, 8 - bob, OUTLINE, ox, oy)

        # Ears
        draw_rect(draw, 18, 5 - bob, 21, 8 - bob, BODY, ox, oy)
        draw_pixel(draw, 19, 6 - bob, PINK, ox, oy)
        draw_rect(draw, 24, 5 - bob, 27, 8 - bob, BODY, ox, oy)
        draw_pixel(draw, 25, 6 - bob, PINK, ox, oy)

        # Eye & Muzzle
        draw_rect(draw, 23, 11 - bob, 25, 13 - bob, EYE, ox, oy)
        draw_pixel(draw, 23, 11 - bob, EYE_SHINE, ox, oy)
        draw_rect(draw, 26, 14 - bob, 28, 16 - bob, BELLY, ox, oy)
        draw_pixel(draw, 28, 14 - bob, PINK, ox, oy)

        # Legs (Front & Back moving)
        fl, fr, bl, br = leg_offsets
        # Back legs
        draw_rect(draw, 9 + bl, 24, 11 + bl, 27, BODY, ox, oy)
        draw_rect(draw, 9 + bl, 27, 11 + bl, 27, PAW, ox, oy)
        draw_rect(draw, 13 + br, 24, 15 + br, 27, BODY_DARK, ox, oy)
        draw_rect(draw, 13 + br, 27, 15 + br, 27, PAW, ox, oy)
        # Front legs
        draw_rect(draw, 19 + fl, 24, 21 + fl, 27, BODY, ox, oy)
        draw_rect(draw, 19 + fl, 27, 21 + fl, 27, PAW, ox, oy)
        draw_rect(draw, 23 + fr, 24, 25 + fr, 27, BODY_DARK, ox, oy)
        draw_rect(draw, 23 + fr, 27, 25 + fr, 27, PAW, ox, oy)

        # Tail
        draw_rect(draw, 5, 13 - bob, 7, 15 - bob, BODY, ox, oy)
        draw_rect(draw, 3, 11 - bob, 5, 13 - bob, BODY_DARK, ox, oy)

    elif state == "run":
        # 4 frame energetic sprint
        stretch = [0, 2, 1, -1][frame_idx]
        y_lift = [0, -2, -3, -1][frame_idx]

        # Body stretched
        draw_rect(draw, 6 - stretch, 16 + y_lift, 23 + stretch, 22 + y_lift, BODY, ox, oy)
        draw_rect(draw, 10, 18 + y_lift, 20, 22 + y_lift, BELLY, ox, oy)
        draw_rect(draw, 13, 16 + y_lift, 15, 18 + y_lift, BODY_DARK, ox, oy)
        draw_rect(draw, 18, 16 + y_lift, 20, 18 + y_lift, BODY_DARK, ox, oy)

        # Head low and focused
        draw_rect(draw, 20 + stretch, 11 + y_lift, 29 + stretch, 19 + y_lift, BODY, ox, oy)
        draw_rect(draw, 21 + stretch, 7 + y_lift, 23 + stretch, 10 + y_lift, BODY, ox, oy)  # Ear
        draw_pixel(draw, 22 + stretch, 8 + y_lift, PINK, ox, oy)
        draw_rect(draw, 26 + stretch, 7 + y_lift, 28 + stretch, 10 + y_lift, BODY, ox, oy)  # Ear
        draw_pixel(draw, 27 + stretch, 8 + y_lift, PINK, ox, oy)

        # Eyes narrowed / excited
        draw_rect(draw, 25 + stretch, 13 + y_lift, 28 + stretch, 14 + y_lift, EYE, ox, oy)
        draw_pixel(draw, 28 + stretch, 15 + y_lift, PINK, ox, oy)

        # Legs extended
        if frame_idx in (1, 2):  # Leaping in air
            draw_rect(draw, 3 - stretch, 17 + y_lift, 6 - stretch, 20 + y_lift, PAW, ox, oy)
            draw_rect(draw, 25 + stretch, 20 + y_lift, 29 + stretch, 22 + y_lift, PAW, ox, oy)
        else:
            draw_rect(draw, 8, 22 + y_lift, 11, 26 + y_lift, PAW, ox, oy)
            draw_rect(draw, 20, 22 + y_lift, 23, 26 + y_lift, PAW, ox, oy)

        # Tail streaming straight back
        draw_rect(draw, 1 - stretch, 15 + y_lift, 6 - stretch, 17 + y_lift, BODY_DARK, ox, oy)

    elif state == "jump":
        # 3 frames: 0=crouch, 1=leap high, 2=land
        if frame_idx == 0:  # Crouch
            draw_rect(draw, 8, 20, 24, 27, BODY, ox, oy)
            draw_rect(draw, 18, 14, 28, 22, BODY, ox, oy)
            draw_rect(draw, 21, 10, 24, 13, BODY, ox, oy)  # Ears
            draw_rect(draw, 25, 10, 28, 13, BODY, ox, oy)
            draw_pixel(draw, 25, 16, EYE, ox, oy)
            draw_rect(draw, 10, 26, 14, 27, PAW, ox, oy)
            draw_rect(draw, 20, 26, 24, 27, PAW, ox, oy)
        elif frame_idx == 1:  # Leap up in air
            draw_rect(draw, 10, 7, 22, 17, BODY, ox, oy)
            draw_rect(draw, 16, 2, 26, 10, BODY, ox, oy)
            draw_rect(draw, 18, 0, 21, 2, BODY, ox, oy)  # Ears
            draw_rect(draw, 23, 0, 26, 2, BODY, ox, oy)
            draw_rect(draw, 22, 4, 25, 6, EYE, ox, oy)
            draw_pixel(draw, 22, 4, EYE_SHINE, ox, oy)
            # Stretched paws
            draw_rect(draw, 7, 16, 10, 21, PAW, ox, oy)
            draw_rect(draw, 22, 10, 27, 13, PAW, ox, oy)
        else:  # Landing puff
            draw_rect(draw, 8, 18, 24, 26, BODY, ox, oy)
            draw_rect(draw, 17, 12, 27, 20, BODY, ox, oy)
            draw_rect(draw, 19, 8, 22, 11, BODY, ox, oy)
            draw_rect(draw, 24, 8, 27, 11, BODY, ox, oy)
            draw_pixel(draw, 23, 14, EYE, ox, oy)
            draw_rect(draw, 9, 26, 13, 27, PAW, ox, oy)
            draw_rect(draw, 21, 26, 25, 27, PAW, ox, oy)

    elif state == "sleep":
        # Curled into an adorable sleeping ball with breathing motion
        breathe = 1 if frame_idx in (1, 2) else 0
        draw_rect(draw, 7, 17 - breathe, 25, 27, BODY, ox, oy)
        draw_rect(draw, 10, 20 - breathe, 22, 26, BELLY, ox, oy)
        draw_rect(draw, 15, 17 - breathe, 18, 19 - breathe, BODY_DARK, ox, oy)
        draw_rect(draw, 20, 18 - breathe, 23, 20 - breathe, BODY_DARK, ox, oy)

        # Head tucked in
        draw_rect(draw, 6, 18 - breathe, 14, 26, BODY, ox, oy)
        # Ears flat
        draw_rect(draw, 6, 15 - breathe, 9, 17 - breathe, BODY, ox, oy)
        draw_pixel(draw, 7, 16 - breathe, PINK, ox, oy)

        # Sleeping closed eye: curved cute line
        draw_pixel(draw, 8, 22 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 9, 23 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 10, 22 - breathe, OUTLINE, ox, oy)
        draw_pixel(draw, 11, 23 - breathe, PINK, ox, oy)  # Nose

        # Tail curled over paws
        draw_rect(draw, 22, 22, 26, 26, BODY, ox, oy)
        draw_rect(draw, 18, 25, 23, 27, BODY_DARK, ox, oy)

    elif state == "groom":
        # Licking paw / washing face
        paw_lift = [0, 2, 4, 2][frame_idx]
        draw_rect(draw, 10, 16, 22, 27, BODY, ox, oy)
        draw_rect(draw, 12, 18, 18, 26, BELLY, ox, oy)
        draw_rect(draw, 8, 10, 19, 18, BODY, ox, oy)
        draw_rect(draw, 8, 6, 11, 9, BODY, ox, oy)
        draw_rect(draw, 15, 6, 18, 9, BODY, ox, oy)

        # Closed contented eyes
        draw_rect(draw, 9, 12, 11, 12, OUTLINE, ox, oy)
        draw_rect(draw, 14, 12, 16, 12, OUTLINE, ox, oy)
        draw_pixel(draw, 12, 14, PINK, ox, oy)

        # Front paw raised to mouth
        draw_rect(draw, 11, 18 - paw_lift, 14, 21 - paw_lift, PAW, ox, oy)
        if frame_idx in (1, 2):
            draw_pixel(draw, 13, 15, PINK, ox, oy)  # Little tongue out!

        draw_rect(draw, 17, 25, 20, 27, PAW, ox, oy)
        draw_rect(draw, 22, 20, 25, 24, BODY, ox, oy)

    elif state == "drag":
        # Picked up by the scruff! Dangling legs, surprised wide eyes
        blink = (frame_idx == 1)
        draw_rect(draw, 11, 10, 21, 22, BODY, ox, oy)
        draw_rect(draw, 13, 12, 19, 20, BELLY, ox, oy)
        draw_rect(draw, 10, 4, 22, 12, BODY, ox, oy)
        draw_rect(draw, 9, 1, 12, 4, BODY, ox, oy)
        draw_rect(draw, 20, 1, 23, 4, BODY, ox, oy)
        draw_pixel(draw, 10, 2, PINK, ox, oy)
        draw_pixel(draw, 21, 2, PINK, ox, oy)

        if blink:
            draw_rect(draw, 12, 7, 14, 7, OUTLINE, ox, oy)
            draw_rect(draw, 18, 7, 20, 7, OUTLINE, ox, oy)
        else:
            # Big surprised round eyes
            draw_rect(draw, 12, 6, 14, 8, EYE, ox, oy)
            draw_pixel(draw, 12, 6, EYE_SHINE, ox, oy)
            draw_rect(draw, 18, 6, 20, 8, EYE, ox, oy)
            draw_pixel(draw, 18, 6, EYE_SHINE, ox, oy)
        draw_pixel(draw, 16, 9, PINK, ox, oy)

        # Dangling paws
        draw_rect(draw, 11, 22, 13, 27, PAW, ox, oy)
        draw_rect(draw, 19, 22, 21, 27, PAW, ox, oy)
        # Tail curled in between legs
        draw_rect(draw, 15, 22, 17, 28, BODY_DARK, ox, oy)

    elif state == "fall":
        # Falling through the air, paws flared out like a flying squirrel
        draw_rect(draw, 10, 11, 22, 21, BODY, ox, oy)
        draw_rect(draw, 12, 13, 20, 19, BELLY, ox, oy)
        draw_rect(draw, 11, 5, 21, 13, BODY, ox, oy)
        draw_rect(draw, 10, 2, 13, 5, BODY, ox, oy)
        draw_rect(draw, 19, 2, 22, 5, BODY, ox, oy)
        draw_rect(draw, 12, 8, 14, 10, EYE, ox, oy)
        draw_pixel(draw, 12, 8, EYE_SHINE, ox, oy)
        draw_rect(draw, 18, 8, 20, 10, EYE, ox, oy)
        draw_pixel(draw, 18, 8, EYE_SHINE, ox, oy)
        draw_pixel(draw, 16, 10, PINK, ox, oy)

        # Paws spread out high & low
        draw_rect(draw, 6, 9, 9, 12, PAW, ox, oy)
        draw_rect(draw, 23, 9, 26, 12, PAW, ox, oy)
        draw_rect(draw, 7, 21, 10, 24, PAW, ox, oy)
        draw_rect(draw, 22, 21, 25, 24, PAW, ox, oy)
        # Tail pointing straight up
        draw_rect(draw, 15, 2, 17, 7, BODY_DARK, ox, oy)


def generate_cat_pack(output_dir: Path):
    """Generate the spritesheet and pet.json metadata."""
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
            create_cat_frame(state_name, col_idx, ox, oy, draw)

    spritesheet_path = output_dir / "spritesheet.png"
    img.save(spritesheet_path, "PNG")

    meta = {
        "name": "Neko the Cat",
        "description": "An adorable ginger tabby cat companion that loves running along your taskbar.",
        "author": "Antigravity",
        "version": "1.0",
        "frame_width": FRAME_SIZE,
        "frame_height": FRAME_SIZE,
        "spritesheet": "spritesheet.png",
        "default_scale": 2,
        "states": {
            "idle":  {"row": 0, "frames": 4, "fps": 4, "loop": True,  "speed": 0.0},
            "walk":  {"row": 1, "frames": 4, "fps": 7, "loop": True,  "speed": 1.2},
            "run":   {"row": 2, "frames": 4, "fps": 12, "loop": True, "speed": 3.0},
            "jump":  {"row": 3, "frames": 3, "fps": 6, "loop": False, "speed": 1.5},
            "sleep": {"row": 4, "frames": 4, "fps": 2, "loop": True,  "speed": 0.0},
            "groom": {"row": 5, "frames": 4, "fps": 4, "loop": True,  "speed": 0.0},
            "drag":  {"row": 6, "frames": 2, "fps": 3, "loop": True,  "speed": 0.0},
            "fall":  {"row": 7, "frames": 2, "fps": 6, "loop": True,  "speed": 0.0}
        }
    }

    config_path = output_dir / "pet.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"Generated cat spritesheet at: {spritesheet_path}")
    print(f"Generated pet config at: {config_path}")


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "pets" / "default_cat"
    generate_cat_pack(target)
