"""
Cleaner module for safely deleting cache folders.
"""
import os
import sys
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Callable
from datetime import datetime
from scanner import FolderInfo

# Set up logging to file
log_file = Path(__file__).parent / "cleaner.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Cleaner:
    """Handles safe deletion of cache folders."""
    
    @staticmethod
    def delete_folder(folder_path: Path) -> Tuple[bool, Optional[str], int]:
        """
        Delete a folder and return success status, error message, and bytes freed.
        
        Args:
            folder_path: Path to the folder to delete
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str], bytes_freed: int)
        """
        logger.info(f"Starting deletion of: {folder_path}")
        
        if not folder_path.exists():
            logger.info("Folder doesn't exist, nothing to delete")
            return True, None, 0
        
        if not folder_path.is_dir():
            logger.error("Path is not a directory")
            return False, "Path is not a directory", 0
        
        # Calculate size before deletion
        bytes_freed = Cleaner._calculate_size(folder_path)
        logger.info(f"Folder size: {bytes_freed / (1024*1024):.1f} MB")
        
        # On Windows, use robocopy trick for long paths, then regular rmtree
        if sys.platform == 'win32':
            success, error_msg = Cleaner._delete_windows_long_path(folder_path)
            if success:
                logger.info(f"Successfully deleted {folder_path}")
                return True, None, bytes_freed
            else:
                logger.error(f"Windows deletion failed: {error_msg}")
                return False, error_msg, 0
        
        # Non-Windows: use regular rmtree
        try:
            shutil.rmtree(folder_path)
            logger.info(f"Successfully deleted {folder_path}")
            return True, None, bytes_freed
        except PermissionError as e:
            error_str = str(e)
            logger.error(f"Permission denied: {error_str}")
            hint = Cleaner._get_lock_hint(folder_path)
            return False, f"Some files are locked. {hint}", 0
        except OSError as e:
            error_str = str(e)
            logger.error(f"OS Error: {error_str}")
            hint = Cleaner._get_lock_hint(folder_path)
            return False, f"Cannot delete - files may be in use. {hint}", 0
        except Exception as e:
            logger.exception(f"Unexpected error deleting {folder_path}")
            return False, f"Unexpected error: {type(e).__name__}", 0
    
    @staticmethod
    def _delete_windows_long_path(folder_path: Path) -> Tuple[bool, Optional[str]]:
        """
        Delete folder on Windows, handling long paths (>260 chars).
        Uses 'rd /s /q' command which handles long paths better than Python's shutil.
        """
        try:
            # Use cmd.exe's rd command which handles long paths
            # /s = remove all subdirectories and files
            # /q = quiet mode, no confirmation
            result = subprocess.run(
                ['cmd', '/c', 'rd', '/s', '/q', str(folder_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for large folders
            )
            
            if result.returncode == 0:
                return True, None
            
            # If rd failed, check why
            error_output = result.stderr.strip() if result.stderr else result.stdout.strip()
            logger.error(f"rd command failed: {error_output}")
            
            # Check if it's a permission/lock issue
            if "Access is denied" in error_output or "being used" in error_output:
                hint = Cleaner._get_lock_hint(folder_path)
                return False, f"Some files are locked. {hint}"
            
            # Try to give a helpful message
            if "cannot find" in error_output.lower():
                # Might already be partially deleted, check if folder exists
                if not folder_path.exists():
                    return True, None
            
            return False, f"Deletion failed. {Cleaner._get_lock_hint(folder_path)}"
            
        except subprocess.TimeoutExpired:
            logger.error("Deletion timed out after 5 minutes")
            return False, "Deletion timed out. The folder may be very large or files may be locked."
        except Exception as e:
            logger.exception(f"Exception during Windows deletion: {e}")
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def _get_lock_hint(folder_path: Path) -> str:
        """Get a hint about what might be locking files."""
        path_str = str(folder_path).lower()
        
        if ".gradle" in path_str:
            return "Try closing Android Studio and stopping Gradle daemons (run 'gradlew --stop' in your project)."
        elif ".android" in path_str:
            return "Try closing Android Studio and any running emulators."
        elif ".npm" in path_str:
            return "Try closing any running Node.js processes or IDEs."
        elif ".cargo" in path_str:
            return "Try closing any running Rust builds or IDEs."
        elif ".cursor" in path_str:
            return "Try closing Cursor editor."
        elif ".vscode" in path_str:
            return "Try closing VS Code."
        else:
            return "Try closing applications that might be using these files."
    
    @staticmethod
    def _calculate_size(folder_path: Path) -> int:
        """Calculate total size of a folder in bytes."""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    try:
                        total_size += filepath.stat().st_size
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue
        except (OSError, PermissionError):
            # Folder doesn't exist or we can't access it
            pass
        return total_size
    
    @staticmethod
    def delete_folders_batch(folders: List[FolderInfo], 
                             progress_callback: Optional[Callable[[FolderInfo, int, int], None]] = None) -> dict:
        """
        Delete multiple folders in batch with progress tracking.
        
        Args:
            folders: List of FolderInfo objects to delete
            progress_callback: Optional callback(current_folder, completed, total)
            
        Returns:
            Dict with 'success_count', 'failed_count', 'total_bytes_freed', 'errors'
        """
        results = {
            "success_count": 0,
            "failed_count": 0,
            "total_bytes_freed": 0,
            "errors": []
        }
        
        total = len(folders)
        
        for idx, folder in enumerate(folders, 1):
            if progress_callback:
                progress_callback(folder, idx, total)
            
            success, error_msg, bytes_freed = Cleaner.delete_folder(folder.full_path)
            
            if success:
                results["success_count"] += 1
                results["total_bytes_freed"] += bytes_freed
            else:
                results["failed_count"] += 1
                results["errors"].append({
                    "folder": folder.name,
                    "error": error_msg
                })
        
        return results
    
    @staticmethod
    def open_in_explorer(folder_path: Path) -> bool:
        """
        Open folder in Windows File Explorer.
        
        Args:
            folder_path: Path to open
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # If folder doesn't exist, open parent directory
            if not folder_path.exists():
                parent = folder_path.parent
                if parent.exists():
                    os.startfile(parent)
                else:
                    os.startfile(Path.home())
            else:
                os.startfile(folder_path)
            return True
        except Exception as e:
            print(f"Error opening folder: {e}")
            return False
    
    @staticmethod
    def move_file(source: Path, destination: Path) -> Tuple[bool, Optional[str]]:
        """
        Move a file to a destination directory, handling Windows long paths.
        
        Args:
            source: Source file path
            destination: Destination directory (file will keep same name)
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        logger.info(f"Moving file: {source} -> {destination}")
        
        if not source.exists():
            logger.error("Source file doesn't exist")
            return False, "Source file doesn't exist"
        
        if not source.is_file():
            logger.error("Source path is not a file")
            return False, "Source path is not a file"
        
        if not destination.exists():
            logger.info(f"Creating destination directory: {destination}")
            try:
                destination.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create destination directory: {e}")
                return False, f"Failed to create destination directory: {str(e)}"
        
        if not destination.is_dir():
            logger.error("Destination is not a directory")
            return False, "Destination is not a directory"
        
        # Destination file path
        dest_file = destination / source.name
        
        # Check if destination file already exists
        if dest_file.exists():
            logger.warning(f"Destination file already exists: {dest_file}")
            return False, "Destination file already exists"
        
        try:
            # Use shutil.move which handles Windows long paths better than rename
            shutil.move(str(source), str(dest_file))
            logger.info(f"Successfully moved {source} to {dest_file}")
            return True, None
        except PermissionError as e:
            error_str = str(e)
            logger.error(f"Permission denied: {error_str}")
            return False, f"Permission denied: {error_str}"
        except OSError as e:
            error_str = str(e)
            logger.error(f"OS Error: {error_str}")
            return False, f"Cannot move file: {error_str}"
        except Exception as e:
            logger.exception(f"Unexpected error moving file {source}")
            return False, f"Unexpected error: {type(e).__name__}"