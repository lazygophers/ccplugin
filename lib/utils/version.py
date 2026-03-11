"""Version parsing utilities for CCPlugin scripts."""

from typing import Tuple


# Version parts constants
VERSION_PARTS_STANDARD = 3
VERSION_PARTS_WITH_BUILD = 4


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string to tuple for comparison.

    Examples:
        '0.0.11' -> (0, 0, 11)
        '1.2' -> (1, 2, 0)
        '1' -> (1, 0, 0)

    Args:
        version_str: Version string (1-3 parts)

    Returns:
        Tuple of (major, minor, patch) with missing parts as 0

    Note:
        This is a simplified parser for version display sorting.
        For strict version parsing, use parse_version() from update_version.py.
    """
    try:
        parts = version_str.split(".")
        if len(parts) >= 3:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        elif len(parts) == 2:
            return (int(parts[0]), int(parts[1]), 0)
        elif len(parts) == 1:
            return (int(parts[0]), 0, 0)
    except (ValueError, AttributeError):
        pass
    return (0, 0, 0)
