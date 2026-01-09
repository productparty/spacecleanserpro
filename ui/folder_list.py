"""
Grouped, filterable folder list component.
"""
import customtkinter as ctk
from typing import List, Callable, Dict, Optional
from scanner import FolderInfo

from ui.folder_card import FolderCard


class FolderList(ctk.CTkScrollableFrame):
    """Scrollable list of folders grouped by category."""
    
    def __init__(self, parent, on_clean: Callable[[FolderInfo], None],
                 on_show_folder: Callable[[FolderInfo], None],
                 on_selection_changed: Optional[Callable[[List[FolderInfo]], None]] = None):
        super().__init__(parent)
        
        self.on_clean = on_clean
        self.on_show_folder = on_show_folder
        self.on_selection_changed = on_selection_changed
        self.all_folders: List[FolderInfo] = []
        self.filtered_folders: List[FolderInfo] = []
        self.selected_folders: List[FolderInfo] = []
        self.category_sections: Dict[str, ctk.CTkFrame] = {}
        
        # Category display names
        self.category_names = {
            "dev_tools": "Development Tools",
            "system": "System Files",
            "browsers": "Browser Caches",
            "user_files": "User Files",
            "unknown": "Other"
        }
    
    def set_folders(self, folders: List[FolderInfo]):
        """Set folders to display."""
        self.all_folders = folders
        self._apply_filters()
    
    def apply_filters(self, filters: Dict):
        """Apply filters to the folder list."""
        self._apply_filters(filters)
    
    def _apply_filters(self, filters: Optional[Dict] = None):
        """Filter folders based on current filter settings."""
        if filters is None:
            # Use default filters
            filters = {
                "category": "all",
                "size_threshold_gb": 0,
                "age_days": None,
                "search": ""
            }
        
        filtered = []
        
        for folder in self.all_folders:
            if not folder.exists:
                continue
            
            # Category filter
            if filters["category"] != "all":
                if filters["category"] == "safe":
                    if folder.safety != "safe":
                        continue
                elif folder.category != filters["category"]:
                    continue
            
            # Size filter
            size_gb = folder.size_bytes / (1024 ** 3)
            if size_gb < filters["size_threshold_gb"]:
                continue
            
            # Age filter
            if filters["age_days"] is not None and folder.age_days is not None:
                if folder.age_days < filters["age_days"]:
                    continue
            
            # Search filter
            if filters["search"]:
                search_lower = filters["search"].lower()
                if search_lower not in folder.name.lower() and search_lower not in folder.path.lower():
                    continue
            
            filtered.append(folder)
        
        self.filtered_folders = filtered
        self._redraw()
    
    def _redraw(self):
        """Redraw the folder list grouped by category."""
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        self.category_sections.clear()
        
        if not self.filtered_folders:
            # Show empty state
            empty_label = ctk.CTkLabel(
                self,
                text="No folders match the current filters.",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            empty_label.pack(pady=40)
            return
        
        # Group by category
        categories: Dict[str, List[FolderInfo]] = {}
        for folder in self.filtered_folders:
            category = folder.category or "unknown"
            if category not in categories:
                categories[category] = []
            categories[category].append(folder)
        
        # Sort categories by total size
        category_order = sorted(
            categories.keys(),
            key=lambda c: sum(f.size_bytes for f in categories[c]),
            reverse=True
        )
        
        # Create sections for each category
        for category in category_order:
            folders_in_category = categories[category]
            self._create_category_section(category, folders_in_category)
    
    def _create_category_section(self, category: str, folders: List[FolderInfo]):
        """Create a collapsible section for a category."""
        # Section header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(16, 8))
        
        # Collapsible button
        total_size = sum(f.size_bytes for f in folders)
        category_name = self.category_names.get(category, category.replace("_", " ").title())
        
        header_btn = ctk.CTkButton(
            header_frame,
            text=f"▼ {category_name} ({len(folders)} items, {self._format_size(total_size)})",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            hover_color="#2b2b2b",
            anchor="w",
            command=lambda c=category: self._toggle_category(c)
        )
        header_btn.pack(fill="x")
        
        # Section content frame
        section_frame = ctk.CTkFrame(self, fg_color="transparent")
        section_frame.pack(fill="x", padx=16)
        
        self.category_sections[category] = section_frame
        
        # Add folder cards
        for folder in folders:
            card = FolderCard(
                section_frame,
                folder,
                on_clean=self.on_clean,
                on_show_folder=lambda f=folder: self.on_show_folder(f),
                on_selection_changed=self._on_card_selection_changed
            )
            card.pack(fill="x", pady=(0, 12))
    
    def _toggle_category(self, category: str):
        """Toggle category section visibility."""
        if category in self.category_sections:
            section = self.category_sections[category]
            if section.winfo_viewable():
                section.pack_forget()
            else:
                section.pack(fill="x", padx=16)
    
    def _on_card_selection_changed(self, folder: FolderInfo, selected: bool):
        """Handle folder card selection change."""
        if selected:
            if folder not in self.selected_folders:
                self.selected_folders.append(folder)
        else:
            if folder in self.selected_folders:
                self.selected_folders.remove(folder)
        
        if self.on_selection_changed:
            self.on_selection_changed(self.selected_folders)
    
    def get_selected_folders(self) -> List[FolderInfo]:
        """Get currently selected folders."""
        return self.selected_folders.copy()
    
    def select_all_safe(self):
        """Select all safe folders."""
        self.selected_folders = [f for f in self.filtered_folders if f.safety == "safe" and f.exists]
        self._redraw()
        if self.on_selection_changed:
            self.on_selection_changed(self.selected_folders)
    
    def clear_selection(self):
        """Clear all selections."""
        self.selected_folders = []
        self._redraw()
        if self.on_selection_changed:
            self.on_selection_changed(self.selected_folders)
    
    def _format_size(self, bytes_size: int) -> str:
        """Format bytes to human-readable size."""
        from ui.dialogs import format_size
        return format_size(bytes_size)
