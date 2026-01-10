"""
Enhanced scanner module for discovering and analyzing cache folders across system, browsers, and dev tools.
"""
import json
import os
import glob
import hashlib
import threading
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


@dataclass
class FileInfo:
    """Information about a single file."""
    path: Path
    size_bytes: int
    modified_date: datetime
    created_date: Optional[datetime] = None


@dataclass
class DuplicateGroup:
    """Group of duplicate files with the same hash."""
    file_hash: str
    size_bytes: int
    files: List[FileInfo]
    
    def get_wasted_space(self) -> int:
        """Calculate wasted space (size * (copies - 1))."""
        if len(self.files) < 2:
            return 0
        return self.size_bytes * (len(self.files) - 1)
    
    def get_representative_name(self) -> str:
        """Get a representative filename from the group."""
        if self.files:
            return self.files[0].path.name
        return "Unknown"


@dataclass
class LargeFileInfo:
    """Information about a large file."""
    path: Path
    size_bytes: int
    modified_date: datetime
    created_date: Optional[datetime]
    file_type: str  # "video", "installer", "archive", "image", "document", "other"
    age_days: int


class DiscoveryScanner:
    """Scans for duplicate files and large files across the C: drive."""
    
    # System folders to exclude from scanning
    EXCLUDED_PATHS = [
        "C:\\Windows",
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        "C:\\ProgramData",
        "$Recycle.Bin",
        "System Volume Information",
        "C:\\$Recycle.Bin",
        "C:\\System Volume Information",
    ]
    
    # File type mappings
    FILE_TYPE_MAP = {
        "video": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
        "installer": [".exe", ".msi", ".iso", ".img", ".dmg"],
        "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
        "image": [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".psd", ".raw", ".tiff", ".webp"],
        "document": [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt"],
    }
    
    def __init__(self):
        """Initialize the discovery scanner."""
        self.cancel_event = threading.Event()
    
    def _should_exclude_path(self, path: Path) -> bool:
        """Check if a path should be excluded from scanning."""
        path_str = str(path).lower()
        for excluded in self.EXCLUDED_PATHS:
            if excluded.lower() in path_str:
                return True
        # Check for hidden/system files
        if path.name.startswith('.') or path.name.startswith('$'):
            return True
        return False
    
    def hash_file(self, file_path: Path) -> Optional[str]:
        """
        Calculate MD5 hash of a file using chunked reading for memory efficiency.
        
        Args:
            file_path: Path to the file
            
        Returns:
            MD5 hash string or None if file can't be read
        """
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except (OSError, PermissionError, IOError):
            return None
    
    def get_file_type(self, file_path: Path) -> str:
        """Determine file type category from extension."""
        ext = file_path.suffix.lower()
        for file_type, extensions in self.FILE_TYPE_MAP.items():
            if ext in extensions:
                return file_type
        return "other"
    
    def scan_duplicates(self, root_path: Path, 
                       progress_callback: Optional[Callable[[int, int], None]] = None,
                       cancel_event: Optional[threading.Event] = None) -> List[DuplicateGroup]:
        """
        Scan for duplicate files using hash-based matching.
        
        Args:
            root_path: Root directory to scan (typically C:\)
            progress_callback: Optional callback(current_count, total_count)
            cancel_event: Optional threading.Event to signal cancellation
            
        Returns:
            List of DuplicateGroup objects, sorted by wasted space
        """
        if cancel_event is None:
            cancel_event = self.cancel_event
        
        cancel_event.clear()
        
        # Dictionary to group files by hash
        hash_groups: Dict[str, List[FileInfo]] = {}
        file_count = 0
        processed_count = 0
        
        # First pass: count files (for progress)
        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                # Filter out excluded directories
                dirnames[:] = [d for d in dirnames if not self._should_exclude_path(Path(dirpath) / d)]
                
                for filename in filenames:
                    file_path = Path(dirpath) / filename
                    if self._should_exclude_path(file_path):
                        continue
                    try:
                        stat = file_path.stat()
                        # Skip files smaller than 1MB
                        if stat.st_size < 1024 * 1024:
                            continue
                        file_count += 1
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        
        # Second pass: hash files
        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                if cancel_event.is_set():
                    break
                
                # Filter out excluded directories
                dirnames[:] = [d for d in dirnames if not self._should_exclude_path(Path(dirpath) / d)]
                
                for filename in filenames:
                    if cancel_event.is_set():
                        break
                    
                    file_path = Path(dirpath) / filename
                    if self._should_exclude_path(file_path):
                        continue
                    
                    try:
                        stat = file_path.stat()
                        # Skip files smaller than 1MB
                        if stat.st_size < 1024 * 1024:
                            continue
                        
                        # Calculate hash
                        file_hash = self.hash_file(file_path)
                        if file_hash is None:
                            continue
                        
                        # Get file metadata
                        modified_date = datetime.fromtimestamp(stat.st_mtime)
                        created_date = None
                        try:
                            created_date = datetime.fromtimestamp(stat.st_ctime)
                        except (OSError, AttributeError):
                            pass
                        
                        file_info = FileInfo(
                            path=file_path,
                            size_bytes=stat.st_size,
                            modified_date=modified_date,
                            created_date=created_date
                        )
                        
                        # Group by hash
                        if file_hash not in hash_groups:
                            hash_groups[file_hash] = []
                        hash_groups[file_hash].append(file_info)
                        
                        processed_count += 1
                        
                        # Update progress every 50 files
                        if progress_callback and processed_count % 50 == 0:
                            progress_callback(processed_count, file_count)
                    
                    except (OSError, PermissionError):
                        continue
        
        except (OSError, PermissionError):
            pass
        
        # Convert to DuplicateGroup objects (only groups with 2+ files)
        duplicate_groups = []
        for file_hash, files in hash_groups.items():
            if len(files) >= 2:
                # All files in group have same size
                size_bytes = files[0].size_bytes
                duplicate_groups.append(DuplicateGroup(
                    file_hash=file_hash,
                    size_bytes=size_bytes,
                    files=files
                ))
        
        # Sort by wasted space (largest first)
        duplicate_groups.sort(key=lambda g: g.get_wasted_space(), reverse=True)
        
        return duplicate_groups
    
    def scan_large_files(self, root_path: Path, threshold_mb: int,
                        progress_callback: Optional[Callable[[int, int], None]] = None,
                        cancel_event: Optional[threading.Event] = None) -> List[LargeFileInfo]:
        """
        Scan for large files above threshold.
        
        Args:
            root_path: Root directory to scan (typically C:\)
            threshold_mb: Minimum file size in MB
            progress_callback: Optional callback(current_count, total_count)
            cancel_event: Optional threading.Event to signal cancellation
            
        Returns:
            List of LargeFileInfo objects, sorted by size
        """
        if cancel_event is None:
            cancel_event = self.cancel_event
        
        cancel_event.clear()
        
        threshold_bytes = threshold_mb * 1024 * 1024
        large_files = []
        processed_count = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                if cancel_event.is_set():
                    break
                
                # Filter out excluded directories
                dirnames[:] = [d for d in dirnames if not self._should_exclude_path(Path(dirpath) / d)]
                
                for filename in filenames:
                    if cancel_event.is_set():
                        break
                    
                    file_path = Path(dirpath) / filename
                    if self._should_exclude_path(file_path):
                        continue
                    
                    try:
                        stat = file_path.stat()
                        if stat.st_size < threshold_bytes:
                            continue
                        
                        modified_date = datetime.fromtimestamp(stat.st_mtime)
                        created_date = None
                        try:
                            created_date = datetime.fromtimestamp(stat.st_ctime)
                        except (OSError, AttributeError):
                            pass
                        
                        age_days = (datetime.now() - modified_date).days
                        file_type = self.get_file_type(file_path)
                        
                        large_file = LargeFileInfo(
                            path=file_path,
                            size_bytes=stat.st_size,
                            modified_date=modified_date,
                            created_date=created_date,
                            file_type=file_type,
                            age_days=age_days
                        )
                        
                        large_files.append(large_file)
                        processed_count += 1
                        
                        # Update progress every 25 files
                        if progress_callback and processed_count % 25 == 0:
                            progress_callback(processed_count, 0)  # Total unknown
                    
                    except (OSError, PermissionError):
                        continue
        
        except (OSError, PermissionError):
            pass
        
        # Sort by size (largest first)
        large_files.sort(key=lambda f: f.size_bytes, reverse=True)
        
        return large_files