"""File operation utilities for CCPlugin scripts."""

import json
from pathlib import Path
from typing import Any, Dict


def safe_load_json(file_path: Path) -> Dict[str, Any] | None:
    """Safely load JSON file with error handling.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON data as dict, or None if file doesn't exist or is invalid

    Examples:
        data = safe_load_json(Path("config.json"))
        if data:
            print(data.get("key"))
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return None


def safe_save_json(file_path: Path, data: Any) -> bool:
    """Safely save data to JSON file with error handling.

    Args:
        file_path: Path to write JSON file
        data: Data to serialize (must be JSON-serializable)

    Returns:
        True if save succeeded, False otherwise

    Examples:
        if safe_save_json(Path("output.json"), {"key": "value"}):
            print("Saved successfully")
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write('\n')
        return True
    except (IOError, OSError, TypeError):
        return False
