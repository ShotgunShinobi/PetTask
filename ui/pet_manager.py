"""Pet Manager & Sprite Importer Dialog for Desktop Pet.
Allows users to switch active pets, upload custom PNG spritesheets or animated GIFs,
configure frame slicing, preview animations, and save new pet profiles.
"""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image
from PyQt6.QtCore import QPointF, QRect, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QImage, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class AnimationPreviewWidget(QWidget):
    """Real-time animation preview canvas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 160)
        self.frames: List[QPixmap] = []
        self.current_idx: int = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_frame)
        self.fps: int = 8

    def set_frames(self, frames: List[QPixmap], fps: int = 8):
        self.frames = frames
        self.current_idx = 0
        self.fps = max(1, fps)
        self.timer.stop()
        if self.frames:
            interval = int(1000.0 / self.fps)
            self.timer.start(interval)
        self.update()

    def set_fps(self, fps: int):
        self.fps = max(1, fps)
        if self.timer.isActive():
            self.timer.setInterval(int(1000.0 / self.fps))

    def _next_frame(self):
        if self.frames:
            self.current_idx = (self.current_idx + 1) % len(self.frames)
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Draw checkerboard background for transparency preview
        tile_size = 10
        for x in range(0, self.width(), tile_size):
            for y in range(0, self.height(), tile_size):
                color = QColor(40, 44, 52) if ((x // tile_size + y // tile_size) % 2 == 0) else QColor(30, 34, 42)
                painter.fillRect(x, y, tile_size, tile_size, color)

        # Draw frame centered with pixel-sharp scaling
        if self.frames and 0 <= self.current_idx < len(self.frames):
            frame = self.frames[self.current_idx]
            scale = min(self.width() / max(1, frame.width()), self.height() / max(1, frame.height()))
            scale = max(1, int(scale * 0.8))  # Snap to integer scale

            scaled_w = frame.width() * scale
            scaled_h = frame.height() * scale
            scaled = frame.scaled(scaled_w, scaled_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

            ox = (self.width() - scaled.width()) // 2
            oy = (self.height() - scaled.height()) // 2
            painter.drawPixmap(ox, oy, scaled)


class PetManagerDialog(QDialog):
    """Dialog for selecting installed pets and importing custom sprite files."""

    pet_selected = pyqtSignal(Path)

    def __init__(self, pets_dir: Path, current_pet_dir: Path, parent=None):
        super().__init__(parent)
        self.pets_dir = Path(pets_dir)
        self.current_pet_dir = Path(current_pet_dir)

        self.setWindowTitle("🐾 Desktop Pet & Sprite Manager")
        self.setFixedSize(680, 580)
        self._apply_dark_style()

        # Import wizard temp state
        self.imported_image_path: Optional[Path] = None
        self.loaded_raw_pixmap: Optional[QPixmap] = None
        self.sliced_preview_frames: List[QPixmap] = []

        self._setup_ui()
        self._refresh_installed_pets()

    def _apply_dark_style(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #121316;
                color: #e2e8f0;
                font-family: 'Segoe UI', sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #2d3139;
                background: #181a1f;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #181a1f;
                color: #94a3b8;
                padding: 10px 24px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: #2563eb;
                color: #ffffff;
            }
            QListWidget {
                background-color: #16181d;
                border: 1px solid #2b2f38;
                border-radius: 6px;
                padding: 6px;
                color: #e2e8f0;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
                margin-bottom: 4px;
            }
            QListWidget::item:selected {
                background-color: #2563eb;
                color: #ffffff;
            }
            QLabel {
                color: #cbd5e1;
            }
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton#secondary {
                background-color: #2b303c;
                color: #cbd5e1;
            }
            QPushButton#secondary:hover {
                background-color: #383e4d;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #1f232b;
                border: 1px solid #373e4d;
                border-radius: 6px;
                padding: 6px 10px;
                color: #f1f5f9;
            }
            QGroupBox {
                border: 1px solid #2d3139;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: bold;
                color: #93c5fd;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
            }
        """)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # Tab 1: Installed Pets
        self.tab_installed = QWidget()
        self._setup_installed_tab()
        self.tabs.addTab(self.tab_installed, "🐾 Installed Pets")

        # Tab 2: Sprite Uploader / Importer
        self.tab_import = QWidget()
        self._setup_import_tab()
        self.tabs.addTab(self.tab_import, "✨ Import Custom Sprite")

        main_layout.addWidget(self.tabs)

    def _setup_installed_tab(self):
        layout = QVBoxLayout(self.tab_installed)

        header = QLabel("Choose a pet companion to accompany you along the taskbar:")
        layout.addWidget(header)

        h_layout = QHBoxLayout()

        self.pets_list = QListWidget()
        self.pets_list.currentItemChanged.connect(self._on_installed_pet_selected)
        h_layout.addWidget(self.pets_list, 3)

        # Detail preview card
        detail_card = QFrame()
        detail_card.setStyleSheet("background-color: #16181d; border-radius: 8px; padding: 12px;")
        card_layout = QVBoxLayout(detail_card)

        self.installed_preview = AnimationPreviewWidget()
        card_layout.addWidget(self.installed_preview, 0, Qt.AlignmentFlag.AlignCenter)

        self.lbl_pet_name = QLabel("Name: -")
        self.lbl_pet_name.setStyleSheet("font-weight: bold; font-size: 14px; color: #60a5fa;")
        card_layout.addWidget(self.lbl_pet_name)

        self.lbl_pet_desc = QLabel("Description: -")
        self.lbl_pet_desc.setWordWrap(True)
        card_layout.addWidget(self.lbl_pet_desc)

        card_layout.addStretch()

        self.btn_activate = QPushButton("Set as Active Pet")
        self.btn_activate.clicked.connect(self._activate_selected_pet)
        card_layout.addWidget(self.btn_activate)

        h_layout.addWidget(detail_card, 2)
        layout.addLayout(h_layout)

    def _setup_import_tab(self):
        layout = QVBoxLayout(self.tab_import)

        # File Picker Header
        file_box = QHBoxLayout()
        self.lbl_file_path = QLabel("Select a sprite sheet (PNG) or animated GIF:")
        file_box.addWidget(self.lbl_file_path, 1)

        btn_browse = QPushButton("📁 Browse File...")
        btn_browse.setObjectName("secondary")
        btn_browse.clicked.connect(self._browse_sprite_file)
        file_box.addWidget(btn_browse)
        layout.addLayout(file_box)

        # Slicer Configuration & Preview Box
        body_box = QHBoxLayout()

        # Left: Slicer settings
        cfg_group = QGroupBox("Sprite Slicing & Animations")
        cfg_layout = QVBoxLayout(cfg_group)

        # Dimensions
        dim_layout = QHBoxLayout()
        dim_layout.addWidget(QLabel("Frame W:"))
        self.spin_fw = QSpinBox()
        self.spin_fw.setRange(8, 512)
        self.spin_fw.setValue(32)
        self.spin_fw.valueChanged.connect(self._update_import_preview)
        dim_layout.addWidget(self.spin_fw)

        dim_layout.addWidget(QLabel("Frame H:"))
        self.spin_fh = QSpinBox()
        self.spin_fh.setRange(8, 512)
        self.spin_fh.setValue(32)
        self.spin_fh.valueChanged.connect(self._update_import_preview)
        dim_layout.addWidget(self.spin_fh)
        cfg_layout.addLayout(dim_layout)

        # Total frames / FPS
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel("Frames to Loop:"))
        self.spin_frames = QSpinBox()
        self.spin_frames.setRange(1, 64)
        self.spin_frames.setValue(4)
        self.spin_frames.valueChanged.connect(self._update_import_preview)
        fps_layout.addWidget(self.spin_frames)

        fps_layout.addWidget(QLabel("Animation FPS:"))
        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(1, 60)
        self.spin_fps.setValue(8)
        self.spin_fps.valueChanged.connect(lambda v: self.import_preview.set_fps(v))
        fps_layout.addWidget(self.spin_fps)
        cfg_layout.addLayout(fps_layout)

        # Row selector (if sprite sheet)
        row_layout = QHBoxLayout()
        row_layout.addWidget(QLabel("Sprite Sheet Row:"))
        self.spin_row = QSpinBox()
        self.spin_row.setRange(0, 32)
        self.spin_row.setValue(0)
        self.spin_row.valueChanged.connect(self._update_import_preview)
        row_layout.addWidget(self.spin_row)
        cfg_layout.addLayout(row_layout)

        # Pet metadata
        cfg_layout.addWidget(QLabel("Pet Name:"))
        self.txt_pet_name = QLineEdit("My Custom Pet")
        cfg_layout.addWidget(self.txt_pet_name)

        cfg_layout.addWidget(QLabel("Description:"))
        self.txt_pet_desc = QLineEdit("A wonderful custom desktop companion.")
        cfg_layout.addWidget(self.txt_pet_desc)

        cfg_layout.addStretch()
        body_box.addWidget(cfg_group, 3)

        # Right: Live Animated Preview
        prev_group = QGroupBox("Live Preview")
        prev_layout = QVBoxLayout(prev_group)
        self.import_preview = AnimationPreviewWidget()
        prev_layout.addWidget(self.import_preview, 0, Qt.AlignmentFlag.AlignCenter)

        self.lbl_import_info = QLabel("Load a sprite file to begin.")
        self.lbl_import_info.setStyleSheet("color: #94a3b8; font-size: 11px;")
        prev_layout.addWidget(self.lbl_import_info, 0, Qt.AlignmentFlag.AlignCenter)
        prev_layout.addStretch()

        body_box.addWidget(prev_group, 2)
        layout.addLayout(body_box)

        # Bottom buttons
        btn_bar = QHBoxLayout()
        btn_bar.addStretch()

        self.btn_save_import = QPushButton("💾 Save & Activate Pet")
        self.btn_save_import.clicked.connect(self._save_imported_pet)
        btn_bar.addWidget(self.btn_save_import)
        layout.addLayout(btn_bar)

    def _refresh_installed_pets(self):
        """Scans pets directory for valid pets with pet.json."""
        self.pets_list.clear()
        if not self.pets_dir.exists():
            return

        for p in self.pets_dir.iterdir():
            if p.is_dir() and (p / "pet.json").exists():
                try:
                    with open(p / "pet.json", "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    name = meta.get("name", p.name)
                    item = QListWidgetItem(f"🐾 {name}")
                    item.setData(Qt.ItemDataRole.UserRole, str(p))
                    self.pets_list.addItem(item)

                    if p.resolve() == self.current_pet_dir.resolve():
                        self.pets_list.setCurrentItem(item)
                except Exception as e:
                    print(f"Error loading {p}: {e}")

        if self.pets_list.currentItem() is None and self.pets_list.count() > 0:
            self.pets_list.setCurrentRow(0)

    def _on_installed_pet_selected(self, current: Optional[QListWidgetItem]):
        if not current:
            return
        pet_path = Path(current.data(Qt.ItemDataRole.UserRole))
        config_path = pet_path / "pet.json"
        if not config_path.exists():
            return

        with open(config_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.lbl_pet_name.setText(f"Name: {meta.get('name', pet_path.name)}")
        self.lbl_pet_desc.setText(meta.get("description", "No description provided."))

        # Preview idle animation
        sheet_file = meta.get("spritesheet", "spritesheet.png")
        sheet_path = pet_path / sheet_file
        fw = meta.get("frame_width", 32)
        fh = meta.get("frame_height", 32)

        if sheet_path.exists():
            frames = []
            if sheet_path.suffix.lower() == ".gif":
                pil_img = Image.open(sheet_path)
                for frame in list(ImageSequence.Iterator(pil_img))[:8]:
                    rgba = frame.convert("RGBA")
                    qimg = QImage(rgba.tobytes("raw", "RGBA"), rgba.size[0], rgba.size[1], QImage.Format.Format_RGBA8888)
                    frames.append(QPixmap.fromImage(qimg))
                fps = 1000.0 / pil_img.info.get("duration", 120)
            else:
                pm = QPixmap(str(sheet_path))
                idle_cfg = meta.get("states", {}).get("idle", {})
                row = idle_cfg.get("row", 0)
                count = idle_cfg.get("frames", 4)
                fps = idle_cfg.get("fps", 6)
                for i in range(count):
                    frames.append(pm.copy(i * fw, row * fh, fw, fh))

            self.installed_preview.set_frames(frames, int(fps))

    def _activate_selected_pet(self):
        current = self.pets_list.currentItem()
        if not current:
            return
        pet_path = Path(current.data(Qt.ItemDataRole.UserRole))
        self.pet_selected.emit(pet_path)
        self.accept()

    def _browse_sprite_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Sprite File",
            "",
            "Images (*.png *.gif *.bmp);;All Files (*.*)"
        )
        if not file_path:
            return

        self.imported_image_path = Path(file_path)
        self.lbl_file_path.setText(f"Selected: {self.imported_image_path.name}")

        if self.imported_image_path.suffix.lower() == ".gif":
            # For GIF, auto load frames
            self.loaded_raw_pixmap = None
            self._load_gif_preview(self.imported_image_path)
        else:
            self.loaded_raw_pixmap = QPixmap(str(self.imported_image_path))
            # Auto-detect default frame sizes if divisible by 32 or 16
            w = self.loaded_raw_pixmap.width()
            h = self.loaded_raw_pixmap.height()
            if w % 32 == 0 and h % 32 == 0:
                self.spin_fw.setValue(32)
                self.spin_fh.setValue(32)
            elif w % 48 == 0 and h % 48 == 0:
                self.spin_fw.setValue(48)
                self.spin_fh.setValue(48)
            elif w % 16 == 0 and h % 16 == 0:
                self.spin_fw.setValue(16)
                self.spin_fh.setValue(16)

            self.spin_frames.setValue(max(1, w // self.spin_fw.value()))
            self._update_import_preview()

    def _load_gif_preview(self, gif_path: Path):
        pil_img = Image.open(gif_path)
        frames = []
        for frame in ImageSequence.Iterator(pil_img):
            rgba = frame.convert("RGBA")
            qimg = QImage(rgba.tobytes("raw", "RGBA"), rgba.size[0], rgba.size[1], QImage.Format.Format_RGBA8888)
            frames.append(QPixmap.fromImage(qimg))

        duration = pil_img.info.get("duration", 100)
        fps = int(1000.0 / max(10, duration))
        self.spin_fps.setValue(fps)
        self.spin_fw.setValue(pil_img.size[0])
        self.spin_fh.setValue(pil_img.size[1])
        self.spin_frames.setValue(len(frames))

        self.import_preview.set_frames(frames, fps)
        self.lbl_import_info.setText(f"Animated GIF: {len(frames)} frames ({pil_img.size[0]}x{pil_img.size[1]})")

    def _update_import_preview(self):
        if not self.loaded_raw_pixmap or self.loaded_raw_pixmap.isNull():
            return

        fw = self.spin_fw.value()
        fh = self.spin_fh.value()
        count = self.spin_frames.value()
        row = self.spin_row.value()

        frames = []
        for i in range(count):
            cx = i * fw
            cy = row * fh
            if cx + fw <= self.loaded_raw_pixmap.width() and cy + fh <= self.loaded_raw_pixmap.height():
                frames.append(self.loaded_raw_pixmap.copy(cx, cy, fw, fh))

        self.import_preview.set_frames(frames, self.spin_fps.value())
        self.lbl_import_info.setText(f"Sliced {len(frames)} frames from row {row} ({fw}x{fh})")

    def _save_imported_pet(self):
        if not self.imported_image_path or not self.imported_image_path.exists():
            QMessageBox.warning(self, "No File", "Please select a sprite file first.")
            return

        pet_name = self.txt_pet_name.text().strip() or "Custom Pet"
        sanitized_folder = re.sub(r'[^a-zA-Z0-9_\-]', '_', pet_name.lower())
        target_dir = self.pets_dir / sanitized_folder
        target_dir.mkdir(parents=True, exist_ok=True)

        target_sprite = target_dir / self.imported_image_path.name
        shutil.copy2(self.imported_image_path, target_sprite)

        fw = self.spin_fw.value()
        fh = self.spin_fh.value()
        frames_count = self.spin_frames.value()
        fps = self.spin_fps.value()
        row = self.spin_row.value()

        is_gif = self.imported_image_path.suffix.lower() == ".gif"

        # Generate pet.json
        if is_gif:
            states_dict = {
                state: {"row": 0, "frames": frames_count, "fps": fps, "loop": True, "speed": 1.0 if state in ("walk", "run") else 0.0}
                for state in ["idle", "walk", "run", "jump", "sleep", "groom", "drag", "fall"]
            }
        else:
            # Sprite sheet configuration
            states_dict = {
                "idle":  {"row": row, "frames": frames_count, "fps": max(2, fps // 2), "loop": True, "speed": 0.0},
                "walk":  {"row": row, "frames": frames_count, "fps": fps, "loop": True, "speed": 1.2},
                "run":   {"row": row, "frames": frames_count, "fps": int(fps * 1.5), "loop": True, "speed": 2.5},
                "jump":  {"row": row, "frames": frames_count, "fps": fps, "loop": False, "speed": 1.2},
                "sleep": {"row": row, "frames": max(1, frames_count // 2), "fps": 2, "loop": True, "speed": 0.0},
                "groom": {"row": row, "frames": frames_count, "fps": 4, "loop": True, "speed": 0.0},
                "drag":  {"row": row, "frames": 1, "fps": 2, "loop": True, "speed": 0.0},
                "fall":  {"row": row, "frames": 1, "fps": 4, "loop": True, "speed": 0.0}
            }

        meta = {
            "name": pet_name,
            "description": self.txt_pet_desc.text().strip() or "Custom imported desktop pet.",
            "author": "User",
            "version": "1.0",
            "frame_width": fw,
            "frame_height": fh,
            "spritesheet": self.imported_image_path.name,
            "default_scale": 2,
            "states": states_dict
        }

        with open(target_dir / "pet.json", "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        QMessageBox.information(self, "Success", f"'{pet_name}' imported successfully!")
        self._refresh_installed_pets()
        self.tabs.setCurrentIndex(0)
        self.pet_selected.emit(target_dir)
