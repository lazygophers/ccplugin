"""User-level cortex config loader (`~/.cortex/config.json`).

Flat schema (all fields optional):
    {
      "vault": "/abs/path/to/vault",
      "lang": "zh-CN",
      "settings": "/abs/path/to/claude-settings.json",
      "install_path": "/abs/path/to/cortex-plugin"
    }

Loader does not validate field semantics (path existence, locale code); that
is the responsibility of `cortex config validate`. JSON syntax errors are
fail-fast via :class:`ConfigSyntaxError` so consumers can surface a clear
remediation message.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_PATH = Path.home() / ".cortex" / "config.json"

# Flat schema keys; kept here so CLI / doctor can introspect.
KNOWN_KEYS = ("vault", "lang", "settings", "install_path")


class ConfigSyntaxError(Exception):
    """Raised when `~/.cortex/config.json` exists but has invalid JSON."""


def _config_path() -> Path:
    # Re-resolve each call so tests that monkeypatch $HOME take effect.
    return Path(os.path.expanduser("~")) / ".cortex" / "config.json"


def load_config() -> dict:
    """Return parsed config dict, or `{}` if the file is absent.

    Raises:
        ConfigSyntaxError: file exists but contains invalid JSON or
            non-object root.
    """
    path = _config_path()
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigSyntaxError(
            f"config syntax error at {path}: cannot read ({e})"
        ) from e
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ConfigSyntaxError(
            f"config syntax error at {path}: {e.msg} (line {e.lineno} col {e.colno})"
        ) from e
    if not isinstance(data, dict):
        raise ConfigSyntaxError(
            f"config syntax error at {path}: root must be a JSON object"
        )
    return data


def resolve(key: str, env_var: str | None, fallback: Any) -> Any:
    """Resolve a value with priority: env > config > fallback.

    Empty-string values (both env and config) are treated as unset and
    fall through to the next source. This keeps `CORTEX_VAULT=""` (a
    common shell mistake) from masking a valid config entry.

    NOTE: kept for backward compatibility (install.sh / bootstrap paths).
    Plugin business code SHOULD use the env-free helpers below.
    """
    if env_var:
        env_val = os.environ.get(env_var)
        if env_val is not None and env_val != "":
            return env_val
    cfg = load_config()
    val = cfg.get(key)
    if val is not None and val != "":
        return val
    return fallback


# --- Config-only helpers (env-free) -------------------------------------
# Plugin business code uses these. Env vars are reserved for
# platform-contract (CLAUDE_PLUGIN_ROOT) and internal runtime communication
# (CORTEX_JOB_LABEL, CORTEX_STREAM_TEE_FILE).


def get_config_value(key: str, default: Any = None) -> Any:
    """Return config[key] from ~/.cortex/config.json, or `default` if absent."""
    try:
        cfg = load_config()
    except ConfigSyntaxError:
        return default
    val = cfg.get(key)
    if val is None or val == "":
        return default
    return val


def get_vault() -> Path | None:
    v = get_config_value("vault")
    return Path(os.path.expanduser(v)) if v else None


def get_plugin_root() -> Path | None:
    p = get_config_value("install_path")
    return Path(os.path.expanduser(p)) if p else None


def get_lang(default: str = "zh-CN") -> str:
    return str(get_config_value("lang", default) or default)


def get_settings_path() -> Path:
    s = get_config_value("settings")
    if s:
        return Path(os.path.expanduser(s))
    return Path.home() / ".claude" / "settings.json"


def get_timeout(default: int = 300) -> int:
    try:
        return int(get_config_value("timeout_default", default) or default)
    except (TypeError, ValueError):
        return default
