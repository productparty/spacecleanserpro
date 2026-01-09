"""
Dialog components for confirmations and feedback.
"""
import customtkinter as ctk
from typing import Optional, Callable


def format_size(bytes_size: int) -> str:
    """Format bytes to human-readable size string."""
    if bytes_size == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


class ConfirmationDialog(ctk.CTkToplevel):
    """Confirmation dialog for folder deletion."""
    
    def __init__(self, parent, folder_name: str, folder_path: str, 
                 size_bytes: int, impact: str, safety: str, 
                 on_confirm: Callable[[], None]):
        super().__init__(parent)
        
        self.on_confirm = on_confirm
        self.result = False
        
        self.title("Confirm Deletion")
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
            text=f"Delete {folder_name}?",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_text.pack(side="left")
        
        # Size info
        size_label = ctk.CTkLabel(
            content,
            text=f"Size: {format_size(size_bytes)}",
            font=ctk.CTkFont(size=16),
            text_color="#ffc107"
        )
        size_label.pack(pady=(0, 10))
        
        # Impact description
        impact_label = ctk.CTkLabel(
            content,
            text=impact,
            font=ctk.CTkFont(size=14),
            wraplength=450,
            justify="left"
        )
        impact_label.pack(pady=(0, 20))
        
        # Path info
        path_label = ctk.CTkLabel(
            content,
            text=f"Path: {folder_path}",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            wraplength=450
        )
        path_label.pack(pady=(0, 20))
        
        # Safety warning for caution items
        if safety == "caution":
            caution_frame = ctk.CTkFrame(content, fg_color="#fff3cd", corner_radius=5)
            caution_frame.pack(fill="x", pady=(0, 20))
            caution_text = ctk.CTkLabel(
                caution_frame,
                text="⚠️ This action requires caution. Make sure you understand the impact.",
                font=ctk.CTkFont(size=12),
                text_color="#856404",
                wraplength=430
            )
            caution_text.pack(padx=10, pady=10)
        
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


def show_success_message(parent, bytes_freed: int):
    """Show a success toast message."""
    # Create a simple top-level window as toast
    toast = ctk.CTkToplevel(parent)
    toast.title("")
    toast.geometry("300x100")
    toast.overrideredirect(True)  # Remove window decorations
    
    # Center on parent
    toast.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - 150
    y = parent.winfo_y() + (parent.winfo_height() // 2) - 50
    toast.geometry(f"+{x}+{y}")
    
    frame = ctk.CTkFrame(toast, fg_color="#28a745")
    frame.pack(fill="both", expand=True)
    
    message = ctk.CTkLabel(
        frame,
        text=f"✓ Freed {format_size(bytes_freed)}",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color="white"
    )
    message.pack(expand=True)
    
    # Auto-close after 2 seconds
    toast.after(2000, toast.destroy)
