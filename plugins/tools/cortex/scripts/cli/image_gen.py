#!/usr/bin/env python3
"""cortex image_gen — text-to-image CLI.

Driven by `<vault>/.cortex/config/image-gen.yaml` (multi-provider, OpenAI-compat).

Subcommands:
    probe   [--config NAME] [--all]      ping providers, mark untrusted ones disabled
    generate <prompt> [--config NAME] [--output PATH] [--size WxH] [--style S]
    list    [--all]                      tabulate providers

OUTPUT:
    JSON on stdout (for `probe` / `generate`); plaintext table (for `list`).

Network: stdlib `urllib` only. No new deps. `PyYAML` soft-required to load yaml
(`ruamel.yaml` optional for round-trip with comments).

Security:
    api_key_env > api_key fallback. When logging, keys are masked (80% middle).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import random
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


# ---------- yaml IO ----------------------------------------------------------

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
    except Exception as e:  # noqa: BLE001
        return None, f"yaml parse error: {e}"
    return data, None


def _dump_yaml(path: Path, data: Any) -> tuple[bool, str | None]:
    """Write yaml back. Comments lost when ruamel.yaml absent (warn)."""
    try:
        from ruamel.yaml import YAML  # type: ignore
        yml = YAML()
        yml.preserve_quotes = True
        with path.open("w", encoding="utf-8") as f:
            yml.dump(data, f)
        return True, None
    except ImportError:
        pass
    try:
        import yaml  # type: ignore
    except ImportError:
        return False, "PyYAML not installed"
    try:
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        return True, "ruamel.yaml absent — comments not preserved"
    except Exception as e:  # noqa: BLE001
        return False, f"yaml dump error: {e}"


# ---------- vault / config ---------------------------------------------------

def _resolve_vault() -> Path | None:
    v = os.environ.get("CORTEX_VAULT") or os.environ.get("CORTEX_VAULT_PATH")
    if v:
        return Path(v).expanduser()
    cfg = Path.home() / ".cortex" / "config.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("vault"):
                return Path(data["vault"]).expanduser()
        except Exception:  # noqa: BLE001
            pass
    return None


def _config_path(vault: Path) -> Path:
    return vault / ".cortex" / "config" / "image-gen.yaml"


def _load_config(vault: Path) -> dict:
    data, err = _load_yaml(_config_path(vault))
    if err:
        print(f"[image_gen] {err}", file=sys.stderr)
        sys.exit(1)
    if data is None:
        return {"providers": [], "defaults": {"random_selection": True,
                                              "output_dir": "_assets/images"}}
    if not isinstance(data, dict):
        print(f"[image_gen] image-gen.yaml root must be mapping", file=sys.stderr)
        sys.exit(1)
    data.setdefault("providers", [])
    data.setdefault("defaults", {})
    data["defaults"].setdefault("random_selection", True)
    data["defaults"].setdefault("output_dir", "_assets/images")
    return data


def _save_config(vault: Path, data: dict) -> None:
    ok, warn = _dump_yaml(_config_path(vault), data)
    if not ok:
        print(f"[image_gen] save config failed: {warn}", file=sys.stderr)
        sys.exit(1)
    if warn:
        print(f"[image_gen] {warn}", file=sys.stderr)


# ---------- helpers ----------------------------------------------------------

def _mask(s: str) -> str:
    if not s or len(s) < 8:
        return "***"
    keep = max(2, len(s) // 10)
    return f"{s[:keep]}***{s[-keep:]}"


def _resolve_api_key(p: dict) -> tuple[str | None, str | None]:
    """Returns (key, source). source ∈ {"env", "inline", None}."""
    env_name = p.get("api_key_env")
    if env_name:
        v = os.environ.get(env_name)
        if v:
            return v, "env"
    inline = p.get("api_key")
    if inline:
        return inline, "inline"
    return None, None


def _active_providers(cfg: dict, include_disabled: bool = False) -> list[dict]:
    out = []
    for p in cfg.get("providers", []):
        if not isinstance(p, dict):
            continue
        if not include_disabled and p.get("disabled"):
            continue
        out.append(p)
    return out


def _find_by_name(cfg: dict, name: str) -> dict | None:
    for p in cfg.get("providers", []):
        if isinstance(p, dict) and p.get("name") == name:
            return p
    return None


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _http_request(url: str, method: str = "GET", headers: dict | None = None,
                  body: bytes | None = None, timeout: int = 30) -> tuple[int, bytes, str | None]:
    req = urllib.request.Request(url, data=body, method=method,
                                 headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(), None
    except urllib.error.HTTPError as e:
        try:
            data = e.read()
        except Exception:  # noqa: BLE001
            data = b""
        return e.code, data, None
    except socket.timeout:
        return 0, b"", "timeout"
    except urllib.error.URLError as e:
        return 0, b"", f"network: {e.reason}"
    except Exception as e:  # noqa: BLE001
        return 0, b"", f"error: {e}"


# ---------- probe ------------------------------------------------------------

def _models_url(endpoint: str) -> str:
    """Derive `/v1/models` URL from images endpoint, best-effort."""
    u = urlparse(endpoint)
    parts = u.path.rstrip("/").split("/")
    # strip trailing `/images/generations` segments if present
    while parts and parts[-1] in ("generations", "images"):
        parts.pop()
    base = parts or [""]
    new_path = "/".join(base) + "/models"
    if not new_path.startswith("/"):
        new_path = "/" + new_path
    return f"{u.scheme}://{u.netloc}{new_path}"


def _probe_one(p: dict) -> dict:
    """Return {name, status, ok, error}. Mutates p (last_check/last_status/disabled)."""
    name = p.get("name", "?")
    timeout = int(p.get("timeout_seconds") or 30)
    key, _src = _resolve_api_key(p)
    headers = {"Accept": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    if isinstance(p.get("extra_headers"), dict):
        for k, v in p["extra_headers"].items():
            headers[str(k)] = str(v)

    endpoint = p.get("endpoint") or ""
    status, _data, err = _http_request(_models_url(endpoint), method="GET",
                                       headers=headers, timeout=timeout)

    p["last_check"] = _now_iso()
    p["last_status"] = status

    auth_error_codes = (401, 403, 404)
    is_healthy = 200 <= status < 300
    is_auth_err = status in auth_error_codes

    if is_healthy:
        if p.get("disabled"):
            p["disabled"] = False  # auto-recover
        return {"name": name, "status": status, "ok": True, "error": None}

    if is_auth_err and not p.get("trusted"):
        p["disabled"] = True

    return {
        "name": name,
        "status": status,
        "ok": False,
        "error": err or f"http {status}",
    }


def cmd_probe(args: argparse.Namespace) -> int:
    vault = _resolve_vault()
    if vault is None:
        print('{"ok": false, "error": "vault not resolved"}', file=sys.stdout)
        return 1
    cfg = _load_config(vault)

    targets: list[dict]
    if args.config:
        p = _find_by_name(cfg, args.config)
        if p is None:
            print(f'{{"ok": false, "error": "provider not found: {args.config}"}}')
            return 1
        targets = [p]
    else:
        targets = _active_providers(cfg, include_disabled=bool(args.all))

    healthy, disabled_now, errors = [], [], []
    for p in targets:
        r = _probe_one(p)
        if r["ok"]:
            healthy.append(r["name"])
        else:
            errors.append(r)
            if p.get("disabled"):
                disabled_now.append(r["name"])

    if targets:
        _save_config(vault, cfg)

    print(json.dumps({
        "checked": len(targets),
        "healthy": healthy,
        "disabled_now": disabled_now,
        "errors": errors,
    }, ensure_ascii=False, indent=2))
    return 0


# ---------- generate ---------------------------------------------------------

def _select_provider(cfg: dict, name: str | None) -> dict | None:
    if name:
        p = _find_by_name(cfg, name)
        if p and not p.get("disabled"):
            return p
        return None
    active = _active_providers(cfg)
    if not active:
        return None
    if cfg.get("defaults", {}).get("random_selection", True):
        return random.choice(active)
    return active[0]


def _sha8(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]


def _download(url: str, dst: Path, timeout: int = 60) -> tuple[bool, str | None]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "cortex-image-gen/1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        return True, None
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def cmd_generate(args: argparse.Namespace) -> int:
    vault = _resolve_vault()
    if vault is None:
        print('{"ok": false, "error": "vault not resolved"}')
        return 1
    cfg = _load_config(vault)
    provider = _select_provider(cfg, args.config)
    if provider is None:
        print(json.dumps({"ok": False, "error": "no active provider available"}))
        return 1

    key, src = _resolve_api_key(provider)
    if not key:
        print(json.dumps({"ok": False, "error": f"no api key for {provider.get('name')}"}))
        return 1

    body: dict[str, Any] = {
        "model": provider.get("model"),
        "prompt": args.prompt,
    }
    if args.size:
        body["size"] = args.size
    if args.style:
        body["style"] = args.style
    if isinstance(provider.get("extra_body"), dict):
        for k, v in provider["extra_body"].items():
            body.setdefault(k, v)
    body.setdefault("size", "1024x1024")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if isinstance(provider.get("extra_headers"), dict):
        for k, v in provider["extra_headers"].items():
            headers[str(k)] = str(v)

    timeout = int(provider.get("timeout_seconds") or 60)
    status, raw, err = _http_request(
        provider["endpoint"], method="POST", headers=headers,
        body=json.dumps(body).encode("utf-8"), timeout=timeout,
    )
    if err or not (200 <= status < 300):
        print(json.dumps({
            "ok": False,
            "provider": provider.get("name"),
            "status": status,
            "error": err or raw.decode("utf-8", errors="replace")[:400],
        }, ensure_ascii=False))
        return 1

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": f"bad json: {e}"}))
        return 1

    items = payload.get("data") or []
    if not items:
        print(json.dumps({"ok": False, "error": "empty data[]", "payload": payload}))
        return 1
    item = items[0]
    img_url = item.get("url")
    img_b64 = item.get("b64_json")

    output_dir = Path(args.output).parent if args.output else (
        vault / cfg.get("defaults", {}).get("output_dir", "_assets/images")
    )
    date_str = _dt.datetime.now().strftime("%Y-%m-%d")
    sha = _sha8(args.prompt + provider.get("name", "") + _now_iso())
    filename = Path(args.output).name if args.output else f"{date_str}-{sha}.png"
    out_path = output_dir / filename
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if img_url:
        ok, derr = _download(img_url, out_path, timeout=timeout)
        if not ok:
            print(json.dumps({"ok": False, "error": f"download: {derr}"}))
            return 1
    elif img_b64:
        import base64
        out_path.write_bytes(base64.b64decode(img_b64))
    else:
        print(json.dumps({"ok": False, "error": "no url nor b64 in response"}))
        return 1

    # Sidecar markdown with frontmatter
    md_path = out_path.with_suffix(".md")
    fm_lines = [
        "---",
        "type: image",
        f"title: {filename}",
        f"created: {_now_iso()}",
        f"provider: {provider.get('name')}",
        f"model: {provider.get('model')}",
        f"size: {body['size']}",
        f"prompt: |",
        *(f"  {ln}" for ln in args.prompt.splitlines()),
        "---",
        "",
        f"![[{filename}]]",
        "",
    ]
    md_path.write_text("\n".join(fm_lines), encoding="utf-8")

    print(json.dumps({
        "ok": True,
        "path": str(out_path),
        "sidecar": str(md_path),
        "provider": provider.get("name"),
        "model": provider.get("model"),
        "size": body["size"],
        "key_source": src,
    }, ensure_ascii=False))
    return 0


# ---------- list -------------------------------------------------------------

def cmd_list(args: argparse.Namespace) -> int:
    vault = _resolve_vault()
    if vault is None:
        print("vault not resolved", file=sys.stderr)
        return 1
    cfg = _load_config(vault)
    providers = _active_providers(cfg, include_disabled=bool(args.all))
    if not providers:
        print("(no providers configured)")
        return 0
    cols = ("name", "host", "model", "trusted", "disabled", "last_status", "last_check")
    rows = []
    for p in providers:
        host = urlparse(p.get("endpoint") or "").netloc or "-"
        rows.append((
            p.get("name", "-"),
            host,
            p.get("model", "-"),
            str(bool(p.get("trusted"))),
            str(bool(p.get("disabled"))),
            str(p.get("last_status") or "-"),
            str(p.get("last_check") or "-"),
        ))
    widths = [max(len(c), *(len(r[i]) for r in rows)) for i, c in enumerate(cols)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*cols))
    print(fmt.format(*("-" * w for w in widths)))
    for r in rows:
        print(fmt.format(*r))
    return 0


# ---------- main -------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="image_gen",
                                 description="cortex text-to-image CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_probe = sub.add_parser("probe", help="health check providers")
    p_probe.add_argument("--config", help="provider name (default: all active)")
    p_probe.add_argument("--all", action="store_true",
                        help="include disabled providers")
    p_probe.set_defaults(func=cmd_probe)

    p_gen = sub.add_parser("generate", help="generate image from prompt")
    p_gen.add_argument("prompt", help="text prompt")
    p_gen.add_argument("--config", help="provider name (default: random active)")
    p_gen.add_argument("--output", help="output file path (default: vault/<output_dir>/<date>-<sha>.png)")
    p_gen.add_argument("--size", help="image size, e.g. 1024x1024")
    p_gen.add_argument("--style", help="provider-specific style (e.g. vivid / natural)")
    p_gen.set_defaults(func=cmd_generate)

    p_list = sub.add_parser("list", help="list configured providers")
    p_list.add_argument("--all", action="store_true",
                       help="include disabled providers")
    p_list.set_defaults(func=cmd_list)

    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
