"""
Settings and cache persistence for Space Cleanser Pro.
"""
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from scanner import FolderInfo


class Settings:
    """Manages user preferences and cached scan results."""
    
    def __init__(self, settings_file: str = "settings.json"):
        """Initialize settings manager."""
        self.settings_file = Path(settings_file)
        self.settings = self._load_settings()
    
    def _load_settings(self) -> dict:
        """Load settings from file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Default settings
        return {
            "window_size": {"width": 900, "height": 700},
            "window_position": None,
            "filters": {
                "category": "all",
                "size_threshold_gb": 0,
                "age_days": None
            },
            "last_scan": None,
            "last_scan_time": None
        }
    
    def save(self):
        """Save settings to file."""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, default=str)
        except IOError as e:
            print(f"Failed to save settings: {e}")
    
    def get_window_size(self) -> tuple:
        """Get saved window size."""
        size = self.settings.get("window_size", {})
        return (size.get("width", 900), size.get("height", 700))
    
    def set_window_size(self, width: int, height: int):
        """Save window size."""
        self.settings["window_size"] = {"width": width, "height": height}
        self.save()
    
    def get_window_position(self) -> Optional[tuple]:
        """Get saved window position."""
        pos = self.settings.get("window_position")
        if pos:
            return (pos.get("x"), pos.get("y"))
        return None
    
    def set_window_position(self, x: int, y: int):
        """Save window position."""
        self.settings["window_position"] = {"x": x, "y": y}
        self.save()
    
    def get_filters(self) -> dict:
        """Get saved filter preferences."""
        return self.settings.get("filters", {
            "category": "all",
            "size_threshold_gb": 0,
            "age_days": None
        })
    
    def set_filters(self, category: str = "all", size_threshold_gb: float = 0, age_days: Optional[int] = None):
        """Save filter preferences."""
        self.settings["filters"] = {
            "category": category,
            "size_threshold_gb": size_threshold_gb,
            "age_days": age_days
        }
        self.save()
    
    def cache_scan_results(self, folders: list[FolderInfo]):
        """Cache scan results for instant display on startup."""
        # Convert FolderInfo to dict for JSON serialization
        cached = []
        for folder in folders:
            cached.append({
                "key": folder.key,
                "name": folder.name,
                "path": folder.path,
                "full_path": str(folder.full_path),
                "size_bytes": folder.size_bytes,
                "exists": folder.exists,
                "last_modified": folder.last_modified.isoformat() if folder.last_modified else None,
                "description": folder.description,
                "impact": folder.impact,
                "safety": folder.safety,
                "category": folder.category,
                "requires_admin": folder.requires_admin,
                "age_days": folder.age_days,
                "item_count": folder.item_count
            })
        
        self.settings["last_scan"] = cached
        self.settings["last_scan_time"] = datetime.now().isoformat()
        self.save()
    
    def get_cached_scan_results(self) -> Optional[list]:
        """Get cached scan results."""
        return self.settings.get("last_scan")
    
    def clear_cache(self):
        """Clear cached scan results."""
        self.settings["last_scan"] = None
        self.settings["last_scan_time"] = None
        self.save()
