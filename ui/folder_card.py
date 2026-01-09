"""
Enhanced folder card component with checkboxes and expandable details.
"""
import customtkinter as ctk
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime

from scanner import FolderInfo
from ui.dialogs import format_size


class FolderCard(ctk.CTkFrame):
    """Card component displaying a single cache folder with batch selection."""
    
    def __init__(self, parent, folder_info: FolderInfo, 
                 on_clean: Callable[[FolderInfo], None],
                 on_show_folder: Callable[[FolderInfo], None],
                 on_selection_changed: Optional[Callable[[FolderInfo, bool], None]] = None):
        super().__init__(parent, corner_radius=8, border_width=1)
        
        self.folder_info = folder_info
        self.on_clean = on_clean
        self.on_show_folder = on_show_folder
        self.on_selection_changed = on_selection_changed
        self.expanded = False
        self.selected = False
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the card UI."""
        # Main content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Top row: Checkbox, Name, Size, Safety badge
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 12))
        
        # Checkbox (only for safe/caution items)
        if self.folder_info.exists and self.folder_info.safety in ["safe", "caution"]:
            self.checkbox_var = ctk.BooleanVar(value=False)
            self.checkbox = ctk.CTkCheckBox(
                top_row,
                text="",
                variable=self.checkbox_var,
                command=self._on_checkbox_changed,
                width=20
            )
            self.checkbox.pack(side="left", padx=(0, 12))
        
        # Left: Name and path
        left_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)
        
        name_label = ctk.CTkLabel(
            left_frame,
            text=self.folder_info.name,
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        path_label = ctk.CTkLabel(
            left_frame,
            text=self.folder_info.path,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        path_label.pack(anchor="w", pady=(2, 0))
        
        # Right: Category badge, Size badge, Safety badge
        right_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        right_frame.pack(side="right")
        
        # Category badge
        category_name = self.folder_info.category.replace("_", " ").title() if self.folder_info.category else "Unknown"
        category_badge = ctk.CTkLabel(
            right_frame,
            text=category_name,
            font=ctk.CTkFont(size=10),
            text_color="white",
            fg_color="#4b5563",
            corner_radius=4,
            width=80,
            height=22
        )
        category_badge.pack(side="right", padx=(10, 0))
        
        # Size badge with color coding
        size_color = self._get_size_color(self.folder_info.size_bytes)
        size_text = format_size(self.folder_info.size_bytes) if self.folder_info.exists else "Not found"
        
        size_badge = ctk.CTkLabel(
            right_frame,
            text=size_text,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white",
            fg_color=size_color,
            corner_radius=4,
            width=80,
            height=28
        )
        size_badge.pack(side="right", padx=(10, 0))
        
        # Safety badge
        safety_color, safety_text = self._get_safety_info(self.folder_info.safety)
        safety_badge = ctk.CTkLabel(
            right_frame,
            text=safety_text,
            font=ctk.CTkFont(size=12),
            text_color="white",
            fg_color=safety_color,
            corner_radius=4,
            width=70,
            height=28
        )
        safety_badge.pack(side="right")
        
        # Description
        self.description_label = ctk.CTkLabel(
            content,
            text=self.folder_info.description,
            font=ctk.CTkFont(size=13),
            wraplength=600,
            justify="left",
            anchor="w"
        )
        self.description_label.pack(fill="x", pady=(0, 8))
        
        # Expandable "Why this matters" section
        self.details_frame = None
        if self.folder_info.impact:
            expand_btn = ctk.CTkButton(
                content,
                text="▼ Why this matters",
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                hover_color="#2b2b2b",
                anchor="w",
                command=self._toggle_details,
                width=150,
                height=24
            )
            expand_btn.pack(anchor="w", pady=(0, 8))
        
        # Metadata row: Last modified, age, item count
        meta_frame = ctk.CTkFrame(content, fg_color="transparent")
        meta_frame.pack(fill="x", pady=(0, 12))
        
        meta_parts = []
        if self.folder_info.last_modified:
            date_str = self.folder_info.last_modified.strftime("%Y-%m-%d %H:%M")
            meta_parts.append(f"Last used: {date_str}")
        
        if self.folder_info.age_days is not None:
            meta_parts.append(f"Age: {self.folder_info.age_days} days")
        
        if self.folder_info.item_count > 0:
            meta_parts.append(f"{self.folder_info.item_count:,} items")
        
        if meta_parts:
            meta_label = ctk.CTkLabel(
                meta_frame,
                text=" • ".join(meta_parts),
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w"
            )
            meta_label.pack(anchor="w")
        
        # Action buttons
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # Show in Folder button (always available if folder exists)
        if self.folder_info.exists:
            show_btn = ctk.CTkButton(
                button_frame,
                text="Show in Folder",
                command=lambda: self.on_show_folder(self.folder_info),
                width=120,
                fg_color="gray"
            )
            show_btn.pack(side="right", padx=(10, 0))
        
        # Clean button (only for safe/caution items that exist)
        if self.folder_info.exists and self.folder_info.safety in ["safe", "caution"]:
            clean_btn = ctk.CTkButton(
                button_frame,
                text="Clean",
                command=lambda: self.on_clean(self.folder_info),
                width=120,
                fg_color="#dc3545" if self.folder_info.safety == "caution" else "#28a745"
            )
            clean_btn.pack(side="right")
        elif self.folder_info.safety == "keep":
            keep_label = ctk.CTkLabel(
                button_frame,
                text="Not recommended to delete",
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            keep_label.pack(side="right")
    
    def _toggle_details(self):
        """Toggle expandable details section."""
        if self.details_frame is None:
            # Create details frame
            self.details_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=4)
            self.details_frame.pack(fill="x", padx=16, pady=(0, 16))
            
            impact_label = ctk.CTkLabel(
                self.details_frame,
                text=self.folder_info.impact,
                font=ctk.CTkFont(size=12),
                wraplength=600,
                justify="left",
                anchor="w"
            )
            impact_label.pack(padx=12, pady=12, anchor="w")
            
            self.expanded = True
        else:
            self.details_frame.destroy()
            self.details_frame = None
            self.expanded = False
    
    def _on_checkbox_changed(self):
        """Handle checkbox state change."""
        self.selected = self.checkbox_var.get()
        if self.on_selection_changed:
            self.on_selection_changed(self.folder_info, self.selected)
    
    def set_selected(self, selected: bool):
        """Set checkbox state programmatically."""
        if hasattr(self, 'checkbox_var'):
            self.checkbox_var.set(selected)
            self.selected = selected
    
    def _get_size_color(self, bytes_size: int) -> str:
        """Get color for size badge based on size."""
        gb = bytes_size / (1024 ** 3)
        if gb < 5:
            return "#28a745"  # Green
        elif gb < 20:
            return "#ffc107"  # Yellow
        else:
            return "#dc3545"  # Red
    
    def _get_safety_info(self, safety: str) -> tuple:
        """Get color and text for safety badge."""
        if safety == "safe":
            return "#28a745", "🟢 Safe"
        elif safety == "caution":
            return "#ffc107", "🟡 Caution"
        else:
            return "#dc3545", "🔴 Keep"
