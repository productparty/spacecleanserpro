"""
Auto-categorization module for unknown folders using heuristics.
"""
from pathlib import Path
from scanner import FolderInfo


def categorize_folder(folder_path: Path, folder_name: str) -> tuple[str, str]:
    """
    Auto-categorize an unknown folder using heuristics.
    
    Args:
        folder_path: Full path to the folder
        folder_name: Name of the folder
        
    Returns:
        Tuple of (category, safety_rating)
    """
    path_str = str(folder_path).lower()
    name_lower = folder_name.lower()
    
    # Check for cache/temp indicators
    cache_indicators = ["cache", "temp", "tmp", "temporary", "tmpfiles"]
    if any(indicator in path_str or indicator in name_lower for indicator in cache_indicators):
        # Determine category based on location
        if "appdata\\local\\temp" in path_str or "%temp%" in path_str.lower():
            return "system", "safe"
        elif "appdata\\local" in path_str:
            return "dev_tools", "safe"
        else:
            return "unknown", "caution"
    
    # Check for log files
    if "log" in name_lower or "logs" in path_str:
        return "system", "safe"
    
    # Check location-based categorization
    if "appdata\\local" in path_str:
        return "dev_tools", "caution"
    elif "appdata\\roaming" in path_str:
        return "user_files", "caution"
    elif "programdata" in path_str:
        return "system", "caution"
    elif "windows" in path_str:
        return "system", "keep"  # Be conservative with Windows folders
    elif "program files" in path_str:
        return "system", "keep"  # Be conservative with Program Files
    
    # Default: unknown with caution
    return "unknown", "caution"


def enhance_folder_info(folder_info: FolderInfo) -> FolderInfo:
    """
    Enhance a FolderInfo with auto-categorization if category is unknown.
    
    Args:
        folder_info: FolderInfo to enhance
        
    Returns:
        Enhanced FolderInfo (may be same object if already categorized)
    """
    if folder_info.category == "unknown" and folder_info.full_path != Path("RECYCLE_BIN"):
        category, safety = categorize_folder(folder_info.full_path, folder_info.name)
        folder_info.category = category
        if folder_info.safety == "keep":  # Don't override explicit "keep"
            pass
        elif safety == "safe" and folder_info.safety == "caution":
            # Upgrade to safe if heuristic suggests it
            folder_info.safety = "safe"
        elif folder_info.safety not in ["safe", "caution", "keep"]:
            folder_info.safety = safety
    
    return folder_info
