"""
Custom canvas-based disk usage visualization component.
"""
import customtkinter as ctk
import math
from typing import Dict, Optional, Callable
from scanner import FolderInfo
from ui.dialogs import format_size


class DiskVisualization(ctk.CTkFrame):
    """Custom pie chart showing disk usage by category."""
    
    # Color scheme for categories
    CATEGORY_COLORS = {
        "dev_tools": "#3b82f6",      # Blue
        "system": "#f59e0b",         # Orange
        "browsers": "#a855f7",       # Purple
        "user_files": "#10b981",     # Green
        "free": "#6b7280",           # Gray
        "unknown": "#9ca3af"         # Light gray
    }
    
    def __init__(self, parent, height: int = 200, on_category_click: Optional[Callable[[str], None]] = None):
        super().__init__(parent, fg_color="transparent")
        
        self.height = height
        self.on_category_click = on_category_click
        self.data: Dict[str, int] = {}
        self.total_space = 0
        self.free_space = 0
        
        # Create canvas
        self.canvas = ctk.CTkCanvas(
            self,
            height=height,
            bg="#1a1a1a",
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Bind click events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        
        self.hovered_segment = None
    
    def update_data(self, folders: list[FolderInfo], total_space_gb: float = 100, free_space_gb: float = 0):
        """Update visualization with new data."""
        # Group by category
        category_totals: Dict[str, int] = {}
        
        for folder in folders:
            if folder.exists and folder.size_bytes > 0:
                category = folder.category or "unknown"
                category_totals[category] = category_totals.get(category, 0) + folder.size_bytes
        
        self.data = category_totals
        
        # Convert total and free space to bytes
        self.total_space = int(total_space_gb * 1024 * 1024 * 1024)
        self.free_space = int(free_space_gb * 1024 * 1024 * 1024)
        
        self._redraw()
    
    def _redraw(self):
        """Redraw the pie chart."""
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width()
        if width < 10:
            return
        
        center_x = width // 2
        center_y = self.height // 2
        radius = min(center_x, center_y) - 20
        
        # Calculate total used space
        total_used = sum(self.data.values())
        total_with_free = total_used + self.free_space
        
        if total_with_free == 0:
            # No data, show empty state
            self.canvas.create_text(
                center_x, center_y,
                text="No data available",
                fill="#9ca3af",
                font=("Arial", 12)
            )
            return
        
        # Draw pie segments
        start_angle = -90  # Start at top
        segment_info = []
        
        # Draw free space segment
        if self.free_space > 0:
            angle = (self.free_space / total_with_free) * 360
            self._draw_segment(
                center_x, center_y, radius,
                start_angle, start_angle + angle,
                self.CATEGORY_COLORS["free"],
                "free"
            )
            segment_info.append({
                "category": "free",
                "start": start_angle,
                "end": start_angle + angle,
                "size": self.free_space
            })
            start_angle += angle
        
        # Draw category segments
        for category, size_bytes in sorted(self.data.items(), key=lambda x: x[1], reverse=True):
            angle = (size_bytes / total_with_free) * 360
            color = self.CATEGORY_COLORS.get(category, self.CATEGORY_COLORS["unknown"])
            
            self._draw_segment(
                center_x, center_y, radius,
                start_angle, start_angle + angle,
                color,
                category
            )
            
            segment_info.append({
                "category": category,
                "start": start_angle,
                "end": start_angle + angle,
                "size": size_bytes
            })
            
            start_angle += angle
        
        # Store segment info for click detection
        self.segment_info = segment_info
        
        # Draw legend
        self._draw_legend(width, center_y + radius + 30)
    
    def _draw_segment(self, cx, cy, radius, start_angle, end_angle, color, category):
        """Draw a pie chart segment."""
        # Convert angles to radians
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        # Calculate points
        x1 = cx + radius * math.cos(start_rad)
        y1 = cy + radius * math.sin(start_rad)
        x2 = cx + radius * math.cos(end_rad)
        y2 = cy + radius * math.sin(end_rad)
        
        # Draw segment
        self.canvas.create_arc(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            start=start_angle, extent=end_angle - start_angle,
            fill=color,
            outline=color,
            tags=(category, "segment")
        )
    
    def _draw_legend(self, width, y_start):
        """Draw legend below the chart."""
        x = 20
        y = y_start
        line_height = 20
        
        # Legend items
        items = []
        if self.free_space > 0:
            items.append(("Free Space", "free", self.free_space))
        
        for category, size_bytes in sorted(self.data.items(), key=lambda x: x[1], reverse=True):
            category_name = category.replace("_", " ").title()
            items.append((category_name, category, size_bytes))
        
        for label, category, size_bytes in items:
            # Color box
            color = self.CATEGORY_COLORS.get(category, self.CATEGORY_COLORS["unknown"])
            self.canvas.create_rectangle(
                x, y, x + 15, y + 15,
                fill=color,
                outline="",
                tags=(category, "legend")
            )
            
            # Label and size
            text = f"{label}: {format_size(size_bytes)}"
            self.canvas.create_text(
                x + 25, y + 7,
                text=text,
                fill="#ffffff",
                anchor="w",
                font=("Arial", 10),
                tags=(category, "legend")
            )
            
            y += line_height
            
            # Wrap to next column if needed
            if y > self.height - 20 and x < width // 2:
                x = width // 2 + 20
                y = y_start
    
    def _on_canvas_click(self, event):
        """Handle click on canvas."""
        if not hasattr(self, 'segment_info'):
            return
        
        # Find which segment was clicked
        clicked_category = self._get_category_at_point(event.x, event.y)
        if clicked_category and self.on_category_click:
            self.on_category_click(clicked_category)
    
    def _on_mouse_move(self, event):
        """Handle mouse movement for hover effects."""
        if not hasattr(self, 'segment_info'):
            return
        
        category = self._get_category_at_point(event.x, event.y)
        
        if category != self.hovered_segment:
            self.hovered_segment = category
            if category:
                # Show tooltip or highlight
                self.canvas.configure(cursor="hand2")
            else:
                self.canvas.configure(cursor="")
    
    def _get_category_at_point(self, x, y) -> Optional[str]:
        """Determine which category segment contains the given point."""
        if not hasattr(self, 'segment_info'):
            return None
        
        width = self.canvas.winfo_width()
        center_x = width // 2
        center_y = self.height // 2
        radius = min(center_x, center_y) - 20
        
        # Calculate angle from center
        dx = x - center_x
        dy = y - center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > radius:
            return None
        
        angle = math.degrees(math.atan2(dy, dx))
        angle = (angle + 90) % 360  # Adjust to start at top
        
        # Find matching segment
        for seg_info in self.segment_info:
            start = seg_info["start"]
            end = seg_info["end"]
            
            if start <= angle <= end:
                return seg_info["category"]
        
        return None
