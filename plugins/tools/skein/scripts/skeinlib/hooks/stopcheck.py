"""Stop hook: 扫 spec 问题写 `.pending-fix` 标记, 供 main 下回合派 specer bg 修复。

只读不修, 永远返回 0 —— 修复是 specer agent 的异步职责, 回合结束这一刻不该被体检卡住。

它是唯一会加载整个 `skeinlib.spec` 门面的 hook 子命令 (几十毫秒)。与别的 hook 合模块的话,
每次跑 fmt / spec-meta 都得先付这份钱 —— 一 hook 一文件 + cli 懒 dispatch, 只有真跑
stop-check 时才加载。
"""
from __future__ import annotations

import json
from typing import Any

# ponytail: _scan_findings 是 Spec 私有方法但同包内可直调, 免为 stop-check 单开 maintain --check-only 公开口


def cmd_stop_check(_: dict[str, Any]) -> int:
    """Stop hook: 扫 spec → 有问题写 .pending-fix JSON (供 main 下回合检测派 specer bg 修复); 只读不修。

    返回 0 永不阻塞 (问题归 specer agent 异步修)。无 .skein/spec → 静默; 无问题 → 删旧标记防已修复后误触发。

    判据按 namespace 分表 (与 maintain 共用同一套 MAINTAIN_POLICY 逻辑):
    - product namespace: 失效项不写 .pending-fix (需求真值不自动修复)
    - rules/map/external: 失效项写 .pending-fix (可自动修复或需人工判断)
    """
    from datetime import datetime  # 局部: 仅落盘 ts 用

    from skeinlib.spec.facade import Spec
    from skeinlib.spec.model import always_budget_tokens, MAINTAIN_POLICY
    from skeinlib.token_conversion import estimate_tokens_from_chars

    spec = Spec()
    if not spec.root.exists():
        return 0  # 非 skein 项目 → 静默

    # 扫描全部 namespace，但不写 product namespace 的失效标记 (需求真值不自动修复)
    all_ns = spec._scan_namespaces()
    findings = spec._scan_findings(all_ns)

    # 过滤掉 product namespace 的失效项 (不自动修复需求真值)
    # rel 格式为 "namespace/category/stem"，通过 rel 判断 namespace
    filtered_findings = [fd for fd in findings if not fd.get("rel", "").startswith("product/")]

    marker = spec.root / ".pending-fix"
    if not filtered_findings:
        try:
            marker.unlink()  # 已修复 → 清旧标记免误触发
        except FileNotFoundError:
            pass
        return 0
    root = spec.root
    problems: list[dict[str, Any]] = []
    for fd in filtered_findings:
        kind = fd["kind"]
        text = fd.get("text", "")
        if kind == "overbudget":
            problems.append({"type": "over-budget", "detail": text, "size": fd.get("size")})
        elif kind == "keywords_dup":
            files = [f.relative_to(root).as_posix() for f in fd.get("files", [])]
            problems.append({"type": "keywords-dup", "files": files, "detail": text})
        else:  # stale / deprecated / broken_link 均带 rel
            tmap = {"stale": "stale", "deprecated": "deprecated", "broken_link": "broken-link"}
            rel = fd.get("rel", "")
            problems.append({"type": tmap.get(kind, kind),
                             "files": [rel] if rel else [], "detail": text})
    payload = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "core_chars": len(spec._core_text_raw()),
        "core_tokens": estimate_tokens_from_chars(len(spec._core_text_raw())),
        "budget_tokens": always_budget_tokens(),
        "problems": problems,
    }
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0
