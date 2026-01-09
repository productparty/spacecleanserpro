"""
Main dashboard view combining visualization, filters, recommendations, and folder list.
"""
import customtkinter as ctk
import threading
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime
from tkinter import PanedWindow

from scanner import Scanner, FolderInfo
from cleaner import Cleaner
from categorizer import enhance_folder_info
from recommendations import generate_recommendations, Recommendation
from settings import Settings
from ui.disk_viz import DiskVisualization
from ui.filter_bar import FilterBar
from ui.folder_list import FolderList
from ui.batch_dialog import BatchCleanupDialog
from ui.dialogs import format_size, show_success_message


class Dashboard(ctk.CTkFrame):
    """Main dashboard view for Space Cleanser Pro."""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.scanner = Scanner()
        self.cleaner = Cleaner()
        self.settings = Settings()
        self.folders: List[FolderInfo] = []
        self.recommendations: List[Recommendation] = []
        
        self._build_ui()
        
        # Load cached results if available
        self._load_cached_results()
    
    def _build_ui(self):
        """Build the dashboard UI."""
        # Create resizable paned window
        self.paned = PanedWindow(self, orient="vertical", sashrelief="raised", 
                                 sashwidth=8, bg="#1a1a1a", bd=0)
        self.paned.pack(fill="both", expand=True)
        
        # Top pane - header section (scrollable)
        header_container = ctk.CTkFrame(self.paned, corner_radius=0)
        self.paned.add(header_container, minsize=250, height=400)
        
        # Scrollable header content
        header_scroll = ctk.CTkScrollableFrame(header_container)
        header_scroll.pack(fill="both", expand=True, padx=0, pady=0)
        
        header_content = ctk.CTkFrame(header_scroll, fg_color="transparent")
        header_content.pack(fill="x", padx=24, pady=16)
        
        # Title and subtitle
        title_label = ctk.CTkLabel(
            header_content,
            text="Space Cleanser Pro",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 8))
        
        subtitle_label = ctk.CTkLabel(
            header_content,
            text="Comprehensive disk space manager for Windows",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(anchor="w", pady=(0, 16))
        
        # Summary row
        summary_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        summary_frame.pack(fill="x")
        
        self.total_label = ctk.CTkLabel(
            summary_frame,
            text="",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#28a745"
        )
        self.total_label.pack(side="left")
        
        # Action buttons
        button_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        button_frame.pack(side="right")
        
        self.quick_clean_btn = ctk.CTkButton(
            button_frame,
            text="Quick Clean (All Safe)",
            command=self._on_quick_clean,
            width=150,
            height=32,
            fg_color="#28a745"
        )
        self.quick_clean_btn.pack(side="right", padx=(10, 0))
        
        self.scan_button = ctk.CTkButton(
            button_frame,
            text="Scan",
            command=self._start_scan,
            width=100,
            height=32
        )
        self.scan_button.pack(side="right")
        
        # Progress bar frame (hidden by default)
        self.progress_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_frame.pack_forget()
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, mode="indeterminate", height=6)
        self.progress_bar.pack(fill="x", pady=(0, 8))
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Scanning...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.progress_label.pack(anchor="w")
        
        # Completion frame
        self.completion_frame = ctk.CTkFrame(header_content, fg_color="#1a472a", corner_radius=8)
        self.completion_frame.pack(fill="x", pady=(16, 0))
        self.completion_frame.pack_forget()
        
        self.completion_label = ctk.CTkLabel(
            self.completion_frame,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4ade80",
            wraplength=800
        )
        self.completion_label.pack(pady=12, padx=16)
        
        # Disk visualization - make it smaller
        self.disk_viz = DiskVisualization(
            header_content,
            height=150,
            on_category_click=self._on_category_clicked
        )
        self.disk_viz.pack(fill="x", pady=(16, 0))
        
        # Recommendations section - limit to 1 recommendation to save space
        self.recommendations_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        self.recommendations_frame.pack(fill="x", pady=(12, 0))
        
        # Filter bar - move to main content area for better visibility
        self.filter_bar = FilterBar(self, on_filter_changed=self._on_filter_changed)
        
        # Bottom pane - main content area
        content_frame = ctk.CTkFrame(self.paned, fg_color="transparent")
        self.paned.add(content_frame, minsize=200)
        
        content_inner = ctk.CTkFrame(content_frame, fg_color="transparent")
        content_inner.pack(fill="both", expand=True, padx=24, pady=(12, 24))
        
        # Filter bar at top of content area
        self.filter_bar.pack(fill="x", pady=(0, 12))
        
        # Folder list with batch selection
        self.folder_list = FolderList(
            content_inner,
            on_clean=self._on_clean_requested,
            on_show_folder=self._on_show_folder,
            on_selection_changed=self._on_selection_changed
        )
        self.folder_list.pack(fill="both", expand=True)
        
        # Batch action bar (hidden by default)
        self.batch_bar = ctk.CTkFrame(content_inner, fg_color="#1a1a1a", corner_radius=8)
        self.batch_bar.pack(fill="x", pady=(10, 0))
        self.batch_bar.pack_forget()
        
        batch_content = ctk.CTkFrame(self.batch_bar, fg_color="transparent")
        batch_content.pack(fill="x", padx=16, pady=12)
        
        self.batch_label = ctk.CTkLabel(
            batch_content,
            text="",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.batch_label.pack(side="left")
        
        batch_btn_frame = ctk.CTkFrame(batch_content, fg_color="transparent")
        batch_btn_frame.pack(side="right")
        
        ctk.CTkButton(
            batch_btn_frame,
            text="Clear Selection",
            command=self._clear_selection,
            width=120,
            fg_color="gray"
        ).pack(side="right", padx=(10, 0))
        
        ctk.CTkButton(
            batch_btn_frame,
            text="Clean Selected",
            command=self._on_batch_clean,
            width=120,
            fg_color="#dc3545"
        ).pack(side="right")
    
    def _load_cached_results(self):
        """Load cached scan results for instant display."""
        cached = self.settings.get_cached_scan_results()
        if cached:
            # Convert cached dicts back to FolderInfo objects
            folders = []
            for item in cached:
                folder = FolderInfo(
                    key=item["key"],
                    name=item["name"],
                    path=item["path"],
                    full_path=Path(item["full_path"]),
                    size_bytes=item["size_bytes"],
                    exists=item["exists"],
                    last_modified=datetime.fromisoformat(item["last_modified"]) if item.get("last_modified") else None,
                    description=item["description"],
                    impact=item["impact"],
                    safety=item["safety"],
                    category=item.get("category", "unknown"),
                    requires_admin=item.get("requires_admin", False),
                    age_days=item.get("age_days"),
                    item_count=item.get("item_count", 0)
                )
                folders.append(folder)
            
            self.folders = folders
            self._update_display()
    
    def _start_scan(self):
        """Start scanning in background thread."""
        self.scan_button.configure(state="disabled", text="Scanning...")
        self.quick_clean_btn.configure(state="disabled")
        
        # Hide completion, show progress
        self.completion_frame.pack_forget()
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_bar.start()
        self.progress_label.configure(text="Starting scan...")
        
        # Run scan in background thread
        thread = threading.Thread(target=self._scan_thread, daemon=True)
        thread.start()
    
    def _scan_thread(self):
        """Background thread for scanning."""
        def progress_callback(folder_name: str):
            self.after(0, lambda name=folder_name: self.progress_label.configure(text=f"Scanning: {name}"))
        
        try:
            folders = self.scanner.scan(progress_callback=progress_callback)
            
            # Enhance with auto-categorization
            folders = [enhance_folder_info(f) for f in folders]
            
            self.after(0, lambda: self._on_scan_complete(folders))
        except Exception as e:
            self.after(0, lambda: self._on_scan_error(str(e)))
    
    def _on_scan_complete(self, folders: List[FolderInfo]):
        """Handle scan completion."""
        self.folders = folders
        
        # Stop and hide progress bar
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        # Cache results
        self.settings.cache_scan_results(folders)
        
        # Generate recommendations
        self.recommendations = generate_recommendations(folders)
        
        # Update display
        self._update_display()
        
        # Show completion message
        total_bytes = self.scanner.get_total_reclaimable(folders)
        found_count = len([f for f in folders if f.exists])
        
        self.completion_label.configure(
            text=f"✓ Scan complete! Found {found_count} cache folders. You can safely free {format_size(total_bytes)}."
        )
        self.completion_frame.configure(fg_color="#1a472a")
        self.completion_label.configure(text_color="#4ade80")
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        # Update UI state
        self.scan_button.configure(state="normal", text="Scan")
        self.quick_clean_btn.configure(state="normal")
    
    def _on_scan_error(self, error_msg: str):
        """Handle scan error."""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        self.completion_label.configure(text=f"✗ Error: {error_msg}")
        self.completion_frame.configure(fg_color="#4a1a1a")
        self.completion_label.configure(text_color="#dc3545")
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        self.scan_button.configure(state="normal", text="Scan")
        self.quick_clean_btn.configure(state="normal")
    
    def _update_display(self):
        """Update all display components with current data."""
        # Update disk visualization (estimate disk space - would need actual disk info)
        total_bytes = sum(f.size_bytes for f in self.folders if f.exists)
        self.disk_viz.update_data(self.folders, total_space_gb=100, free_space_gb=0)
        
        # Update total reclaimable
        reclaimable = self.scanner.get_total_reclaimable(self.folders)
        self.total_label.configure(text=f"Reclaimable: {format_size(reclaimable)}")
        
        # Update recommendations
        self._update_recommendations()
        
        # Update folder list
        self.folder_list.set_folders(self.folders)
        self.folder_list.apply_filters(self.filter_bar.get_filters())
    
    def _update_recommendations(self):
        """Update recommendations display."""
        # Clear existing recommendations
        for widget in self.recommendations_frame.winfo_children():
            widget.destroy()
        
        if not self.recommendations:
            return
        
        # Show recommendations - limit to 1 to save space
        for rec in self.recommendations[:1]:  # Show top 1
            rec_frame = ctk.CTkFrame(self.recommendations_frame, fg_color="#1a1a1a", corner_radius=8)
            rec_frame.pack(fill="x", pady=(0, 12))
            
            title_label = ctk.CTkLabel(
                rec_frame,
                text=f"{rec.icon} {rec.title}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            title_label.pack(anchor="w", padx=16, pady=(12, 8))
            
            for item in rec.items[:3]:  # Show top 3 items
                item_label = ctk.CTkLabel(
                    rec_frame,
                    text=f"  • {item.name}: {format_size(item.size_bytes)}",
                    font=ctk.CTkFont(size=12),
                    anchor="w"
                )
                item_label.pack(anchor="w", padx=32, pady=2)
            
            hint_label = ctk.CTkLabel(
                rec_frame,
                text=rec.action_hint,
                font=ctk.CTkFont(size=11),
                text_color="gray",
                anchor="w"
            )
            hint_label.pack(anchor="w", padx=16, pady=(8, 12))
    
    def _on_filter_changed(self, filters: Dict):
        """Handle filter changes."""
        self.folder_list.apply_filters(filters)
        self.settings.set_filters(**filters)
    
    def _on_category_clicked(self, category: str):
        """Handle category click in visualization."""
        self.filter_bar.category_var.set(category if category != "free" else "all")
        self.filter_bar._on_category_changed()
    
    def _on_clean_requested(self, folder_info: FolderInfo):
        """Handle single folder clean request."""
        from ui.dialogs import ConfirmationDialog
        
        def confirm_delete():
            self._delete_folder(folder_info)
        
        dialog = ConfirmationDialog(
            self,
            folder_info.name,
            str(folder_info.full_path),
            folder_info.size_bytes,
            folder_info.impact,
            folder_info.safety,
            confirm_delete
        )
    
    def _on_batch_clean(self):
        """Handle batch clean request."""
        selected = self.folder_list.get_selected_folders()
        if not selected:
            return
        
        def confirm_batch(folders: List[FolderInfo]):
            self._delete_folders_batch(folders)
        
        dialog = BatchCleanupDialog(self, selected, confirm_batch)
    
    def _on_quick_clean(self):
        """Handle quick clean (all safe items)."""
        safe_folders = self.scanner.get_safe_folders(self.folders)
        if not safe_folders:
            return
        
        def confirm_batch(folders: List[FolderInfo]):
            self._delete_folders_batch(folders)
        
        dialog = BatchCleanupDialog(self, safe_folders, confirm_batch)
    
    def _delete_folder(self, folder_info: FolderInfo):
        """Delete a single folder."""
        self.completion_frame.pack_forget()
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_bar.start()
        self.progress_label.configure(text=f"Deleting {folder_info.name}...")
        
        def delete_thread():
            success, error_msg, bytes_freed = self.cleaner.delete_folder(folder_info.full_path)
            
            if success:
                self.after(0, lambda: self._on_delete_success(folder_info, bytes_freed))
            else:
                self.after(0, lambda: self._on_delete_error(error_msg))
        
        thread = threading.Thread(target=delete_thread, daemon=True)
        thread.start()
    
    def _delete_folders_batch(self, folders: List[FolderInfo]):
        """Delete multiple folders in batch."""
        self.completion_frame.pack_forget()
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_bar.start()
        self.progress_label.configure(text=f"Deleting {len(folders)} items...")
        
        def delete_thread():
            def progress_callback(folder, completed, total):
                self.after(0, lambda: self.progress_label.configure(
                    text=f"Deleting {folder.name}... ({completed}/{total})"
                ))
            
            results = self.cleaner.delete_folders_batch(folders, progress_callback)
            self.after(0, lambda: self._on_batch_delete_complete(results))
        
        thread = threading.Thread(target=delete_thread, daemon=True)
        thread.start()
    
    def _on_delete_success(self, folder_info: FolderInfo, bytes_freed: int):
        """Handle successful deletion."""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        show_success_message(self, bytes_freed)
        
        self.completion_label.configure(
            text=f"✓ Cleaned {folder_info.name}! Freed {format_size(bytes_freed)}"
        )
        self.completion_frame.configure(fg_color="#1a472a")
        self.completion_label.configure(text_color="#4ade80")
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        # Refresh scan
        self.after(1500, self._start_scan)
    
    def _on_batch_delete_complete(self, results: dict):
        """Handle batch deletion completion."""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        total_freed = format_size(results["total_bytes_freed"])
        success_msg = f"✓ Cleaned {results['success_count']} items! Freed {total_freed}"
        
        if results["failed_count"] > 0:
            success_msg += f" ({results['failed_count']} failed)"
        
        self.completion_label.configure(text=success_msg)
        self.completion_frame.configure(fg_color="#1a472a")
        self.completion_label.configure(text_color="#4ade80")
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        # Clear selection and refresh
        self._clear_selection()
        self.after(1500, self._start_scan)
    
    def _on_delete_error(self, error_msg: str):
        """Handle deletion error."""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
        
        self.completion_label.configure(text=f"✗ Error: {error_msg}")
        self.completion_frame.configure(fg_color="#4a1a1a")
        self.completion_label.configure(text_color="#dc3545")
        self.completion_frame.pack(fill="x", pady=(16, 0))
    
    def _on_show_folder(self, folder_info: FolderInfo):
        """Open folder in File Explorer."""
        self.cleaner.open_in_explorer(folder_info.full_path)
    
    def _on_selection_changed(self, selected_folders: List[FolderInfo]):
        """Handle folder selection changes."""
        if selected_folders:
            total_bytes = sum(f.size_bytes for f in selected_folders)
            self.batch_label.configure(
                text=f"{len(selected_folders)} items selected ({format_size(total_bytes)})"
            )
            self.batch_bar.pack(fill="x", pady=(10, 0))
        else:
            self.batch_bar.pack_forget()
    
    def _clear_selection(self):
        """Clear all selections."""
        self.folder_list.clear_selection()
