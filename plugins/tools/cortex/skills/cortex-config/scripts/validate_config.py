#!/usr/bin/env python3
"""cortex-config validate — read-only schema check for both config sources.

Sources:
    ~/.cortex/config.json                              — user-level
    $CORTEX_VAULT/.cortex/config/{digest,enrich,tags}.yaml — vault-level

Behavior:
    - emits JSON {ok, errors, warnings} on stdout
    - exit 0 if ok or only warnings, exit 1 if errors
    - never modifies any file
    - missing files are OK (defaults apply)

Schema mirrors references/schema.md. Keep both in sync.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ---------- schema -----------------------------------------------------------

_LANG_RE = re.compile(r"^[a-zA-Z]{2,3}(-[A-Z]{2})?$")

_USER_KEYS = {
    "vault": {"type": "path", "required": True, "exists": True},
    "lang": {"type": "lang", "required": False, "default": "zh-CN"},
    "settings": {"type": "path", "required": False, "exists": True},
    "install_path": {"type": "path", "required": False, "exists": True},
    "timeout_default": {"type": "int", "required": False, "default": 600, "min": 60, "max": 7200},
}

_MERMAID_TYPES = {
    "flowchart", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram",
    "journey", "gantt", "pie", "mindmap", "timeline", "gitGraph",
    "requirementDiagram", "c4Context", "quadrantChart", "sankey", "xychart",
}

_TAG_NAMING_ENUM = {"kebab-case", "snake_case"}


# ---------- helpers ----------------------------------------------------------

def _err(errors: list[dict], file: str, key: str, issue: str) -> None:
    errors.append({"file": file, "key": key, "issue": issue})


def _warn(warnings: list[dict], file: str, key: str, issue: str) -> None:
    warnings.append({"file": file, "key": key, "issue": issue})


def _load_yaml(path: Path) -> tuple[Any, str | None]:
    if not path.exists():
        return None, None
    try:
        import yaml  # type: ignore
    except ImportError:
        return None, "PyYAML not installed (pip install pyyaml)"
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return None, f"yaml parse error: {e}"
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, f"root must be mapping, got {type(data).__name__}"
    return data, None


def _user_config_path() -> Path:
    return Path.home() / ".cortex" / "config.json"


def _resolve_vault(user_cfg: dict | None) -> Path | None:
    env_v = os.environ.get("CORTEX_VAULT")
    if env_v:
        return Path(env_v).expanduser()
    if user_cfg and user_cfg.get("vault"):
        return Path(user_cfg["vault"]).expanduser()
    return None


# ---------- validators -------------------------------------------------------

def validate_user_config(errors: list[dict], warnings: list[dict]) -> dict | None:
    path = _user_config_path()
    if not path.exists():
        _warn(warnings, "~/.cortex/config.json", "*", "file absent (run install.sh)")
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        _err(errors, "~/.cortex/config.json", "*", f"json parse: {e}")
        return None
    if not isinstance(cfg, dict):
        _err(errors, "~/.cortex/config.json", "*", "root must be object")
        return None

    file_label = "~/.cortex/config.json"

    for key, spec in _USER_KEYS.items():
        if spec.get("required") and not cfg.get(key):
            _err(errors, file_label, key, "required field missing or empty")

    for key, val in cfg.items():
        if key not in _USER_KEYS:
            _warn(warnings, file_label, key, "unknown key")
            continue
        if val is None or val == "":
            continue
        spec = _USER_KEYS[key]
        t = spec["type"]
        if t == "path":
            if not isinstance(val, str):
                _err(errors, file_label, key, f"expected str path, got {type(val).__name__}")
                continue
            if spec.get("exists") and not Path(val).expanduser().exists():
                _err(errors, file_label, key, f"{val} does not exist")
        elif t == "lang":
            if not isinstance(val, str) or not _LANG_RE.match(val):
                _err(errors, file_label, key, f"invalid lang code '{val}'")
        elif t == "int":
            if not isinstance(val, int) or isinstance(val, bool):
                _err(errors, file_label, key, f"expected int, got {type(val).__name__}")
                continue
            lo, hi = spec.get("min"), spec.get("max")
            if lo is not None and val < lo:
                _err(errors, file_label, key, f"out of range {lo}-{hi}, got {val}")
            if hi is not None and val > hi:
                _err(errors, file_label, key, f"out of range {lo}-{hi}, got {val}")

    return cfg


def validate_digest_yaml(vault: Path, errors: list[dict], warnings: list[dict]) -> None:
    path = vault / ".cortex" / "config" / "digest.yaml"
    file_label = "digest.yaml"
    data, err = _load_yaml(path)
    if err:
        _err(errors, file_label, "*", err)
        return
    if data is None:
        return  # missing OK

    stages = data.get("stages")
    if stages is not None:
        if not isinstance(stages, dict):
            _err(errors, file_label, "stages", f"expected mapping, got {type(stages).__name__}")
        else:
            for sk in ("consolidate", "enrich", "verify"):
                if sk in stages and not isinstance(stages[sk], bool):
                    _err(errors, file_label, f"stages.{sk}", f"expected bool, got {type(stages[sk]).__name__}")
            for k in stages:
                if k not in ("consolidate", "enrich", "verify"):
                    _warn(warnings, file_label, f"stages.{k}", "unknown stage")

    age = data.get("incremental_max_age_days")
    if age is not None:
        if not isinstance(age, int) or isinstance(age, bool):
            _err(errors, file_label, "incremental_max_age_days", f"expected int 1-365, got {type(age).__name__}")
        elif not (1 <= age <= 365):
            _err(errors, file_label, "incremental_max_age_days", f"out of range 1-365, got {age}")

    aliases = data.get("domain_aliases")
    if aliases is not None:
        if not isinstance(aliases, dict):
            _err(errors, file_label, "domain_aliases", f"expected mapping, got {type(aliases).__name__}")
        else:
            for ak, av in aliases.items():
                if not isinstance(ak, str) or not ak:
                    _err(errors, file_label, f"domain_aliases.{ak!r}", "key must be non-empty str")
                if not isinstance(av, str) or not av:
                    _err(errors, file_label, f"domain_aliases.{ak}", "value must be non-empty str")

    for k in data:
        if k not in ("stages", "incremental_max_age_days", "domain_aliases"):
            _warn(warnings, file_label, k, "unknown key")


def validate_enrich_yaml(vault: Path, errors: list[dict], warnings: list[dict]) -> None:
    path = vault / ".cortex" / "config" / "enrich.yaml"
    file_label = "enrich.yaml"
    data, err = _load_yaml(path)
    if err:
        _err(errors, file_label, "*", err)
        return
    if data is None:
        return

    wl = data.get("mermaid_whitelist")
    if wl is not None:
        if not isinstance(wl, list):
            _err(errors, file_label, "mermaid_whitelist", f"expected list, got {type(wl).__name__}")
        else:
            for i, item in enumerate(wl):
                if not isinstance(item, str):
                    _err(errors, file_label, f"mermaid_whitelist[{i}]", f"expected str, got {type(item).__name__}")
                elif item not in _MERMAID_TYPES:
                    _warn(warnings, file_label, f"mermaid_whitelist[{i}]", f"unknown mermaid type '{item}'")

    sp = data.get("skip_paths")
    if sp is not None:
        if not isinstance(sp, list):
            _err(errors, file_label, "skip_paths", f"expected list, got {type(sp).__name__}")
        else:
            for i, item in enumerate(sp):
                if not isinstance(item, str) or not item:
                    _err(errors, file_label, f"skip_paths[{i}]", "expected non-empty str")

    for k in data:
        if k not in ("mermaid_whitelist", "skip_paths"):
            _warn(warnings, file_label, k, "unknown key")


def validate_tags_yaml(vault: Path, errors: list[dict], warnings: list[dict]) -> None:
    path = vault / ".cortex" / "config" / "tags.yaml"
    file_label = "tags.yaml"
    data, err = _load_yaml(path)
    if err:
        _err(errors, file_label, "*", err)
        return
    if data is None:
        return

    syn = data.get("alias_synonyms")
    if syn is not None:
        if not isinstance(syn, dict):
            _err(errors, file_label, "alias_synonyms", f"expected mapping, got {type(syn).__name__}")
        else:
            for sk, sv in syn.items():
                if not isinstance(sk, str) or not sk:
                    _err(errors, file_label, f"alias_synonyms.{sk!r}", "key must be non-empty str")
                if not isinstance(sv, list):
                    _err(errors, file_label, f"alias_synonyms.{sk}", f"expected list, got {type(sv).__name__}")
                elif not sv:
                    _err(errors, file_label, f"alias_synonyms.{sk}", "list must be non-empty")
                else:
                    for i, e in enumerate(sv):
                        if not isinstance(e, str) or not e:
                            _err(errors, file_label, f"alias_synonyms.{sk}[{i}]", "expected non-empty str")

    naming = data.get("tag_naming")
    if naming is not None:
        if not isinstance(naming, str):
            _err(errors, file_label, "tag_naming", f"expected str, got {type(naming).__name__}")
        elif naming not in _TAG_NAMING_ENUM:
            _err(errors, file_label, "tag_naming", f"expected enum {sorted(_TAG_NAMING_ENUM)}, got '{naming}'")

    for k in data:
        if k not in ("alias_synonyms", "tag_naming"):
            _warn(warnings, file_label, k, "unknown key")


# ---------- main -------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    errors: list[dict] = []
    warnings: list[dict] = []

    user_cfg = validate_user_config(errors, warnings)
    vault = _resolve_vault(user_cfg)

    if vault is None:
        _warn(warnings, "*", "vault", "vault not resolved (skip yaml validation)")
    elif not vault.exists():
        _warn(warnings, "*", "vault", f"vault path {vault} not found (skip yaml validation)")
    else:
        validate_digest_yaml(vault, errors, warnings)
        validate_enrich_yaml(vault, errors, warnings)
        validate_tags_yaml(vault, errors, warnings)

    result = {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }

    if errors:
        # Stop hook displays this in stderr; keep stdout JSON for programmatic use.
        for e in errors:
            print(f"[cortex-config WARN] {e['file']}/{e['key']}: {e['issue']}", file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
