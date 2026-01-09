"""
Batch cleanup confirmation dialog.
"""
import customtkinter as ctk
from typing import List, Callable
from pathlib import Path

from scanner import FolderInfo
from ui.dialogs import format_size


class BatchCleanupDialog(ctk.CTkToplevel):
    """Confirmation dialog for batch folder deletion."""
    
    def __init__(self, parent, selected_folders: List[FolderInfo], on_confirm: Callable[[List[FolderInfo]], None]):
        super().__init__(parent)
        
        self.selected_folders = selected_folders
        self.on_confirm = on_confirm
        self.result = False
        
        self.title("Confirm Batch Cleanup")
        self.geometry("600x500")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (500 // 2)
        self.geometry(f"+{x}+{y}")
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the dialog UI."""
        # Content frame
        content = ctk.CTkFrame(self)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ctk.CTkFrame(content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        warning_label = ctk.CTkLabel(
            header_frame,
            text="⚠️",
            font=ctk.CTkFont(size=32)
        )
        warning_label.pack(side="left", padx=(0, 10))
        
        title_text = ctk.CTkLabel(
            header_frame,
            text=f"Delete {len(self.selected_folders)} items?",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_text.pack(side="left")
        
        # Calculate totals
        total_bytes = sum(f.size_bytes for f in self.selected_folders)
        safe_count = len([f for f in self.selected_folders if f.safety == "safe"])
        caution_count = len([f for f in self.selected_folders if f.safety == "caution"])
        
        # Summary
        summary_label = ctk.CTkLabel(
            content,
            text=f"Total space to free: {format_size(total_bytes)}",
            font=ctk.CTkFont(size=16),
            text_color="#ffc107"
        )
        summary_label.pack(pady=(0, 10))
        
        if caution_count > 0:
            caution_label = ctk.CTkLabel(
                content,
                text=f"⚠️ {caution_count} items require caution. Review the list below.",
                font=ctk.CTkFont(size=12),
                text_color="#ffc107",
                wraplength=550
            )
            caution_label.pack(pady=(0, 10))
        
        # Scrollable list of items
        scroll_frame = ctk.CTkScrollableFrame(content, height=250)
        scroll_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        for folder in self.selected_folders:
            item_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=4)
            
            # Safety badge
            safety_color = "#28a745" if folder.safety == "safe" else "#ffc107"
            safety_text = "🟢 Safe" if folder.safety == "safe" else "🟡 Caution"
            
            safety_badge = ctk.CTkLabel(
                item_frame,
                text=safety_text,
                font=ctk.CTkFont(size=10),
                text_color="white",
                fg_color=safety_color,
                corner_radius=4,
                width=70,
                height=20
            )
            safety_badge.pack(side="left", padx=(0, 10))
            
            # Name and size
            name_label = ctk.CTkLabel(
                item_frame,
                text=f"{folder.name} - {format_size(folder.size_bytes)}",
                font=ctk.CTkFont(size=12),
                anchor="w"
            )
            name_label.pack(side="left", fill="x", expand=True)
        
        # Buttons
        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=120,
            fg_color="gray"
        )
        cancel_btn.pack(side="right", padx=(10, 0))
        
        confirm_btn = ctk.CTkButton(
            button_frame,
            text=f"Delete {len(self.selected_folders)} Items",
            command=self._on_confirm,
            width=180,
            fg_color="#dc3545"
        )
        confirm_btn.pack(side="right")
        
        # Focus on cancel button by default
        self.after(100, lambda: cancel_btn.focus())
    
    def _on_confirm(self):
        """Handle confirm button click."""
        self.result = True
        self.on_confirm(self.selected_folders)
        self.destroy()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = False
        self.destroy()
