"""
Main application window for Dev Cache Cleaner.
"""
import customtkinter as ctk
import threading
from pathlib import Path
from typing import List, Optional

from scanner import Scanner, FolderInfo
from cleaner import Cleaner
from ui.folder_card import FolderCard
from ui.dialogs import ConfirmationDialog, show_success_message, format_size


class DevCacheCleanerApp(ctk.CTk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Set appearance mode and color theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize components
        self.scanner = Scanner()
        self.cleaner = Cleaner()
        self.folders: List[FolderInfo] = []
        
        # Configure window
        self.title("Dev Cache Cleaner")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        self._build_ui()
        
        # Auto-scan on startup
        self.after(100, self._start_scan)
    
    def _build_ui(self):
        """Build the main UI."""
        # Header frame
        header = ctk.CTkFrame(self, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=24, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            header_content,
            text="Dev Cache Cleaner",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 8))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_content,
            text="Identify and safely clean up development tool caches",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(anchor="w", pady=(0, 16))
        
        # Summary row
        summary_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        summary_frame.pack(fill="x")
        
        # Total reclaimable space
        self.total_label = ctk.CTkLabel(
            summary_frame,
            text="",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#28a745"
        )
        self.total_label.pack(side="left")
        
        # Scan button
        self.scan_button = ctk.CTkButton(
            summary_frame,
            text="Scan",
            command=self._start_scan,
            width=100,
            height=32
        )
        self.scan_button.pack(side="right")
        
        # Progress bar frame (hidden by default)
        self.progress_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_frame.pack_forget()  # Hide initially
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, mode="indeterminate", height=6)
        self.progress_bar.pack(fill="x", pady=(0, 8))
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Scanning...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.progress_label.pack(anchor="w")
        
        # Completion status frame (hidden by default)
        self.completion_frame = ctk.CTkFrame(header_content, fg_color="#1a472a", corner_radius=8)
        self.completion_frame.pack(fill="x", pady=(16, 0))
        self.completion_frame.pack_forget()  # Hide initially
        
        self.completion_label = ctk.CTkLabel(
            self.completion_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#28a745",
            wraplength=800  # Wrap long messages
        )
        self.completion_label.pack(pady=12, padx=16)
        
        # Main content area with scrollable frame
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))
    
    def _start_scan(self):
        """Start scanning in background thread."""
        self.scan_button.configure(state="disabled", text="Scanning...")
        self.total_label.configure(text="")
        
        # Hide completion, show progress
        self.completion_frame.pack_forget()
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_bar.start()
        self.progress_label.configure(text="Starting scan...")
        
        # Clear existing cards
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Run scan in background thread
        thread = threading.Thread(target=self._scan_thread, daemon=True)
        thread.start()
    
    def _scan_thread(self):
        """Background thread for scanning."""
        def progress_callback(folder_name: str):
            self.after(0, lambda name=folder_name: self.progress_label.configure(text=f"Scanning: {name}"))
        
        try:
            folders = self.scanner.scan(progress_callback=progress_callback)
            self.after(0, lambda: self._on_scan_complete(folders))
        except Exception as e:
            self.after(0, lambda: self._on_scan_error(str(e)))
    
    def _on_scan_complete(self, folders: List[FolderInfo]):
        """Handle scan completion."""
        self.folders = folders
        
        # Stop and hide progress bar
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        # Calculate totals
        total_bytes = self.scanner.get_total_reclaimable(folders)
        found_count = len([f for f in folders if f.exists])
        
        # Update header with reclaimable amount
        self.total_label.configure(text=f"Reclaimable: {format_size(total_bytes)}")
        
        # Reset completion frame to success style and show message
        self.completion_frame.configure(fg_color="#1a472a")
        self.completion_label.configure(
            text=f"✓ Scan complete! Found {found_count} cache folders. You can safely free {format_size(total_bytes)}.",
            text_color="#4ade80"
        )
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        # Create folder cards
        for folder_info in folders:
            card = FolderCard(
                self.scrollable_frame,
                folder_info,
                on_clean=self._on_clean_requested,
                on_show_folder=self._on_show_folder
            )
            card.pack(fill="x", pady=(0, 12))
        
        # Update UI state
        self.scan_button.configure(state="normal", text="Scan")
    
    def _on_scan_error(self, error_msg: str):
        """Handle scan error."""
        # Stop and hide progress bar
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        # Show error in completion frame
        self.completion_label.configure(text=f"✗ Error: {error_msg}")
        self.completion_frame.configure(fg_color="#4a1a1a")
        self.completion_label.configure(text_color="#dc3545")
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        self.scan_button.configure(state="normal", text="Scan")
    
    def _on_clean_requested(self, folder_info: FolderInfo):
        """Handle clean button click."""
        def confirm_delete():
            self._delete_folder(folder_info)
        
        # Show confirmation dialog
        dialog = ConfirmationDialog(
            self,
            folder_info.name,
            str(folder_info.full_path),
            folder_info.size_bytes,
            folder_info.impact,
            folder_info.safety,
            confirm_delete
        )
    
    def _delete_folder(self, folder_info: FolderInfo):
        """Delete a folder."""
        # Show deleting progress
        self.completion_frame.pack_forget()
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_bar.start()
        self.progress_label.configure(text=f"Deleting {folder_info.name}...")
        
        # Run deletion in background thread
        def delete_thread():
            success, error_msg, bytes_freed = self.cleaner.delete_folder(folder_info.full_path)
            
            if success:
                self.after(0, lambda: self._on_delete_success(folder_info, bytes_freed))
            else:
                self.after(0, lambda: self._on_delete_error(error_msg))
        
        thread = threading.Thread(target=delete_thread, daemon=True)
        thread.start()
    
    def _on_delete_success(self, folder_info: FolderInfo, bytes_freed: int):
        """Handle successful deletion."""
        # Stop progress bar
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        show_success_message(self, bytes_freed)
        
        # Show success in completion frame
        self.completion_label.configure(
            text=f"✓ Cleaned {folder_info.name}! Freed {format_size(bytes_freed)}"
        )
        self.completion_frame.configure(fg_color="#1a472a")
        self.completion_label.configure(text_color="#28a745")
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        # Refresh scan after a short delay
        self.after(1500, self._start_scan)
    
    def _on_delete_error(self, error_msg: str):
        """Handle deletion error."""
        # Stop progress bar
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        # Show error in completion frame
        self.completion_label.configure(text=f"✗ Error: {error_msg}")
        self.completion_frame.configure(fg_color="#4a1a1a")
        self.completion_label.configure(text_color="#dc3545")
        self.completion_frame.pack(fill="x", pady=(16, 0))
    
    def _on_show_folder(self, folder_path: Path):
        """Open folder in File Explorer."""
        self.cleaner.open_in_explorer(folder_path)
