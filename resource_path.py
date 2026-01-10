"""
Resource path helper for bundled executables.

Handles path resolution for resources (like JSON config files) that need to work
both when running from source and when bundled as a PyInstaller executable.
"""
import sys
import os


def get_resource_path(relative_path: str) -> str:
    """
    Get absolute path to resource, works for dev and PyInstaller bundle.
    
    When running as a PyInstaller bundle, resources are extracted to a temp
    directory (sys._MEIPASS). When running from source, resources are in the
    same directory as the script.
    
    Args:
        relative_path: Path relative to the resource directory (e.g., "folder_defs.json")
        
    Returns:
        Absolute path to the resource file
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled executable - resources are in temp extraction folder
        base_path = sys._MEIPASS
    else:
        # Running from source - resources are in the same directory as this file
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)
