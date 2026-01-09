"""
Filter bar component for category, size, and age filtering.
"""
import customtkinter as ctk
from typing import Callable, Optional


class FilterBar(ctk.CTkFrame):
    """Filter bar with category tabs, size slider, age filter, and search."""
    
    def __init__(self, parent, on_filter_changed: Callable[[dict], None]):
        super().__init__(parent, fg_color="transparent")
        
        self.on_filter_changed = on_filter_changed
        self.current_filters = {
            "category": "all",
            "size_threshold_gb": 0,
            "age_days": None,
            "search": ""
        }
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the filter bar UI."""
        # Category tabs
        category_frame = ctk.CTkFrame(self, fg_color="transparent")
        category_frame.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(
            category_frame,
            text="Category:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 8))
        
        self.category_var = ctk.StringVar(value="all")
        categories = [
            ("All", "all"),
            ("Safe", "safe"),
            ("Dev Tools", "dev_tools"),
            ("System", "system"),
            ("Browsers", "browsers"),
            ("User Files", "user_files")
        ]
        
        for label, value in categories:
            btn = ctk.CTkRadioButton(
                category_frame,
                text=label,
                variable=self.category_var,
                value=value,
                command=self._on_category_changed
            )
            btn.pack(side="left", padx=4)
        
        # Size threshold slider
        size_frame = ctk.CTkFrame(self, fg_color="transparent")
        size_frame.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(
            size_frame,
            text="Size >",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 8))
        
        self.size_var = ctk.DoubleVar(value=0)
        self.size_slider = ctk.CTkSlider(
            size_frame,
            from_=0,
            to=10,
            number_of_steps=10,
            variable=self.size_var,
            command=self._on_size_changed,
            width=150
        )
        self.size_slider.pack(side="left", padx=(0, 8))
        
        self.size_label = ctk.CTkLabel(
            size_frame,
            text="0 GB",
            font=ctk.CTkFont(size=11),
            width=50
        )
        self.size_label.pack(side="left")
        
        # Age filter dropdown
        age_frame = ctk.CTkFrame(self, fg_color="transparent")
        age_frame.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(
            age_frame,
            text="Age:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 8))
        
        self.age_var = ctk.StringVar(value="any")
        age_options = [
            ("Any", "any"),
            ("30+ days", "30"),
            ("90+ days", "90"),
            ("180+ days", "180")
        ]
        
        self.age_menu = ctk.CTkOptionMenu(
            age_frame,
            values=[label for label, _ in age_options],
            variable=self.age_var,
            command=self._on_age_changed,
            width=120
        )
        self.age_menu.pack(side="left")
        
        # Store age values mapping
        self.age_values = {label: value for label, value in age_options}
        
        # Search box
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(side="right")
        
        ctk.CTkLabel(
            search_frame,
            text="Search:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 8))
        
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Filter by name or path...",
            width=200
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search_changed())
    
    def _on_category_changed(self):
        """Handle category filter change."""
        self.current_filters["category"] = self.category_var.get()
        self.on_filter_changed(self.current_filters)
    
    def _on_size_changed(self, value):
        """Handle size threshold change."""
        gb_value = round(value, 1)
        self.current_filters["size_threshold_gb"] = gb_value
        self.size_label.configure(text=f"{gb_value:.1f} GB")
        self.on_filter_changed(self.current_filters)
    
    def _on_age_changed(self, choice):
        """Handle age filter change."""
        age_value = self.age_values.get(choice, "any")
        self.current_filters["age_days"] = int(age_value) if age_value != "any" else None
        self.on_filter_changed(self.current_filters)
    
    def _on_search_changed(self):
        """Handle search text change."""
        self.current_filters["search"] = self.search_entry.get().lower()
        self.on_filter_changed(self.current_filters)
    
    def get_filters(self) -> dict:
        """Get current filter values."""
        return self.current_filters.copy()
    
    def set_filters(self, filters: dict):
        """Set filter values programmatically."""
        if "category" in filters:
            self.category_var.set(filters["category"])
        if "size_threshold_gb" in filters:
            self.size_var.set(filters["size_threshold_gb"])
            self.size_label.configure(text=f"{filters['size_threshold_gb']:.1f} GB")
        if "age_days" in filters:
            # Find matching label
            for label, value in self.age_values.items():
                if (filters["age_days"] is None and value == "any") or \
                   (filters["age_days"] is not None and str(filters["age_days"]) == value):
                    self.age_var.set(label)
                    break
        if "search" in filters:
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, filters["search"])
