"""
Smart recommendations engine for disk cleanup suggestions.
"""
from dataclasses import dataclass
from typing import List
from scanner import FolderInfo
from ui.dialogs import format_size


@dataclass
class RecommendationItem:
    """A single item in a recommendation."""
    name: str
    size_bytes: int
    description: str


@dataclass
class Recommendation:
    """A recommendation group."""
    title: str
    icon: str  # "target", "warning", "info"
    items: List[RecommendationItem]
    total_bytes: int
    action_hint: str


def generate_recommendations(folders: List[FolderInfo]) -> List[Recommendation]:
    """
    Analyze scan results and generate smart recommendations.
    
    Args:
        folders: List of scanned folders
        
    Returns:
        List of Recommendation objects
    """
    recommendations = []
    
    # Quick Wins - Safe items
    safe_folders = [f for f in folders if f.safety == "safe" and f.exists and f.size_bytes > 0]
    if safe_folders:
        quick_wins_items = [
            RecommendationItem(
                name=f.name,
                size_bytes=f.size_bytes,
                description=f.description[:60] + "..." if len(f.description) > 60 else f.description
            )
            for f in safe_folders[:5]  # Top 5 safe items
        ]
        total_safe = sum(f.size_bytes for f in safe_folders)
        
        recommendations.append(Recommendation(
            title="Quick Wins",
            icon="target",
            items=quick_wins_items,
            total_bytes=total_safe,
            action_hint=f"You can safely free {format_size(total_safe)} by cleaning these items."
        ))
    
    # Consider Reviewing - Caution items
    caution_folders = [f for f in folders if f.safety == "caution" and f.exists and f.size_bytes > 0]
    if caution_folders:
        caution_items = [
            RecommendationItem(
                name=f.name,
                size_bytes=f.size_bytes,
                description=f.description[:60] + "..." if len(f.description) > 60 else f.description
            )
            for f in caution_folders[:5]  # Top 5 caution items
        ]
        total_caution = sum(f.size_bytes for f in caution_folders)
        
        recommendations.append(Recommendation(
            title="Consider Reviewing",
            icon="warning",
            items=caution_items,
            total_bytes=total_caution,
            action_hint=f"Review these {len(caution_folders)} items before cleaning ({format_size(total_caution)} total)."
        ))
    
    # Large Files Info - Files over 1GB
    large_folders = [f for f in folders if f.size_bytes > 1024 * 1024 * 1024 and f.exists]
    if large_folders:
        large_items = [
            RecommendationItem(
                name=f.name,
                size_bytes=f.size_bytes,
                description=f"{format_size(f.size_bytes)} - {f.category}"
            )
            for f in sorted(large_folders, key=lambda x: x.size_bytes, reverse=True)[:5]
        ]
        total_large = sum(f.size_bytes for f in large_folders)
        
        recommendations.append(Recommendation(
            title="Large Items Detected",
            icon="info",
            items=large_items,
            total_bytes=total_large,
            action_hint=f"Found {len(large_folders)} items larger than 1GB ({format_size(total_large)} total)."
        ))
    
    return recommendations
