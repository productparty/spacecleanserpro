"""
Dialog components for file actions (delete, move) in Discovery tab.
"""
import customtkinter as ctk
import tkinter.filedialog as filedialog
from typing import Callable, List, Optional
from pathlib import Path

from scanner import FileInfo, LargeFileInfo
from ui.dialogs import format_size


class DeleteConfirmationDialog(ctk.CTkToplevel):
    """Confirmation dialog for deleting duplicate files or large files."""
    
    def __init__(self, parent, files: List[Path], total_bytes: int, 
                 on_confirm: Callable[[], None]):
        super().__init__(parent)
        
        self.on_confirm = on_confirm
        self.result = False
        
        self.title("Confirm Deletion")
        self.geometry("600x400")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (600 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (400 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Content frame
        content = ctk.CTkFrame(self)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Warning icon and title
        title_frame = ctk.CTkFrame(content, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))
        
        warning_label = ctk.CTkLabel(
            title_frame,
            text="⚠️",
            font=ctk.CTkFont(size=32)
        )
        warning_label.pack(side="left", padx=(0, 10))
        
        title_text = ctk.CTkLabel(
            title_frame,
            text=f"Delete {len(files)} file(s)?",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_text.pack(side="left")
        
        # Size info
        size_label = ctk.CTkLabel(
            content,
            text=f"Total size: {format_size(total_bytes)}",
            font=ctk.CTkFont(size=16),
            text_color="#ffc107"
        )
        size_label.pack(pady=(0, 10))
        
        # Impact summary
        impact_label = ctk.CTkLabel(
            content,
            text=f"This will free {format_size(total_bytes)} of disk space.",
            font=ctk.CTkFont(size=14),
            wraplength=550,
            justify="left"
        )
        impact_label.pack(pady=(0, 10))
        
        # File list (scrollable)
        scroll_frame = ctk.CTkScrollableFrame(content, height=150)
        scroll_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        for file_path in files[:20]:  # Show first 20 files
            file_label = ctk.CTkLabel(
                scroll_frame,
                text=str(file_path),
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w"
            )
            file_label.pack(fill="x", padx=5, pady=2)
        
        if len(files) > 20:
            more_label = ctk.CTkLabel(
                scroll_frame,
                text=f"... and {len(files) - 20} more files",
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w"
            )
            more_label.pack(fill="x", padx=5, pady=2)
        
        # Warning
        warning_frame = ctk.CTkFrame(content, fg_color="#fff3cd", corner_radius=5)
        warning_frame.pack(fill="x", pady=(0, 20))
        warning_text = ctk.CTkLabel(
            warning_frame,
            text="⚠️ This action cannot be undone. Files will be permanently deleted.",
            font=ctk.CTkFont(size=12),
            text_color="#856404",
            wraplength=550
        )
        warning_text.pack(padx=10, pady=10)
        
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
            text="Delete",
            command=self._on_confirm,
            width=120,
            fg_color="#dc3545"
        )
        confirm_btn.pack(side="right")
        
        # Focus on cancel button by default
        self.after(100, lambda: cancel_btn.focus())
    
    def _on_confirm(self):
        """Handle confirm button click."""
        self.result = True
        self.on_confirm()
        self.destroy()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = False
        self.destroy()


class MoveDestinationDialog(ctk.CTkToplevel):
    """Dialog for selecting destination folder for moving files."""
    
    def __init__(self, parent, file_path: Path, on_confirm: Callable[[Path], None]):
        super().__init__(parent)
        
        self.on_confirm = on_confirm
        self.destination_path: Optional[Path] = None
        
        self.title("Select Destination")
        self.geometry("500x300")
        self.resizable(False, False)
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (500 // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (300 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Content frame
        content = ctk.CTkFrame(self)
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            content,
            text="Move File",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # File info
        file_label = ctk.CTkLabel(
            content,
            text=f"File: {file_path.name}",
            font=ctk.CTkFont(size=14),
            wraplength=450
        )
        file_label.pack(pady=(0, 20))
        
        # Destination selection
        dest_frame = ctk.CTkFrame(content, fg_color="transparent")
        dest_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            dest_frame,
            text="Destination folder:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        self.dest_label = ctk.CTkLabel(
            dest_frame,
            text="(Not selected)",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w"
        )
        self.dest_label.pack(fill="x", pady=(0, 10))
        
        browse_btn = ctk.CTkButton(
            dest_frame,
            text="Browse...",
            command=self._browse_folder,
            width=120
        )
        browse_btn.pack(side="left")
        
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
        
        self.confirm_btn = ctk.CTkButton(
            button_frame,
            text="Move",
            command=self._on_confirm,
            width=120,
            fg_color="#28a745",
            state="disabled"
        )
        self.confirm_btn.pack(side="right")
        
        # Focus on browse button
        self.after(100, lambda: browse_btn.focus())
    
    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(title="Select destination folder")
        if folder:
            self.destination_path = Path(folder)
            self.dest_label.configure(
                text=str(self.destination_path),
                text_color="white"
            )
            self.confirm_btn.configure(state="normal")
    
    def _on_confirm(self):
        """Handle confirm button click."""
        if self.destination_path:
            self.on_confirm(self.destination_path)
            self.destroy()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.destroy()
