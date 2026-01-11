"""
Discovery panel for duplicate file detection and large file finding.
"""
import customtkinter as ctk
import threading
from pathlib import Path
from typing import List, Optional, Dict
from tkinter import PanedWindow

from scanner import DiscoveryScanner, DuplicateGroup, LargeFileInfo, FileInfo
from cleaner import Cleaner
from ui.duplicate_card import DuplicateGroupCard
from ui.large_file_card import LargeFileCard
from ui.file_action_dialog import DeleteConfirmationDialog, MoveDestinationDialog
from ui.dialogs import format_size


class DiscoveryPanel(ctk.CTkFrame):
    """Main discovery panel with duplicate finder and large file finder."""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        self.scanner = DiscoveryScanner()
        self.cleaner = Cleaner()
        self.duplicate_groups: List[DuplicateGroup] = []
        self.large_files: List[LargeFileInfo] = []
        self.selected_duplicate_files: Dict[DuplicateGroup, List[FileInfo]] = {}
        self.selected_large_files: List[LargeFileInfo] = []
        self.duplicate_cancel_event = threading.Event()
        self.large_file_cancel_event = threading.Event()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the discovery panel UI."""
        # Header section
        header = ctk.CTkFrame(self, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=24, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            header_content,
            text="Discovery - Find Hidden Space Hogs",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 8))
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            header_content,
            text="Find duplicate files and large files across your C: drive",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle_label.pack(anchor="w", pady=(0, 16))
        
        # Scan controls
        controls_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 16))
        
        # Scan buttons
        button_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        button_frame.pack(side="left")
        
        self.scan_duplicates_btn = ctk.CTkButton(
            button_frame,
            text="Scan for Duplicates",
            command=self._start_duplicate_scan,
            width=150,
            height=32
        )
        self.scan_duplicates_btn.pack(side="left", padx=(0, 10))
        
        self.scan_large_files_btn = ctk.CTkButton(
            button_frame,
            text="Scan for Large Files",
            command=self._start_large_file_scan,
            width=150,
            height=32
        )
        self.scan_large_files_btn.pack(side="left")
        
        self.scan_both_btn = ctk.CTkButton(
            button_frame,
            text="Scan Both",
            command=self._start_both_scans,
            width=100,
            height=32,
            fg_color="#28a745"
        )
        self.scan_both_btn.pack(side="left", padx=(10, 0))
        
        # Threshold selector for large files
        threshold_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        threshold_frame.pack(side="right")
        
        ctk.CTkLabel(
            threshold_frame,
            text="Threshold:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 8))
        
        self.threshold_var = ctk.StringVar(value="100MB")
        threshold_menu = ctk.CTkOptionMenu(
            threshold_frame,
            values=["100MB", "500MB", "1GB", "2GB", "5GB"],
            variable=self.threshold_var,
            width=100
        )
        threshold_menu.pack(side="left")
        
        # Progress bar frame (hidden by default)
        self.progress_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_frame.pack_forget()
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, mode="determinate", height=6)
        self.progress_bar.pack(fill="x", pady=(0, 8))
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="Scanning...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.progress_label.pack(anchor="w")
        
        self.cancel_btn = ctk.CTkButton(
            self.progress_frame,
            text="Cancel",
            command=self._cancel_scan,
            width=100,
            height=28,
            fg_color="gray"
        )
        self.cancel_btn.pack(anchor="w", pady=(8, 0))
        
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
        
        # Main content area with split panes
        self.paned = PanedWindow(self, orient="horizontal", sashrelief="raised",
                                sashwidth=8, bg="#1a1a1a", bd=0)
        self.paned.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        
        # Left pane - Duplicates
        duplicates_frame = ctk.CTkFrame(self.paned, fg_color="transparent")
        self.paned.add(duplicates_frame, minsize=400, width=500)
        
        duplicates_header = ctk.CTkFrame(duplicates_frame, fg_color="transparent")
        duplicates_header.pack(fill="x", padx=16, pady=(16, 8))
        
        self.duplicates_title = ctk.CTkLabel(
            duplicates_header,
            text="Duplicates",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.duplicates_title.pack(side="left")
        
        self.duplicates_summary = ctk.CTkLabel(
            duplicates_header,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.duplicates_summary.pack(side="right")
        
        self.duplicates_scroll = ctk.CTkScrollableFrame(duplicates_frame)
        self.duplicates_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        
        # Right pane - Large Files
        large_files_frame = ctk.CTkFrame(self.paned, fg_color="transparent")
        self.paned.add(large_files_frame, minsize=400, width=500)
        
        large_files_header = ctk.CTkFrame(large_files_frame, fg_color="transparent")
        large_files_header.pack(fill="x", padx=16, pady=(16, 8))
        
        self.large_files_title = ctk.CTkLabel(
            large_files_header,
            text="Large Files",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.large_files_title.pack(side="left")
        
        self.large_files_summary = ctk.CTkLabel(
            large_files_header,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.large_files_summary.pack(side="right")
        
        self.large_files_scroll = ctk.CTkScrollableFrame(large_files_frame)
        self.large_files_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        
        # Batch action bar (hidden by default)
        self.batch_bar = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=8)
        self.batch_bar.pack(fill="x", padx=24, pady=(0, 24))
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
            text="Delete Selected",
            command=self._delete_selected,
            width=120,
            fg_color="#dc3545"
        ).pack(side="right")
    
    def _start_both_scans(self):
        """Start both duplicate and large file scans simultaneously."""
        self._start_duplicate_scan()
        self._start_large_file_scan()
    
    def _start_duplicate_scan(self):
        """Start scanning for duplicates."""
        self.scan_duplicates_btn.configure(state="disabled", text="Scanning...")
        self.scan_both_btn.configure(state="disabled")
        
        # Clear previous results
        for widget in self.duplicates_scroll.winfo_children():
            widget.destroy()
        self.duplicate_groups = []
        self.selected_duplicate_files = {}
        
        # Show progress
        self.completion_frame.pack_forget()
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting duplicate scan...")
        self.duplicate_cancel_event.clear()
        
        # Run scan in background thread
        thread = threading.Thread(target=self._duplicate_scan_thread, daemon=True)
        thread.start()
    
    def _duplicate_scan_thread(self):
        """Background thread for duplicate scanning."""
        def progress_callback(current: int, total: int):
            if total > 0:
                progress = current / total
                self.after(0, lambda: self.progress_bar.set(progress))
                self.after(0, lambda: self.progress_label.configure(
                    text=f"Scanning duplicates... {current}/{total} files"
                ))
            else:
                self.after(0, lambda: self.progress_label.configure(
                    text=f"Scanning duplicates... {current} files processed"
                ))
        
        try:
            root_path = Path("C:\\")
            groups = self.scanner.scan_duplicates(
                root_path,
                progress_callback=progress_callback,
                cancel_event=self.duplicate_cancel_event
            )
            
            if not self.duplicate_cancel_event.is_set():
                self.after(0, lambda: self._on_duplicate_scan_complete(groups))
        except Exception as e:
            if not self.duplicate_cancel_event.is_set():
                self.after(0, lambda: self._on_scan_error(str(e), "duplicate"))
    
    def _on_duplicate_scan_complete(self, groups: List[DuplicateGroup]):
        """Handle duplicate scan completion."""
        self.duplicate_groups = groups
        
        # Stop and hide progress bar
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Scan complete!")
        self.progress_frame.pack_forget()
        
        # Update summary
        total_wasted = sum(g.get_wasted_space() for g in groups)
        self.duplicates_summary.configure(
            text=f"{len(groups)} groups, {format_size(total_wasted)} wasted"
        )
        
        # Display results immediately
        try:
            print(f"Displaying {len(groups)} duplicate groups...")
            self._display_duplicates()
            print(f"Display complete. Cards created: {len(self.duplicates_scroll.winfo_children())}")
        except Exception as e:
            print(f"Error displaying duplicates: {e}")
            import traceback
            traceback.print_exc()
        
        # Show completion message
        self.completion_label.configure(
            text=f"✓ Duplicate scan complete! Found {len(groups)} duplicate groups."
        )
        self.completion_frame.configure(fg_color="#1a472a")
        self.completion_label.configure(text_color="#4ade80")
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        # Reset buttons
        self.scan_duplicates_btn.configure(state="normal", text="Scan for Duplicates")
        self.scan_large_files_btn.configure(state="normal")
        self.scan_both_btn.configure(state="normal")
    
    def _display_duplicates(self):
        """Display duplicate groups."""
        # Clear any existing widgets first
        for widget in self.duplicates_scroll.winfo_children():
            widget.destroy()
        
        if not self.duplicate_groups:
            # Show empty state
            empty_label = ctk.CTkLabel(
                self.duplicates_scroll,
                text="No duplicates found.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            empty_label.pack(pady=40)
            return
        
        # Limit initial display to first 100 groups for performance
        # User can scroll to see more
        groups_to_display = self.duplicate_groups[:100]
        has_more = len(self.duplicate_groups) > 100
        
        # Create cards for each duplicate group
        cards_created = 0
        for i, group in enumerate(groups_to_display):
            try:
                card = DuplicateGroupCard(
                    self.duplicates_scroll,
                    group,
                    on_selection_changed=self._on_duplicate_selection_changed
                )
                card.pack(fill="x", pady=(0, 12), padx=8)
                cards_created += 1
                
                # Update UI periodically for large lists
                if (i + 1) % 25 == 0:
                    self.duplicates_scroll.update_idletasks()
            except Exception as e:
                print(f"Error creating card for duplicate group {i}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Show "more" indicator if there are more groups
        if has_more:
            more_label = ctk.CTkLabel(
                self.duplicates_scroll,
                text=f"... and {len(self.duplicate_groups) - 100} more groups (scroll to see all)",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            more_label.pack(pady=10)
        
        # Force UI update
        self.duplicates_scroll.update_idletasks()
        print(f"Created {cards_created} duplicate cards (showing first 100 of {len(self.duplicate_groups)})")
    
    def _on_duplicate_selection_changed(self, group: DuplicateGroup, selected_files: List[FileInfo]):
        """Handle duplicate file selection change."""
        if selected_files:
            self.selected_duplicate_files[group] = selected_files
        else:
            self.selected_duplicate_files.pop(group, None)
        
        self._update_batch_bar()
    
    def _start_large_file_scan(self):
        """Start scanning for large files."""
        self.scan_large_files_btn.configure(state="disabled", text="Scanning...")
        self.scan_both_btn.configure(state="disabled")
        
        # Clear previous results
        for widget in self.large_files_scroll.winfo_children():
            widget.destroy()
        self.large_files = []
        self.selected_large_files = []
        
        # Get threshold
        threshold_str = self.threshold_var.get()
        threshold_mb = {
            "100MB": 100,
            "500MB": 500,
            "1GB": 1024,
            "2GB": 2048,
            "5GB": 5120
        }.get(threshold_str, 100)
        
        # Show progress (only if not already showing for duplicates)
        if not self.progress_frame.winfo_viewable():
            self.completion_frame.pack_forget()
            self.progress_frame.pack(fill="x", pady=(16, 0))
            self.progress_bar.set(0)
        
        # Update label to show both scans if duplicates is running
        if self.scan_duplicates_btn.cget("state") == "disabled":
            self.progress_label.configure(text="Scanning large files (duplicate scan also running)...")
        else:
            self.progress_label.configure(text="Starting large file scan...")
        
        self.large_file_cancel_event.clear()
        
        # Run scan in background thread
        thread = threading.Thread(
            target=self._large_file_scan_thread,
            args=(threshold_mb,),
            daemon=True
        )
        thread.start()
    
    def _large_file_scan_thread(self, threshold_mb: int):
        """Background thread for large file scanning."""
        def progress_callback(current: int, total: int):
            if self.scan_duplicates_btn.cget("state") == "disabled":
                self.after(0, lambda: self.progress_label.configure(
                    text=f"Large files: {current} found | Duplicate scan running..."
                ))
            else:
                self.after(0, lambda: self.progress_label.configure(
                    text=f"Scanning large files... {current} files found"
                ))
        
        try:
            root_path = Path("C:\\")
            files = self.scanner.scan_large_files(
                root_path,
                threshold_mb=threshold_mb,
                progress_callback=progress_callback,
                cancel_event=self.large_file_cancel_event
            )
            
            if not self.large_file_cancel_event.is_set():
                self.after(0, lambda: self._on_large_file_scan_complete(files))
        except Exception as e:
            if not self.large_file_cancel_event.is_set():
                self.after(0, lambda: self._on_scan_error(str(e), "large_file"))
    
    def _on_large_file_scan_complete(self, files: List[LargeFileInfo]):
        """Handle large file scan completion."""
        self.large_files = files
        
        # Stop and hide progress bar
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Scan complete!")
        self.progress_frame.pack_forget()
        
        # Update summary
        total_size = sum(f.size_bytes for f in files)
        self.large_files_summary.configure(
            text=f"{len(files)} files, {format_size(total_size)} total"
        )
        
        # Display results immediately
        try:
            print(f"Displaying {len(files)} large files...")
            self._display_large_files()
            print(f"Display complete. Cards created: {len(self.large_files_scroll.winfo_children())}")
        except Exception as e:
            print(f"Error displaying large files: {e}")
            import traceback
            traceback.print_exc()
        
        # Show completion message
        self.completion_label.configure(
            text=f"✓ Large file scan complete! Found {len(files)} large files."
        )
        self.completion_frame.configure(fg_color="#1a472a")
        self.completion_label.configure(text_color="#4ade80")
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        # Reset buttons
        self.scan_duplicates_btn.configure(state="normal")
        self.scan_large_files_btn.configure(state="normal", text="Scan for Large Files")
        self.scan_both_btn.configure(state="normal")
    
    def _display_large_files(self):
        """Display large files."""
        # Clear any existing widgets first
        for widget in self.large_files_scroll.winfo_children():
            widget.destroy()
        
        if not self.large_files:
            # Show empty state
            empty_label = ctk.CTkLabel(
                self.large_files_scroll,
                text="No large files found.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            empty_label.pack(pady=40)
            return
        
        # Limit initial display to first 100 files for performance
        files_to_display = self.large_files[:100]
        has_more = len(self.large_files) > 100
        
        # Create cards for each large file
        cards_created = 0
        for i, large_file in enumerate(files_to_display):
            try:
                card = LargeFileCard(
                    self.large_files_scroll,
                    large_file,
                    on_delete=self._on_delete_large_file,
                    on_move=self._on_move_large_file,
                    on_open_location=self._on_open_location
                )
                card.pack(fill="x", pady=(0, 12), padx=8)
                cards_created += 1
                
                # Update UI periodically for large lists
                if (i + 1) % 25 == 0:
                    self.large_files_scroll.update_idletasks()
            except Exception as e:
                print(f"Error creating card for large file {i}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Show "more" indicator if there are more files
        if has_more:
            more_label = ctk.CTkLabel(
                self.large_files_scroll,
                text=f"... and {len(self.large_files) - 100} more files (scroll to see all)",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            more_label.pack(pady=10)
        
        # Force UI update
        self.large_files_scroll.update_idletasks()
        print(f"Created {cards_created} large file cards (showing first 100 of {len(self.large_files)})")
    
    def _on_delete_large_file(self, large_file: LargeFileInfo):
        """Handle delete request for a large file."""
        def confirm_delete():
            self._delete_files([large_file.path])
        
        dialog = DeleteConfirmationDialog(
            self,
            [large_file.path],
            large_file.size_bytes,
            confirm_delete
        )
    
    def _on_move_large_file(self, large_file: LargeFileInfo):
        """Handle move request for a large file."""
        def confirm_move(dest: Path):
            self._move_file(large_file.path, dest)
        
        dialog = MoveDestinationDialog(
            self,
            large_file.path,
            confirm_move
        )
    
    def _on_open_location(self, file_path: Path):
        """Open file location in Explorer."""
        self.cleaner.open_in_explorer(file_path.parent)
    
    def _cancel_scan(self):
        """Cancel current scans."""
        self.duplicate_cancel_event.set()
        self.large_file_cancel_event.set()
        self.progress_label.configure(text="Cancelling...")
    
    def _update_batch_bar(self):
        """Update batch action bar based on selections."""
        # Count selected duplicate files
        total_duplicate_files = sum(len(files) for files in self.selected_duplicate_files.values())
        total_duplicate_bytes = sum(
            sum(f.size_bytes for f in files)
            for files in self.selected_duplicate_files.values()
        )
        
        # Count selected large files
        total_large_bytes = sum(f.size_bytes for f in self.selected_large_files)
        
        total_files = total_duplicate_files + len(self.selected_large_files)
        total_bytes = total_duplicate_bytes + total_large_bytes
        
        if total_files > 0:
            self.batch_label.configure(
                text=f"{total_files} items selected ({format_size(total_bytes)})"
            )
            self.batch_bar.pack(fill="x", padx=24, pady=(0, 24))
        else:
            self.batch_bar.pack_forget()
    
    def _clear_selection(self):
        """Clear all selections."""
        self.selected_duplicate_files = {}
        self.selected_large_files = []
        
        # Update cards
        for widget in self.duplicates_scroll.winfo_children():
            if isinstance(widget, DuplicateGroupCard):
                widget.clear_selection()
        
        self._update_batch_bar()
    
    def _delete_selected(self):
        """Delete all selected files."""
        # Collect all file paths
        files_to_delete = []
        total_bytes = 0
        
        # From duplicate selections
        for files in self.selected_duplicate_files.values():
            for file_info in files:
                files_to_delete.append(file_info.path)
                total_bytes += file_info.size_bytes
        
        # From large file selections
        for large_file in self.selected_large_files:
            files_to_delete.append(large_file.path)
            total_bytes += large_file.size_bytes
        
        if not files_to_delete:
            return
        
        def confirm_delete():
            self._delete_files(files_to_delete)
        
        dialog = DeleteConfirmationDialog(
            self,
            files_to_delete,
            total_bytes,
            confirm_delete
        )
    
    def _delete_files(self, file_paths: List[Path]):
        """Delete multiple files."""
        # Show progress
        self.completion_frame.pack_forget()
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"Deleting {len(file_paths)} files...")
        
        def delete_thread():
            deleted_count = 0
            failed_count = 0
            total_freed = 0
            
            for i, file_path in enumerate(file_paths):
                try:
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                        total_freed += file_size
                    
                    # Update progress
                    progress = (i + 1) / len(file_paths)
                    self.after(0, lambda p=progress: self.progress_bar.set(p))
                    self.after(0, lambda c=i+1, t=len(file_paths): self.progress_label.configure(
                        text=f"Deleting... {c}/{t}"
                    ))
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to delete {file_path}: {e}")
            
            self.after(0, lambda: self._on_delete_complete(deleted_count, failed_count, total_freed))
        
        thread = threading.Thread(target=delete_thread, daemon=True)
        thread.start()
    
    def _on_delete_complete(self, deleted_count: int, failed_count: int, total_freed: int):
        """Handle deletion completion."""
        self.progress_bar.set(1.0)
        self.progress_frame.pack_forget()
        
        msg = f"✓ Deleted {deleted_count} files! Freed {format_size(total_freed)}"
        if failed_count > 0:
            msg += f" ({failed_count} failed)"
        
        self.completion_label.configure(text=msg)
        self.completion_frame.configure(fg_color="#1a472a")
        self.completion_label.configure(text_color="#4ade80")
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        # Clear selection and refresh display
        self._clear_selection()
        self._display_duplicates()
        self._display_large_files()
    
    def _move_file(self, source: Path, destination: Path):
        """Move a file to destination."""
        # Show progress
        self.completion_frame.pack_forget()
        self.progress_frame.pack(fill="x", pady=(16, 0))
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"Moving {source.name}...")
        
        def move_thread():
            success, error_msg = self.cleaner.move_file(source, destination)
            self.after(0, lambda: self._on_move_complete(success, error_msg, source.name))
        
        thread = threading.Thread(target=move_thread, daemon=True)
        thread.start()
    
    def _on_move_complete(self, success: bool, error_msg: Optional[str], filename: str):
        """Handle move completion."""
        self.progress_bar.set(1.0)
        self.progress_frame.pack_forget()
        
        if success:
            msg = f"✓ Moved {filename} successfully"
            self.completion_frame.configure(fg_color="#1a472a")
            self.completion_label.configure(text_color="#4ade80")
        else:
            msg = f"✗ Failed to move {filename}: {error_msg}"
            self.completion_frame.configure(fg_color="#4a1a1a")
            self.completion_label.configure(text_color="#dc3545")
        
        self.completion_label.configure(text=msg)
        self.completion_frame.pack(fill="x", pady=(16, 0))
    
    def _on_scan_error(self, error_msg: str, scan_type: str = "unknown"):
        """Handle scan error."""
        self.progress_bar.set(0)
        
        # Only hide progress if both scans are done
        if (self.scan_duplicates_btn.cget("state") == "normal" and 
            self.scan_large_files_btn.cget("state") == "normal"):
            self.progress_frame.pack_forget()
        
        self.completion_label.configure(text=f"✗ Error ({scan_type}): {error_msg}")
        self.completion_frame.configure(fg_color="#4a1a1a")
        self.completion_label.configure(text_color="#dc3545")
        self.completion_frame.pack(fill="x", pady=(16, 0))
        
        # Reset buttons based on scan type
        if scan_type == "duplicate":
            self.scan_duplicates_btn.configure(state="normal", text="Scan for Duplicates")
        elif scan_type == "large_file":
            self.scan_large_files_btn.configure(state="normal", text="Scan for Large Files")
        else:
            self.scan_duplicates_btn.configure(state="normal", text="Scan for Duplicates")
            self.scan_large_files_btn.configure(state="normal", text="Scan for Large Files")
        self.scan_both_btn.configure(state="normal")