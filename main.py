"""
Space Cleanser Pro - Main entry point.
"""
import customtkinter as ctk
import sys
import tkinter.messagebox as messagebox
from ui.dashboard import Dashboard
from admin_helper import is_admin, request_elevation, get_admin_message

# Version string for display in window title and releases
VERSION = "1.1.4"


def main():
    """Launch the application."""
    # Set appearance mode
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create main window
    root = ctk.CTk()
    root.title(f"Space Cleanser Pro v{VERSION}")
    root.geometry("1200x800")
    root.minsize(1000, 700)
    
    # Show info about admin access if not running as admin
    if not is_admin():
        # Show a one-time info message (non-blocking)
        root.after(500, lambda: _show_admin_info(root))
    
    # Create tabview for multiple views
    tabview = ctk.CTkTabview(root)
    tabview.pack(fill="both", expand=True, padx=0, pady=0)
    
    # Add tabs
    tabview.add("Cache Cleaner")
    tabview.add("Discovery")
    
    # Create dashboard in Cache Cleaner tab
    from ui.dashboard import Dashboard
    dashboard = Dashboard(tabview.tab("Cache Cleaner"))
    dashboard.pack(fill="both", expand=True)
    
    # Create discovery panel in Discovery tab
    from ui.discovery_panel import DiscoveryPanel
    discovery_panel = DiscoveryPanel(tabview.tab("Discovery"))
    discovery_panel.pack(fill="both", expand=True)
    
    # Run app
    root.mainloop()


def _show_admin_info(root):
    """Show informational message about admin access (non-blocking)."""
    try:
        response = messagebox.askyesno(
            "Administrator Access (Optional)",
            (
                "Space Cleanser Pro can run without administrator privileges.\n\n"
                "Without admin access, some system folders will be skipped:\n"
                "• Windows\\Temp\n"
                "• Windows Update files\n"
                "• System logs\n\n"
                "Would you like to restart with administrator privileges for full scanning?\n\n"
                "You can always continue without admin - the app will work fine."
            )
        )
        
        if response:
            try:
                if request_elevation():
                    # App will restart as admin
                    root.quit()
                    sys.exit(0)
                else:
                    # Elevation failed or was cancelled - continue normally
                    pass
            except Exception as e:
                # If elevation fails for any reason, just continue
                print(f"Admin elevation not available: {e}")
                pass
    except Exception as e:
        # If dialog fails, just continue
        print(f"Could not show admin dialog: {e}")
        pass


if __name__ == "__main__":
    main()
