"""
Card component for displaying duplicate file groups.
"""
import customtkinter as ctk
from pathlib import Path
from typing import List, Callable, Optional, Dict
from datetime import datetime

from scanner import DuplicateGroup, FileInfo
from ui.dialogs import format_size


class DuplicateGroupCard(ctk.CTkFrame):
    """Card component displaying a group of duplicate files."""
    
    def __init__(self, parent, duplicate_group: DuplicateGroup,
                 on_selection_changed: Optional[Callable[[DuplicateGroup, List[FileInfo]], None]] = None):
        super().__init__(parent, corner_radius=12, border_width=1)
        
        self.duplicate_group = duplicate_group
        self.on_selection_changed = on_selection_changed
        self.expanded = False
        self.selected_files: List[FileInfo] = []
        self.checkbox_vars: Dict[FileInfo, ctk.BooleanVar] = {}
        
        # Color based on wasted space
        wasted_space = duplicate_group.get_wasted_space()
        if wasted_space > 5 * 1024 * 1024 * 1024:  # >5GB
            self.border_color = "#dc3545"  # Red
        elif wasted_space > 1024 * 1024 * 1024:  # >1GB
            self.border_color = "#ffc107"  # Orange
        else:
            self.border_color = "#ffeb3b"  # Yellow
        
        self.configure(border_color=self.border_color)
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the card UI."""
        # Main content frame
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)
        
        # Header row
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 12))
        
        # Left: Filename and info
        left_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)
        
        name_label = ctk.CTkLabel(
            left_frame,
            text=self.duplicate_group.get_representative_name(),
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")
        
        # Info row
        info_parts = [
            f"{len(self.duplicate_group.files)} copies",
            f"{format_size(self.duplicate_group.size_bytes)} each",
            f"{format_size(self.duplicate_group.get_wasted_space())} wasted"
        ]
        info_label = ctk.CTkLabel(
            left_frame,
            text=" • ".join(info_parts),
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        info_label.pack(anchor="w", pady=(2, 0))
        
        # Right: Quick action buttons
        right_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_frame.pack(side="right")
        
        keep_newest_btn = ctk.CTkButton(
            right_frame,
            text="Keep Newest",
            command=self._keep_newest,
            width=100,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        keep_newest_btn.pack(side="right", padx=(5, 0))
        
        keep_oldest_btn = ctk.CTkButton(
            right_frame,
            text="Keep Oldest",
            command=self._keep_oldest,
            width=100,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        keep_oldest_btn.pack(side="right")
        
        # Expandable file list
        self.expand_btn = ctk.CTkButton(
            content,
            text="▼ Show all copies",
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color="#2b2b2b",
            anchor="w",
            command=self._toggle_expand,
            width=150,
            height=24
        )
        self.expand_btn.pack(anchor="w", pady=(0, 8))
        
        # File list frame (hidden initially)
        self.file_list_frame = ctk.CTkFrame(content, fg_color="#1a1a1a", corner_radius=4)
        self.file_list_frame.pack_forget()
        
        # Preview first 3 files
        self._show_preview()
    
    def _show_preview(self):
        """Show preview of first 3 files."""
        preview_count = min(3, len(self.duplicate_group.files))
        for i, file_info in enumerate(self.duplicate_group.files[:preview_count]):
            self._add_file_row(file_info, i)
        
        if len(self.duplicate_group.files) > 3:
            self.expand_btn.configure(text=f"▼ Show all {len(self.duplicate_group.files)} copies")
    
    def _toggle_expand(self):
        """Toggle expanded view showing all files."""
        if self.expanded:
            # Collapse
            self.file_list_frame.pack_forget()
            self.expand_btn.configure(text=f"▼ Show all {len(self.duplicate_group.files)} copies")
            self.expanded = False
        else:
            # Expand
            self.file_list_frame.pack(fill="x", pady=(0, 8))
            
            # Clear and rebuild file list
            for widget in self.file_list_frame.winfo_children():
                widget.destroy()
            
            for i, file_info in enumerate(self.duplicate_group.files):
                self._add_file_row(file_info, i)
            
            self.expand_btn.configure(text="▲ Hide copies")
            self.expanded = True
    
    def _add_file_row(self, file_info: FileInfo, index: int):
        """Add a file row with checkbox."""
        row_frame = ctk.CTkFrame(self.file_list_frame, fg_color="transparent")
        row_frame.pack(fill="x", padx=8, pady=4)
        
        # Checkbox
        checkbox_var = ctk.BooleanVar(value=file_info in self.selected_files)
        self.checkbox_vars[file_info] = checkbox_var
        checkbox = ctk.CTkCheckBox(
            row_frame,
            text="",
            variable=checkbox_var,
            command=lambda f=file_info, v=checkbox_var: self._on_checkbox_changed(f, v),
            width=20
        )
        checkbox.pack(side="left", padx=(0, 10))
        
        # File path
        path_label = ctk.CTkLabel(
            row_frame,
            text=str(file_info.path),
            font=ctk.CTkFont(size=11),
            anchor="w"
        )
        path_label.pack(side="left", fill="x", expand=True)
        
        # Modified date
        date_str = file_info.modified_date.strftime("%Y-%m-%d")
        date_label = ctk.CTkLabel(
            row_frame,
            text=date_str,
            font=ctk.CTkFont(size=10),
            text_color="gray",
            width=100
        )
        date_label.pack(side="right")
    
    def _on_checkbox_changed(self, file_info: FileInfo, checkbox_var: ctk.BooleanVar):
        """Handle checkbox state change."""
        if checkbox_var.get():
            if file_info not in self.selected_files:
                self.selected_files.append(file_info)
        else:
            if file_info in self.selected_files:
                self.selected_files.remove(file_info)
        
        if self.on_selection_changed:
            self.on_selection_changed(self.duplicate_group, self.selected_files)
    
    def _keep_newest(self):
        """Select all files except the newest one."""
        if not self.duplicate_group.files:
            return
        
        # Find newest file
        newest = max(self.duplicate_group.files, key=lambda f: f.modified_date)
        
        # Select all except newest
        self.selected_files = [f for f in self.duplicate_group.files if f != newest]
        
        # Update checkboxes
        self._update_checkboxes()
        
        if self.on_selection_changed:
            self.on_selection_changed(self.duplicate_group, self.selected_files)
    
    def _keep_oldest(self):
        """Select all files except the oldest one."""
        if not self.duplicate_group.files:
            return
        
        # Find oldest file
        oldest = min(self.duplicate_group.files, key=lambda f: f.modified_date)
        
        # Select all except oldest
        self.selected_files = [f for f in self.duplicate_group.files if f != oldest]
        
        # Update checkboxes
        self._update_checkboxes()
        
        if self.on_selection_changed:
            self.on_selection_changed(self.duplicate_group, self.selected_files)
    
    def _update_checkboxes(self):
        """Update checkbox states to match selected_files."""
        if not self.expanded:
            self._toggle_expand()
        
        # Update all checkbox states
        for file_info, checkbox_var in self.checkbox_vars.items():
            checkbox_var.set(file_info in self.selected_files)
    
    def get_selected_files(self) -> List[FileInfo]:
        """Get currently selected files."""
        return self.selected_files.copy()
    
    def clear_selection(self):
        """Clear all selections."""
        self.selected_files = []
        # Update checkbox states
        for checkbox_var in self.checkbox_vars.values():
            checkbox_var.set(False)
        if self.on_selection_changed:
            self.on_selection_changed(self.duplicate_group, self.selected_files)
