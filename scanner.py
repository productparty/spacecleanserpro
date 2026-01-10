"""
Enhanced scanner module for discovering and analyzing cache folders across system, browsers, and dev tools.
"""
import json
import os
import glob
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Callable, Dict
from datetime import datetime, timedelta

from admin_helper import is_admin, check_admin_required
from resource_path import get_resource_path


@dataclass
class FolderInfo:
    """Information about a discovered cache folder."""
    key: str
    name: str
    path: str
    full_path: Path
    size_bytes: int
    exists: bool
    last_modified: Optional[datetime]
    description: str
    impact: str
    safety: str  # "safe", "caution", or "keep"
    category: str = "unknown"
    requires_admin: bool = False
    age_days: Optional[int] = None
    item_count: int = 0
    metadata: Dict = field(default_factory=dict)


class Scanner:
    """Scans C: drive for cache folders across dev tools, system, browsers, and user files."""
    
    def __init__(self, config_path: str = None):
        """Initialize scanner with folder definitions."""
        if config_path is None:
            config_path = get_resource_path("folder_defs.json")
        self.config_path = config_path
        self.config = self._load_config()
        self.folder_defs = self.config.get("locations", {})
        self.home_dir = Path.home()
        self.is_admin = is_admin()
    
    def _load_config(self) -> dict:
        """Load folder definitions from JSON config."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {self.config_path} not found")
            return {"locations": {}}
        except json.JSONDecodeError as e:
            print(f"Error parsing {self.config_path}: {e}")
            return {"locations": {}}
    
    def _expand_path(self, path_str: str) -> Path:
        """Expand environment variables and convert to Path."""
        # Handle special cases
        if path_str == "RECYCLE_BIN":
            # Recycle Bin is handled specially
            return Path("RECYCLE_BIN")
        
        # Expand environment variables
        expanded = os.path.expandvars(path_str)
        
        # Handle relative paths (relative to home)
        if not os.path.isabs(expanded):
            return self.home_dir / expanded
        
        return Path(expanded)
    
    def _calculate_size(self, folder_path: Path) -> tuple[int, int]:
        """
        Recursively calculate total size and file count.
        
        Returns:
            Tuple of (size_bytes, file_count)
        """
        total_size = 0
        file_count = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    try:
                        total_size += filepath.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue
        except (OSError, PermissionError):
            # Folder doesn't exist or we can't access it
            pass
        
        return total_size, file_count
    
    def _get_last_modified(self, folder_path: Path) -> Optional[datetime]:
        """Get the last modified time of a folder."""
        try:
            if folder_path.exists():
                # Get the most recent modification time from files in the folder
                latest = 0
                for dirpath, dirnames, filenames in os.walk(folder_path):
                    for filename in filenames:
                        filepath = Path(dirpath) / filename
                        try:
                            mtime = filepath.stat().st_mtime
                            latest = max(latest, mtime)
                        except (OSError, PermissionError):
                            continue
                if latest > 0:
                    return datetime.fromtimestamp(latest)
        except (OSError, PermissionError):
            pass
        return None
    
    def _calculate_age_days(self, last_modified: Optional[datetime]) -> Optional[int]:
        """Calculate age in days since last modification."""
        if last_modified is None:
            return None
        delta = datetime.now() - last_modified
        return delta.days
    
    def _scan_browser_profiles(self, base_path: Path, subpath: str = "") -> List[FolderInfo]:
        """Scan for browser profiles dynamically (Chrome, Firefox, etc.)."""
        results = []
        
        if not base_path.exists():
            return results
        
        # Look for profile directories
        if "Firefox" in str(base_path):
            # Firefox: Profiles folder contains numbered profile folders
            profiles_path = base_path / "Profiles"
            if profiles_path.exists():
                for profile_dir in profiles_path.iterdir():
                    if profile_dir.is_dir() and profile_dir.name.startswith(('default', 'Profile')):
                        cache_path = profile_dir / subpath if subpath else profile_dir
                        if cache_path.exists():
                            size_bytes, item_count = self._calculate_size(cache_path)
                            last_modified = self._get_last_modified(cache_path)
                            age_days = self._calculate_age_days(last_modified)
                            
                            results.append(FolderInfo(
                                key=f"firefox_profile_{profile_dir.name}",
                                name=f"Firefox Profile: {profile_dir.name}",
                                path=str(cache_path.relative_to(self.home_dir)) if cache_path.is_relative_to(self.home_dir) else str(cache_path),
                                full_path=cache_path,
                                size_bytes=size_bytes,
                                exists=True,
                                last_modified=last_modified,
                                description="Firefox browser cache and profile data",
                                impact="Firefox will rebuild cache automatically. You'll need to re-login to some sites.",
                                safety="safe",
                                category="browsers",
                                age_days=age_days,
                                item_count=item_count
                            ))
        else:
            # Chrome/Edge: Default profile or multiple profiles
            default_cache = base_path / "Default" / subpath if subpath else base_path / "Default"
            if default_cache.exists():
                size_bytes, item_count = self._calculate_size(default_cache)
                last_modified = self._get_last_modified(default_cache)
                age_days = self._calculate_age_days(last_modified)
                
                browser_name = "Chrome" if "Chrome" in str(base_path) else "Edge"
                results.append(FolderInfo(
                    key=f"{browser_name.lower()}_cache_default",
                    name=f"{browser_name} Browser Cache",
                    path=str(default_cache.relative_to(self.home_dir)) if default_cache.is_relative_to(self.home_dir) else str(default_cache),
                    full_path=default_cache,
                    size_bytes=size_bytes,
                    exists=True,
                    last_modified=last_modified,
                    description=f"{browser_name} browser cache",
                    impact=f"{browser_name} will rebuild cache automatically. You'll need to re-login to some sites.",
                    safety="safe",
                    category="browsers",
                    age_days=age_days,
                    item_count=item_count
                ))
        
        return results
    
    def _scan_recycle_bin(self) -> Optional[FolderInfo]:
        """Scan Windows Recycle Bin."""
        try:
            import winshell
            recycle_bin = winshell.recycle_bin()
            size_bytes = sum(item.original_size() for item in recycle_bin)
            item_count = len(list(recycle_bin))
            
            return FolderInfo(
                key="recycle_bin",
                name="Recycle Bin",
                path="Recycle Bin",
                full_path=Path("RECYCLE_BIN"),
                size_bytes=size_bytes,
                exists=item_count > 0,
                last_modified=None,
                description="Deleted files waiting to be permanently removed",
                impact="Files will be permanently deleted. You can review contents before emptying.",
                safety="safe",
                category="system",
                item_count=item_count,
                metadata={"special": True}
            )
        except ImportError:
            # winshell not installed, skip Recycle Bin
            return None
        except Exception:
            return None
    
    def _scan_downloads_old(self, downloads_path: Path, age_threshold: int) -> Optional[FolderInfo]:
        """Scan Downloads folder for files older than threshold."""
        if not downloads_path.exists():
            return None
        
        old_files = []
        total_size = 0
        cutoff_date = datetime.now() - timedelta(days=age_threshold)
        
        try:
            for item in downloads_path.iterdir():
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime < cutoff_date:
                        if item.is_file():
                            total_size += item.stat().st_size
                            old_files.append(item.name)
                except (OSError, PermissionError):
                    continue
            
            if old_files:
                return FolderInfo(
                    key="downloads_old",
                    name=f"Old Downloads ({len(old_files)} files)",
                    path=str(downloads_path.relative_to(self.home_dir)),
                    full_path=downloads_path,
                    size_bytes=total_size,
                    exists=True,
                    last_modified=None,
                    description=f"Files in Downloads folder older than {age_threshold} days",
                    impact="These files will be permanently deleted. Review the list before cleaning.",
                    safety="caution",
                    category="user_files",
                    item_count=len(old_files),
                    metadata={"old_files": old_files[:10]}  # Store first 10 for preview
                )
        except (OSError, PermissionError):
            pass
        
        return None
    
    def scan(self, progress_callback: Optional[Callable[[str], None]] = None) -> List[FolderInfo]:
        """
        Scan for all defined cache folders.
        
        Args:
            progress_callback: Optional function called with folder name during scan
            
        Returns:
            List of FolderInfo objects, sorted by size (largest first)
        """
        folders = []
        
        for key, definition in self.folder_defs.items():
            if progress_callback:
                progress_callback(definition.get("name", key))
            
            # Check admin requirement
            requires_admin = definition.get("requires_admin", False)
            if requires_admin and not self.is_admin:
                # Skip admin-required folders if not running as admin
                continue
            
            # Handle special cases
            if definition.get("special"):
                if key == "recycle_bin":
                    recycle_info = self._scan_recycle_bin()
                    if recycle_info:
                        folders.append(recycle_info)
                continue
            
            # Handle dynamic browser profiles
            if definition.get("dynamic"):
                base_path = self._expand_path(definition["path"])
                subpath = definition.get("subpath", "")
                browser_folders = self._scan_browser_profiles(base_path, subpath)
                folders.extend(browser_folders)
                continue
            
            # Handle age-threshold folders (like old downloads)
            if "age_threshold_days" in definition:
                folder_path = self._expand_path(definition["path"])
                age_threshold = definition["age_threshold_days"]
                old_folder_info = self._scan_downloads_old(folder_path, age_threshold)
                if old_folder_info:
                    folders.append(old_folder_info)
                continue
            
            # Standard folder scanning
            folder_path = self._expand_path(definition["path"])
            
            exists = folder_path.exists() and folder_path.is_dir()
            size_bytes = 0
            item_count = 0
            last_modified = None
            age_days = None
            
            if exists:
                try:
                    size_bytes, item_count = self._calculate_size(folder_path)
                    last_modified = self._get_last_modified(folder_path)
                    age_days = self._calculate_age_days(last_modified)
                except (OSError, PermissionError) as e:
                    # Can't access folder, skip it
                    continue
            
            folder_info = FolderInfo(
                key=key,
                name=definition.get("name", key),
                path=definition.get("path", ""),
                full_path=folder_path,
                size_bytes=size_bytes,
                exists=exists,
                last_modified=last_modified,
                description=definition.get("description", ""),
                impact=definition.get("impact", ""),
                safety=definition.get("safety", "keep"),
                category=definition.get("category", "unknown"),
                requires_admin=requires_admin,
                age_days=age_days,
                item_count=item_count
            )
            
            folders.append(folder_info)
        
        # Sort by size (largest first), then by name
        folders.sort(key=lambda f: (f.size_bytes, f.name), reverse=True)
        
        return folders
    
    def get_total_reclaimable(self, folders: List[FolderInfo]) -> int:
        """Calculate total reclaimable space from safe folders."""
        return sum(f.size_bytes for f in folders if f.exists and f.safety == "safe")
    
    def get_by_category(self, folders: List[FolderInfo], category: str) -> List[FolderInfo]:
        """Filter folders by category."""
        return [f for f in folders if f.category == category]
    
    def get_safe_folders(self, folders: List[FolderInfo]) -> List[FolderInfo]:
        """Get all safe folders."""
        return [f for f in folders if f.safety == "safe" and f.exists]