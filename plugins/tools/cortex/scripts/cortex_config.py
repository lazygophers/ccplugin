#!/usr/bin/env python3
"""`cortex config` CLI — read / write / init / validate `~/.cortex/config.json`.

Subcommands:
    get <key>                 print config[key] (empty string if unset)
    set <key> <value>         write single field with semantic validation
    init [--non-interactive]  interactive prompt OR flag-driven write
    validate                  check JSON syntax + field semantics

Reuses the loader at `hooks/_lib/cortex_config.py` so config-format truth lives
in one place (see code-reuse guide).

Exit codes:
    0  success / config absent (for validate)
    1  semantic failure (invalid path, JSON broken, validate failed)
    2  usage error (unknown key, unknown subcommand)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

# Reuse the loader. cortex_config lives at <plugin>/hooks/_lib/cortex_config.py.
# This script shares the module name `cortex_config`, so load the loader via
# importlib from an explicit path to dodge the name collision.
import importlib.util as _ilu

_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_LOADER_PATH = _PLUGIN_ROOT / "hooks" / "_lib" / "cortex_config.py"
_spec = _ilu.spec_from_file_location("_cortex_config_loader", _LOADER_PATH)
_loader_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_loader_mod)

KNOWN_KEYS = _loader_mod.KNOWN_KEYS
ConfigSyntaxError = _loader_mod.ConfigSyntaxError
_config_path = _loader_mod._config_path
load_config = _loader_mod.load_config

# Subset of KNOWN_KEYS that map to filesystem paths.
_PATH_KEYS = ("vault", "settings", "install_path")
_LANG_RE = re.compile(r"^[a-zA-Z]{2,3}(-[A-Z]{2})?$")


def _validate_field(key: str, value: str) -> str | None:
    """Return None if valid, else error message."""
    if key not in KNOWN_KEYS:
        return f"unknown key '{key}'"
    if key == "lang":
        if not _LANG_RE.match(value):
            return f"invalid lang code '{value}'"
        return None
    if key in _PATH_KEYS:
        if not Path(value).expanduser().exists():
            return f"{value} does not exist"
        return None
    return None


def _atomic_write(path: Path, data: dict) -> None:
    """Write JSON atomically: tmp file in same dir + os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".config.", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def cmd_get(args: argparse.Namespace) -> int:
    key = args.key
    if key not in KNOWN_KEYS:
        print(f"get: unknown key '{key}'", file=sys.stderr)
        return 2
    try:
        cfg = load_config()
    except ConfigSyntaxError as e:
        print(str(e), file=sys.stderr)
        return 1
    val = cfg.get(key, "")
    print(val if val is not None else "")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    key, value = args.key, args.value
    if key not in KNOWN_KEYS:
        print(f"set: unknown key '{key}'", file=sys.stderr)
        return 2
    err = _validate_field(key, value)
    if err:
        print(f"set: {err}", file=sys.stderr)
        return 1
    try:
        cfg = load_config()
    except ConfigSyntaxError as e:
        print(str(e), file=sys.stderr)
        return 1
    cfg[key] = value
    _atomic_write(_config_path(), cfg)
    return 0


def _prompt(label: str, default: str | None) -> str:
    suffix = f" [{default}]" if default else ""
    try:
        raw = input(f"{label}{suffix}: ").strip()
    except EOFError:
        raw = ""
    if not raw and default:
        return default
    return raw


def cmd_init(args: argparse.Namespace) -> int:
    # Flag map → config keys.
    flag_map: dict[str, Any] = {
        "vault": args.vault,
        "lang": args.lang,
        "settings": args.settings,
        "install_path": args.install_path,
    }

    try:
        existing = load_config()
    except ConfigSyntaxError as e:
        print(str(e), file=sys.stderr)
        return 1

    out: dict[str, str] = {}

    if args.non_interactive:
        for key, val in flag_map.items():
            if val is None or val == "":
                # Preserve existing entry if user didn't pass the flag.
                if key in existing and existing[key]:
                    out[key] = existing[key]
                continue
            err = _validate_field(key, val)
            if err:
                print(f"init: {err}", file=sys.stderr)
                return 1
            out[key] = val
    else:
        # Interactive: prompt every key. Default = flag > existing config.
        # Env vars are NOT consulted (config is single source of truth per project rules).
        for key in KNOWN_KEYS:
            default = flag_map.get(key) or existing.get(key)
            val = _prompt(f"{key}", default)
            if not val:
                continue
            err = _validate_field(key, val)
            if err:
                print(f"init: {err}", file=sys.stderr)
                return 1
            out[key] = val

    _atomic_write(_config_path(), out)
    _use_color = sys.stderr.isatty() and not os.environ.get("NO_COLOR")
    if _use_color:
        print(
            f"\033[36m[cortex_config]\033[0m \033[32m✓\033[0m wrote "
            f"\033[1m{_config_path()}\033[0m",
            file=sys.stderr,
        )
    else:
        print(f"wrote {_config_path()}", file=sys.stderr)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = _config_path()
    if not path.exists():
        print(f"config absent: {path}")
        return 0
    try:
        cfg = load_config()
    except ConfigSyntaxError as e:
        print(str(e), file=sys.stderr)
        return 1
    errors: list[str] = []
    for key, val in cfg.items():
        if key not in KNOWN_KEYS:
            errors.append(f"  {key}: unknown key")
            continue
        if not isinstance(val, str) or val == "":
            continue
        err = _validate_field(key, val)
        if err:
            errors.append(f"  {key}: {err}")
    if errors:
        print(f"config invalid: {path}")
        for line in errors:
            print(line)
        return 1
    print(f"config ok: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cortex_config", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("get", help="print config[key]")
    g.add_argument("key")
    g.set_defaults(func=cmd_get)

    s = sub.add_parser("set", help="write single field")
    s.add_argument("key")
    s.add_argument("value")
    s.set_defaults(func=cmd_set)

    i = sub.add_parser("init", help="interactive or flag-driven write")
    i.add_argument("--non-interactive", action="store_true")
    i.add_argument("--vault")
    i.add_argument("--lang")
    i.add_argument("--settings")
    i.add_argument("--install-path", dest="install_path")
    i.set_defaults(func=cmd_init)

    v = sub.add_parser("validate", help="check syntax + field semantics")
    v.set_defaults(func=cmd_validate)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
