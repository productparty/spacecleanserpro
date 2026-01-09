"""
Windows admin elevation helper for accessing system folders.
"""
import sys
import ctypes
import os
from pathlib import Path


def is_admin() -> bool:
    """Check if the current process is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def request_elevation() -> bool:
    """
    Re-launch the current script with administrator privileges.
    
    Returns:
        True if elevation was requested successfully, False if user cancelled or error
    """
    if is_admin():
        return True
    
    # Get the script path
    script_path = sys.executable
    
    # Get the script file path (main.py)
    script_file = sys.argv[0] if len(sys.argv) > 0 else "main.py"
    
    # Make sure script_file is an absolute path
    if not os.path.isabs(script_file):
        script_file = os.path.join(os.getcwd(), script_file)
    
    # Build command line arguments - use absolute path
    script_args = f'"{script_file}"'
    
    # Use ShellExecuteW to request elevation
    try:
        # ShellExecuteW returns > 32 on success
        # Returns 42 if user clicks "No" on UAC prompt
        # Returns 1223 if user cancels UAC prompt
        # Returns 0 or negative on error
        result = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",  # Request elevation
            script_path,
            script_args,
            os.getcwd(),  # Working directory
            1  # SW_SHOWNORMAL
        )
        
        # Check result codes
        if result > 32:
            return True
        elif result == 42:
            # User clicked "No" on UAC
            return False
        elif result == 1223:
            # User cancelled UAC
            return False
        else:
            # Other error (might be blocked by Windows Defender)
            return False
    except Exception as e:
        print(f"Failed to request elevation: {e}")
        return False


def check_admin_required(folder_path: Path) -> bool:
    """
    Check if a folder path requires admin access.
    
    Args:
        folder_path: Path to check
        
    Returns:
        True if admin is likely required
    """
    path_str = str(folder_path).lower()
    
    # System folders that typically require admin
    admin_paths = [
        r"c:\windows\temp",
        r"c:\windows\logs",
        r"c:\windows\softwaredistribution",
        r"c:\programdata",
    ]
    
    return any(admin_path in path_str for admin_path in admin_paths)


def get_admin_message() -> str:
    """Get a user-friendly message explaining why admin is needed."""
    return (
        "Some folders require administrator access to scan:\n\n"
        "• Windows temporary files\n"
        "• Windows Update files\n"
        "• System log files\n\n"
        "Would you like to restart Space Cleanser Pro with administrator privileges?\n\n"
        "This is safe - the app only scans and displays information."
    )
