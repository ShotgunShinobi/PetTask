"""Finite State Machine & Physics Engine for Desktop Pet.
Controls autonomous AI decisions, walking along taskbar path, micro-jumps,
falling physics, drag-and-drop, and cute reactions.
"""

import math
import random
from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal

from core.animator import SpriteAnimator
from core.taskbar import TaskbarInfo


class PetStateMachine(QObject):
    """Behavior and physics controller for desktop pet."""

    state_changed = pyqtSignal(str)
    position_changed = pyqtSignal(float, float)

    GRAVITY = 750.0  # pixels / s^2

    def __init__(self, animator: SpriteAnimator, taskbar_info: TaskbarInfo):
        super().__init__()
        self.animator = animator
        self.taskbar_info = taskbar_info

        # Position and physics
        self.x: float = float(taskbar_info.min_x + 200)
        self.y: float = float(taskbar_info.floor_y - self.animator.current_height)
        self.vx: float = 0.0
        self.vy: float = 0.0
        self.direction: int = 1  # 1 = Right, -1 = Left

        # State tracking
        self.state: str = "idle"
        self.state_timer: float = 0.0
        self.state_duration: float = random.uniform(2.5, 6.0)
        self.previous_ground_state: str = "idle"

        # Parameters
        self.speed_multiplier: float = 1.0
        self.base_walk_speed: float = 45.0   # px / s
        self.base_run_speed: float = 110.0   # px / s
        self.jump_impulse: float = -140.0    # micro-jump: gives ~3-5px hop
        self.is_dragged: bool = False
        self.drag_offset_x: float = 0.0
        self.drag_offset_y: float = 0.0

        # Particle timers
        self._sleep_particle_timer: float = 0.0

    @property
    def floor_y(self) -> float:
        """The Y position where pet's feet touch the top of taskbar."""
        return float(self.taskbar_info.floor_y - self.animator.current_height)

    def update_taskbar_info(self, info: TaskbarInfo):
        """Update bounds when screen/taskbar layout changes."""
        self.taskbar_info = info
        if not self.is_dragged and self.state != "fall":
            self.y = self.floor_y
            self.clamp_x()

    def clamp_x(self):
        min_x = float(self.taskbar_info.min_x)
        max_x = float(self.taskbar_info.max_x - self.animator.current_width)
        self.x = max(min_x, min(self.x, max_x))

    def set_state(self, new_state: str, duration: Optional[float] = None):
        """Transition to a new behavior state."""
        self.state = new_state
        self.state_timer = 0.0
        self.animator.set_state(new_state)

        if duration is not None:
            self.state_duration = duration
        else:
            if new_state == "idle":
                self.state_duration = random.uniform(2.0, 5.0)
                self.vx = 0.0
            elif new_state == "walk":
                self.state_duration = random.uniform(3.0, 8.0)
                self.direction = random.choice([-1, 1])
                self.animator.set_facing(self.direction > 0)
            elif new_state == "run":
                self.state_duration = random.uniform(2.0, 4.5)
                self.direction = random.choice([-1, 1])
                self.animator.set_facing(self.direction > 0)
            elif new_state == "sleep":
                self.state_duration = random.uniform(10.0, 25.0)
                self.vx = 0.0
                self._sleep_particle_timer = 0.5
            elif new_state == "groom":
                self.state_duration = random.uniform(3.0, 6.0)
                self.vx = 0.0
            elif new_state == "jump":
                # Cute micro-jump
                self.vy = self.jump_impulse
                self.state_duration = 1.0

        self.state_changed.emit(new_state)

    def force_action(self, action_name: str):
        """Allows direct user triggering from context menu."""
        if self.is_dragged:
            return

        if action_name == "jump":
            self.trigger_jump()
        elif action_name in ("walk", "run", "sleep", "groom", "idle"):
            self.set_state(action_name)

    def trigger_jump(self, micro: bool = True):
        """Initiate a cute jump (micro-jump by 2-5 pixels)."""
        if self.state in ("drag", "fall"):
            return
        self.previous_ground_state = self.state if self.state in ("walk", "run") else "idle"
        self.state = "jump"
        self.animator.set_state("jump")
        # Micro jump gives 2 to 4 px hop; bigger jump gives 8 to 12 px
        self.vy = -110.0 if micro else -220.0
        self.state_changed.emit("jump")

    def pet_clicked(self):
        """React to user petting / clicking the pet."""
        if self.is_dragged:
            return

        # Emit heart particle
        center_x = self.animator.current_width / 2.0
        self.animator.emit_heart(center_x, 0.0)

        # If asleep, wake up!
        if self.state == "sleep":
            self.set_state("idle", duration=2.0)
        else:
            # Cute happy little bounce
            self.trigger_jump(micro=True)

    # ----------------------------------------------------
    # Mouse Drag & Drop
    # ----------------------------------------------------
    def start_drag(self, global_mouse_x: float, global_mouse_y: float):
        self.is_dragged = True
        self.drag_offset_x = global_mouse_x - self.x
        self.drag_offset_y = global_mouse_y - self.y
        self.vx = 0.0
        self.vy = 0.0
        self.set_state("drag")

    def update_drag(self, global_mouse_x: float, global_mouse_y: float):
        if not self.is_dragged:
            return
        self.x = global_mouse_x - self.drag_offset_x
        self.y = global_mouse_y - self.drag_offset_y
        self.position_changed.emit(self.x, self.y)

    def end_drag(self):
        if not self.is_dragged:
            return
        self.is_dragged = False

        if self.y < self.floor_y - 2:
            # Dropped above taskbar -> fall with gravity!
            self.set_state("fall")
            self.vy = 0.0
        else:
            # On or below taskbar -> snap to floor
            self.y = self.floor_y
            self.clamp_x()
            self.set_state("idle")

    # ----------------------------------------------------
    # Main Physics & AI Loop (Called at 60 FPS)
    # ----------------------------------------------------
    def tick(self, dt: float):
        if self.is_dragged:
            self.animator.update(dt)
            return

        self.state_timer += dt
        min_x = float(self.taskbar_info.min_x)
        max_x = float(self.taskbar_info.max_x - self.animator.current_width)

        # 1. State-specific logic
        if self.state == "idle":
            self.vx = 0.0
            if self.state_timer >= self.state_duration:
                self._choose_next_state()

        elif self.state == "walk":
            speed = self.base_walk_speed * self.speed_multiplier
            self.vx = speed * self.direction
            self.x += self.vx * dt

            # Turn around at edges
            if self.x <= min_x:
                self.x = min_x
                self.direction = 1
                self.animator.set_facing(True)
            elif self.x >= max_x:
                self.x = max_x
                self.direction = -1
                self.animator.set_facing(False)

            # Random micro-jump while walking (10% chance)
            if random.random() < 0.008:
                self.trigger_jump(micro=True)

            if self.state_timer >= self.state_duration:
                self._choose_next_state()

        elif self.state == "run":
            speed = self.base_run_speed * self.speed_multiplier
            self.vx = speed * self.direction
            self.x += self.vx * dt

            if self.x <= min_x:
                self.x = min_x
                self.direction = 1
                self.animator.set_facing(True)
            elif self.x >= max_x:
                self.x = max_x
                self.direction = -1
                self.animator.set_facing(False)

            # High sprint micro-jump
            if random.random() < 0.015:
                self.trigger_jump(micro=True)

            if self.state_timer >= self.state_duration:
                # Catch breath
                self.set_state("idle", duration=random.uniform(1.5, 3.0))

        elif self.state == "jump":
            # Jump physics
            self.vy += self.GRAVITY * dt
            self.y += self.vy * dt

            # Preserve horizontal movement if jumping during walk
            if self.previous_ground_state in ("walk", "run"):
                spd = (self.base_walk_speed if self.previous_ground_state == "walk" else self.base_run_speed)
                self.x += spd * self.direction * self.speed_multiplier * dt
                self.clamp_x()

            # Land on floor
            if self.y >= self.floor_y:
                self.y = self.floor_y
                self.vy = 0.0
                self.animator.emit_dust(self.animator.current_width / 2.0, self.animator.current_height)
                self.set_state(self.previous_ground_state or "idle")

        elif self.state == "sleep":
            self.vx = 0.0
            self._sleep_particle_timer += dt
            if self._sleep_particle_timer >= 2.2:
                self._sleep_particle_timer = 0.0
                self.animator.emit_zzz(self.animator.current_width * 0.7, 5.0)

            if self.state_timer >= self.state_duration:
                # Wake up and stretch/groom
                self.set_state("groom", duration=random.uniform(3.0, 5.0))

        elif self.state == "groom":
            self.vx = 0.0
            if self.state_timer >= self.state_duration:
                self._choose_next_state()

        elif self.state == "fall":
            # Falling under gravity after being dropped
            self.vy += self.GRAVITY * dt
            self.y += self.vy * dt

            if self.y >= self.floor_y:
                self.y = self.floor_y
                # Bounce slightly if fast fall
                if self.vy > 200:
                    self.vy = -self.vy * 0.2
                    self.animator.emit_dust(self.animator.current_width / 2.0, self.animator.current_height)
                else:
                    self.vy = 0.0
                    self.animator.emit_dust(self.animator.current_width / 2.0, self.animator.current_height)
                    self.set_state("idle", duration=1.5)

        # Keep within horizontal screen bounds
        self.clamp_x()

        # Update animation frames and particles
        self.animator.update(dt)
        self.position_changed.emit(self.x, self.y)

    def _choose_next_state(self):
        """Autonomous AI state selector."""
        roll = random.random()
        if roll < 0.40:
            self.set_state("walk")
        elif roll < 0.55:
            self.set_state("idle")
        elif roll < 0.70:
            self.set_state("groom")
        elif roll < 0.85:
            self.set_state("run")
        else:
            self.set_state("sleep")
