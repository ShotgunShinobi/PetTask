"""Sprite Animation & Particle Engine for Desktop Pet.
Handles frame slicing, nearest-neighbor pixel scaling, orientation flipping,
GIF animations, and floating particles (Zzz, hearts, dust puffs).
"""

import json
import math
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QImage, QPainter, QPixmap, QTransform
from PIL import Image, ImageSequence


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float        # 0.0 to 1.0 (1.0 is fresh, 0.0 is dead)
    decay: float       # life subtracted per second
    kind: str          # "heart", "zzz", "dust"
    text: str = ""
    size: float = 12.0
    color: QColor = field(default_factory=lambda: QColor(255, 100, 150))


@dataclass
class StateAnimation:
    name: str
    frames: List[QPixmap]
    flipped_frames: List[QPixmap]
    fps: float
    loop: bool
    speed: float


class SpriteAnimator:
    """Manages sprite frames, animations, and particle effects."""

    def __init__(self, pet_dir: Path, scale: int = 2):
        self.pet_dir = Path(pet_dir)
        self.scale = max(1, scale)
        self.meta: dict = {}
        self.animations: Dict[str, StateAnimation] = {}
        self.current_state: str = "idle"
        self.frame_index: int = 0
        self.frame_time_accum: float = 0.0
        self.facing_right: bool = True
        self.particles: List[Particle] = []
        self.frame_width: int = 32
        self.frame_height: int = 32
        self.animation_finished: bool = False

        self.load_pet(self.pet_dir)

    def load_pet(self, pet_dir: Path):
        """Loads pet configuration and generates scaled frames."""
        self.pet_dir = Path(pet_dir)
        config_path = self.pet_dir / "pet.json"

        if not config_path.exists():
            raise FileNotFoundError(f"Missing pet.json in {pet_dir}")

        with open(config_path, "r", encoding="utf-8") as f:
            self.meta = json.load(f)

        self.frame_width = self.meta.get("frame_width", 32)
        self.frame_height = self.meta.get("frame_height", 32)
        spritesheet_file = self.meta.get("spritesheet", "spritesheet.png")
        sheet_path = self.pet_dir / spritesheet_file

        if not sheet_path.exists():
            raise FileNotFoundError(f"Missing spritesheet at {sheet_path}")

        # Check if source is an animated GIF or a PNG spritesheet
        if sheet_path.suffix.lower() == ".gif":
            self._load_from_gif(sheet_path)
        else:
            self._load_from_sheet(sheet_path)

        self.set_state("idle")

    def _load_from_sheet(self, sheet_path: Path):
        """Slices a PNG spritesheet into distinct state animations."""
        master_pixmap = QPixmap(str(sheet_path))
        if master_pixmap.isNull():
            raise ValueError(f"Could not load image at {sheet_path}")

        states_cfg = self.meta.get("states", {})
        self.animations.clear()

        fw = self.frame_width
        fh = self.frame_height
        target_w = fw * self.scale
        target_h = fh * self.scale

        transform_flip = QTransform().scale(-1, 1)

        for state_name, cfg in states_cfg.items():
            row = cfg.get("row", 0)
            col_start = cfg.get("col_start", 0)
            count = cfg.get("frames", 1)
            fps = float(cfg.get("fps", 6))
            loop = cfg.get("loop", True)
            speed = float(cfg.get("speed", 1.0))

            normal_frames: List[QPixmap] = []
            flipped_frames: List[QPixmap] = []

            for i in range(count):
                cx = (col_start + i) * fw
                cy = row * fh
                raw_frame = master_pixmap.copy(cx, cy, fw, fh)
                scaled_frame = raw_frame.scaled(
                    target_w, target_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.FastTransformation  # Pixel-crisp nearest neighbor!
                )
                flipped_frame = scaled_frame.transformed(transform_flip)

                normal_frames.append(scaled_frame)
                flipped_frames.append(flipped_frame)

            self.animations[state_name] = StateAnimation(
                name=state_name,
                frames=normal_frames,
                flipped_frames=flipped_frames,
                fps=fps,
                loop=loop,
                speed=speed
            )

    def _load_from_gif(self, gif_path: Path):
        """Extracts frames from an animated GIF for quick single-loop pets."""
        pil_img = Image.open(gif_path)
        frames_list: List[QPixmap] = []
        flipped_list: List[QPixmap] = []

        transform_flip = QTransform().scale(-1, 1)

        for frame in ImageSequence.Iterator(pil_img):
            rgba_frame = frame.convert("RGBA")
            data = rgba_frame.tobytes("raw", "RGBA")
            qimg = QImage(data, rgba_frame.size[0], rgba_frame.size[1], QImage.Format.Format_RGBA8888)
            pix = QPixmap.fromImage(qimg)

            target_w = pix.width() * self.scale
            target_h = pix.height() * self.scale
            scaled = pix.scaled(target_w, target_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
            flipped = scaled.transformed(transform_flip)

            frames_list.append(scaled)
            flipped_list.append(flipped)

        fps = 1000.0 / pil_img.info.get("duration", 100) if pil_img.info.get("duration") else 8.0

        for state in ["idle", "walk", "run", "jump", "sleep", "groom", "drag", "fall"]:
            self.animations[state] = StateAnimation(
                name=state,
                frames=frames_list,
                flipped_frames=flipped_list,
                fps=fps,
                loop=True,
                speed=1.0 if state in ("walk", "run") else 0.0
            )

    def set_scale(self, new_scale: int):
        """Changes pixel scale and re-caches frames."""
        if new_scale != self.scale and new_scale >= 1:
            self.scale = new_scale
            self.load_pet(self.pet_dir)

    def set_state(self, state: str) -> bool:
        """Switch current animation state."""
        if state not in self.animations:
            if "idle" in self.animations:
                state = "idle"
            else:
                return False

        if self.current_state != state:
            self.current_state = state
            self.frame_index = 0
            self.frame_time_accum = 0.0
            self.animation_finished = False
        return True

    def set_facing(self, facing_right: bool):
        self.facing_right = facing_right

    def update(self, delta_time: float):
        """Update animation frames and particles by delta_time (in seconds)."""
        anim = self.animations.get(self.current_state)
        if anim and anim.frames:
            frame_duration = 1.0 / max(0.1, anim.fps)
            self.frame_time_accum += delta_time

            while self.frame_time_accum >= frame_duration:
                self.frame_time_accum -= frame_duration
                if self.frame_index + 1 < len(anim.frames):
                    self.frame_index += 1
                else:
                    if anim.loop:
                        self.frame_index = 0
                    else:
                        self.animation_finished = True

        # Update particles
        alive_particles = []
        for p in self.particles:
            p.x += p.vx * delta_time
            p.y += p.vy * delta_time
            p.life -= p.decay * delta_time
            if p.life > 0:
                alive_particles.append(p)
        self.particles = alive_particles

    def get_current_pixmap(self) -> Optional[QPixmap]:
        """Returns the current active frame pixmap based on state and direction."""
        anim = self.animations.get(self.current_state)
        if not anim or not anim.frames:
            return None
        idx = min(self.frame_index, len(anim.frames) - 1)
        return anim.frames[idx] if self.facing_right else anim.flipped_frames[idx]

    @property
    def current_width(self) -> int:
        return self.frame_width * self.scale

    @property
    def current_height(self) -> int:
        return self.frame_height * self.scale

    # ----------------------------------------------------
    # Particle Emitters
    # ----------------------------------------------------
    def emit_heart(self, x: float, y: float):
        """Spawn a floating love heart."""
        self.particles.append(Particle(
            x=x + random.uniform(-6, 6),
            y=y,
            vx=random.uniform(-10, 10),
            vy=random.uniform(-30, -50),
            life=1.0,
            decay=0.8,
            kind="heart",
            text="❤️",
            size=14 * (self.scale / 2),
            color=QColor(255, 80, 130)
        ))

    def emit_zzz(self, x: float, y: float):
        """Spawn a floating 'Z' sleep particle."""
        letter = random.choice(["z", "Z", "💤"])
        self.particles.append(Particle(
            x=x + random.uniform(-4, 4),
            y=y,
            vx=random.uniform(5, 15),
            vy=random.uniform(-15, -25),
            life=1.0,
            decay=0.5,
            kind="zzz",
            text=letter,
            size=11 * (self.scale / 2),
            color=QColor(150, 180, 255)
        ))

    def emit_dust(self, x: float, y: float):
        """Spawn dust puff particles when landing."""
        for _ in range(3):
            self.particles.append(Particle(
                x=x + random.uniform(-10, 10),
                y=y + random.uniform(-2, 2),
                vx=random.uniform(-25, 25),
                vy=random.uniform(-10, -5),
                life=1.0,
                decay=2.5,
                kind="dust",
                size=random.uniform(3, 5) * (self.scale / 2),
                color=QColor(220, 210, 200, 200)
            ))

    def render(self, painter: QPainter):
        """Draws the pet sprite and all active particles."""
        pixmap = self.get_current_pixmap()
        if pixmap:
            painter.drawPixmap(0, 0, pixmap)

        # Draw particles
        for p in self.particles:
            alpha = int(max(0.0, min(1.0, p.life)) * 255)
            if p.kind in ("heart", "zzz"):
                painter.save()
                font = painter.font()
                font.setPixelSize(int(p.size))
                font.setBold(True)
                painter.setFont(font)
                color = QColor(p.color)
                color.setAlpha(alpha)
                painter.setPen(color)
                painter.drawText(QPointF(p.x, p.y), p.text)
                painter.restore()
            elif p.kind == "dust":
                painter.save()
                color = QColor(p.color)
                color.setAlpha(alpha)
                painter.setBrush(color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(p.x, p.y), p.size / 2, p.size / 2)
                painter.restore()
