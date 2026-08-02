"""bin wrapper stdout JSON-only enforcement."""
from __future__ import annotations

import contextlib
import io
import json
import os
import runpy
import sys
import tempfile
from typing import Any


def _payload(ok: bool, code: int, stdout: str = "", error: str | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {"ok": ok, "code": code}
    if stdout:
        try:
            data["data"] = json.loads(stdout)
        except json.JSONDecodeError:
            data["stdout"] = stdout
    if error:
        data["error"] = error
    return data


@contextlib.contextmanager
def _capture_stdout() -> Any:
    """Capture sys.stdout and fd 1; Rich/Console may keep its own stdout handle."""
    old_stdout = sys.stdout
    saved_fd = os.dup(1)
    with tempfile.TemporaryFile(mode="w+b") as tmp:
        text = io.TextIOWrapper(tmp, encoding=getattr(old_stdout, "encoding", None) or "utf-8")
        sys.stdout = text
        os.dup2(tmp.fileno(), 1)
        try:
            yield tmp, text
        finally:
            text.flush()
            os.dup2(saved_fd, 1)
            os.close(saved_fd)
            sys.stdout = old_stdout


def _captured_text(tmp: Any, text: io.TextIOWrapper) -> str:
    text.flush()
    tmp.flush()
    tmp.seek(0)
    return tmp.read().decode("utf-8", errors="replace").strip()


def run_json(target: str) -> None:
    """Run script, emit one JSON object on stdout, preserve exit code."""
    code = 0
    error = None
    with _capture_stdout() as (tmp, _text):
        try:
            runpy.run_path(target, run_name="__main__")
        except SystemExit as exc:
            if isinstance(exc.code, int):
                code = exc.code
            elif exc.code:
                code = 1
                error = str(exc.code)
        except Exception as exc:  # pragma: no cover - crash path still must keep stdout JSON-only
            code = 1
            error = f"{type(exc).__name__}: {exc}"
        stdout = _captured_text(tmp, _text)
    print(json.dumps(_payload(code == 0, code, stdout, error), ensure_ascii=False))
    raise SystemExit(code)
