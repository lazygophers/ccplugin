from __future__ import annotations

import json
from datetime import datetime
from typing import Any


def cmd_stop_check(_: dict[str, Any]) -> int:
    from skeinlib.spec.facade import Spec
    from skeinlib.spec.model import always_budget_tokens
    from skeinlib.utils.token_conversion import estimate_tokens_from_chars
    spec = Spec()
    if not spec.root.exists():
        return 0
    root = spec.root
    findings = [finding for finding in spec._scan_findings(spec._scan_namespaces())
                if not finding.get("rel", "").startswith("product/")]
    marker = root / ".pending-fix"
    if not findings:
        try:
            marker.unlink()
        except FileNotFoundError:
            pass
        return 0
    problems: list[dict[str, Any]] = []
    for finding in findings:
        kind = finding["kind"]
        detail = finding.get("text", "")
        if kind == "overbudget":
            problems.append({"type": "over-budget", "detail": detail, "size": finding.get("size")})
        elif kind == "keywords_dup":
            problems.append({"type": "keywords-dup", "files": [path.relative_to(root).as_posix() for path in finding.get("files", [])], "detail": detail})
        else:
            rel = finding.get("rel", "")
            problems.append({"type": {"stale": "stale", "deprecated": "deprecated", "broken_link": "broken-link"}.get(kind, kind),
                             "files": [rel] if rel else [], "detail": detail})
    marker.write_text(json.dumps({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "core_chars": len(spec._core_text_raw()),
        "core_tokens": estimate_tokens_from_chars(len(spec._core_text_raw())),
        "budget_tokens": always_budget_tokens(),
        "problems": problems,
    }, ensure_ascii=False, indent=2))
    return 0


__all__ = ["cmd_stop_check"]
