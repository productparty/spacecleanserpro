"""
Card component for displaying large files.
"""
import customtkinter as ctk
from pathlib import Path
from typing import Callable
from datetime import datetime

from scanner import LargeFileInfo
from ui.dialogs import format_size


class LargeFileCard(ctk.CTkFrame):
    """Card component displaying a single large file."""
    
    # File type icons (using emoji for simplicity)
    FILE_TYPE_ICONS = {
        "video": "🎬",
        "installer": "📦",
        "archive": "📁",
        "image": "🖼️",
        "document": "📄",
        "other": "📎"
    }
    
    # File type colors
    FILE_TYPE_COLORS = {
        "video": "#e74c3c",
        "installer": "#3498db",
        "archive": "#95a5a6",
        "image": "#e67e22",
        "document": "#2ecc71",
        "other": "#9b59b6"
    }
    
    def __init__(self, parent, large_file: LargeFileInfo,
                 on_delete: Callable[[LargeFileInfo], None],
                 on_move: Callable[[LargeFileInfo], None],
                 on_open_location: Callable[[Path], None]):
        super().__init__(parent, corner_radius=12, border_width=1)
        
        self.large_file = large_file
        self.on_delete = on_delete
        self.on_move = on_move
        self.on_open_location = on_open_location
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the card UI."""
        # Main content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Top row: Icon, Name, Size
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 12))
        
        # File type icon (40px equivalent)
        icon_label = ctk.CTkLabel(
            top_row,
            text=self.FILE_TYPE_ICONS.get(self.large_file.file_type, "📎"),
            font=ctk.CTkFont(size=32),
            width=50
        )
        icon_label.pack(side="left", padx=(0, 12))
        
        # Left: Filename and path
        left_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)
        
        name_label = ctk.CTkLabel(
            left_frame,
            text=self.large_file.path.name,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        path_label = ctk.CTkLabel(
            left_frame,
            text=str(self.large_file.path.parent),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        path_label.pack(anchor="w", pady=(2, 0))
        
        # Right: Size badge
        size_color = self._get_size_color(self.large_file.size_bytes)
        size_badge = ctk.CTkLabel(
            top_row,
            text=format_size(self.large_file.size_bytes),
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white",
            fg_color=size_color,
            corner_radius=4,
            width=90,
            height=32
        )
        size_badge.pack(side="right", padx=(10, 0))
        
        # Metadata row
        meta_frame = ctk.CTkFrame(content, fg_color="transparent")
        meta_frame.pack(fill="x", pady=(0, 12))
        
        meta_parts = []
        
        # File type
        type_name = self.large_file.file_type.title()
        meta_parts.append(f"Type: {type_name}")
        
        # Age
        if self.large_file.age_days >= 365:
            age_str = f"{self.large_file.age_days // 365} year(s) old"
        elif self.large_file.age_days >= 30:
            age_str = f"{self.large_file.age_days // 30} month(s) old"
        else:
            age_str = f"{self.large_file.age_days} day(s) old"
        
        meta_parts.append(age_str)
        
        # Modified date
        date_str = self.large_file.modified_date.strftime("%Y-%m-%d")
        meta_parts.append(f"Modified: {date_str}")
        
        meta_label = ctk.CTkLabel(
            meta_frame,
            text=" • ".join(meta_parts),
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        )
        meta_label.pack(anchor="w")
        
        # Highlight old files (>180 days)
        if self.large_file.age_days > 180:
            old_indicator = ctk.CTkLabel(
                meta_frame,
                text="⚠️ Old file - consider archiving or deleting",
                font=ctk.CTkFont(size=10),
                text_color="#ffc107",
                anchor="w"
            )
            old_indicator.pack(anchor="w", pady=(2, 0))
        
        # Action buttons
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # Open location button
        open_btn = ctk.CTkButton(
            button_frame,
            text="Open Location",
            command=lambda: self.on_open_location(self.large_file.path),
            width=120,
            fg_color="gray"
        )
        open_btn.pack(side="right", padx=(10, 0))
        
        # Move button
        move_btn = ctk.CTkButton(
            button_frame,
            text="Move",
            command=lambda: self.on_move(self.large_file),
            width=100,
            fg_color="#28a745"
        )
        move_btn.pack(side="right", padx=(5, 0))
        
        # Delete button
        delete_btn = ctk.CTkButton(
            button_frame,
            text="Delete",
            command=lambda: self.on_delete(self.large_file),
            width=100,
            fg_color="#dc3545"
        )
        delete_btn.pack(side="right")
    
    def _get_size_color(self, bytes_size: int) -> str:
        """Get color for size badge based on size."""
        gb = bytes_size / (1024 ** 3)
        if gb < 1:
            return "#28a745"  # Green
        elif gb < 5:
            return "#ffc107"  # Yellow
        else:
            return "#dc3545"  # Red
