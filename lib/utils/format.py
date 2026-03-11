"""Formatting utilities for CCPlugin scripts."""

from datetime import datetime, timezone
from typing import Optional


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5MB", "500KB")

    Examples:
        500 -> "500.0B"
        1024 -> "1.0KB"
        1048576 -> "1.0MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def format_timestamp(timestamp_str: Optional[str]) -> str:
    """Format ISO timestamp for display.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        Formatted relative time (e.g., "5m ago", "2h ago", "3d ago")
        or absolute date for older timestamps

    Examples:
        "2024-03-11T10:30:00Z" -> "5m ago" (if recent)
        "2024-01-01T10:30:00Z" -> "2024-01-01" (if old)
    """
    if not timestamp_str:
        return "[dim]N/A[/dim]"

    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        delta = now - dt

        if delta.days < 1:
            hours = delta.seconds // 3600
            if hours < 1:
                minutes = delta.seconds // 60
                return f"[cyan]{minutes}m ago[/cyan]"
            return f"[cyan]{hours}h ago[/cyan]"
        elif delta.days < 7:
            return f"[cyan]{delta.days}d ago[/cyan]"
        else:
            return dt.strftime('%Y-%m-%d')
    except (ValueError, AttributeError):
        return str(timestamp_str)
