"""常量 + 预算 + 库根定位。

`always_budget()` 是 SessionStart 常驻注入的字符预算 —— 超了 `maintain --apply` 会把最大的
always 页降成 auto。这个数字直接换算成**每一轮对话**的 token 开销, 调大之前先想清楚。

`MAINTAIN_POLICY` 按 namespace 分表: 不同内容类型该用不同判据 (product 是需求真值, anchors
失效只报告禁自动归档; map 是现算的骨架, 失效即可归档)。新增 namespace 不改代码, 只加一行表项。
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional, cast


# 单一预算表: 各注入点的 token 预算 (单位: token)
# 新增注入点 → 在此表加一行，自动纳入预算管控
# 设计约束: 常驻类注入点 (session_index/session_core/subagent_core) 预算总和 ≤800 token (design.md)
# ponytail: 单一真值源，三处分散预算 → 收进一张表
INJECTION_BUDGETS: dict[str, int] = {
    "session_index": 200,   # SessionStart 极简索引 token 硬预算 (每条 1 行, 只 title+类目)
    "session_core": 300,     # 会话常驻注入 token 软预算 (原 1000 字符 ≈ 580 token, 降为 300)
    "subagent_core": 300,    # SubagentStart core 全文 token 硬预算 (原 2000 字符 ≈ 1160 token, 大幅降为 300)
    "filematch": 500,        # PreToolUse fileMatch 命中正文注入 token 硬预算 (多次命中累加, 超即截断)
}
NAMESPACES = ("rules", "product", "map", "external")  # namespace 默认清单 (仅 init 建目录用); 实际可用 namespace 由 Spec._scan_namespaces() 目录扫描得, 非白名单
INCLUSIONS = ("always", "auto", "fileMatch", "manual")  # inclusion 封闭四值 (加载策略, frontmatter 级); 对齐 Cursor .cursor/rules 与 Kiro .kiro/steering 收敛结论
STALE_DAYS = 180  # maintain stale 判据: created 年龄超此天数且无近期 updated → 候选
KEYWORDS_DUP_THRESHOLD = 3  # maintain keywords 高重复判据: 同 keywords 组 ≥ 此数 → 合并候选
# maintain 判据分表 (design.md §4) — namespace → 该 namespace 生效的判据集合。单一实现:
# 新增/调整 namespace 判据只改这张表 (或叫 _scan_findings 的通用引擎), 禁另起一套判定逻辑。
# 本表只填 rules(=DEFAULT, 未列名 namespace 兜底)/external/全局三类 (spec-model-core s6);
# product/map 两行的取值已按 design.md §4 定案填入骨架, 细节由 spec-product-wiki(p4)/spec-map-namespace(k3) 续填。
MAINTAIN_POLICY: dict[str, dict[str, Any]] = {
    "external": {"deprecated": True},           # 仅 deprecated/superseded → archive; 无 stale/dup/orphan
    "product": {"anchors": "report"},            # 仅 anchors 失效; 报告禁自动 archive (需求真值只有人知道)
    "map": {"anchors": "archive"},               # anchors 失效 → archive (骨架现算, 语义页失效无损)
}
DEFAULT_MAINTAIN_POLICY: dict[str, Any] = {      # rules 及未列名 namespace (含历史遗留 core/recall 目录) 兜底判据
    "stale": True, "keywords_dup": True, "deprecated": True, "orphan": True,
}
AUDIT_RETENTION_DAYS = 7  # .audit-log 保留窗口; 每次写前清掉 7 天前旧行 (按行首 ts 判)
# agent 名 → core 类目白名单 (命中类目注全文, 其余仅索引); 空列表/缺项 → fallback 纯索引。
# ponytail: 静态表足够, 无需 per-agent 配置文件; 新增 agent 就地加一行。
AGENT_CATEGORIES: dict[str, list[str]] = {
    "skein-executor": ["script", "git"],
    "skein-checker": ["script"],
    "skein-researcher": ["script"],
    "skein-finisher": ["script", "git"],
    # setup/dedup/specer 未列 → 默认 fallback 纯索引
}
def now() -> int:
    return int(time.time())  # Unix epoch 秒 — 与 skein.py 一致, 所有落盘时间字段统一时间戳
def _read_hook_stdin() -> Optional[str]:
    """读 hook stdin JSON 取 agent_type; stdin 空/非 JSON/缺字段 → None (容错 fallback)。"""
    raw = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    if not raw:
        return None
    try:
        return cast(Optional[str], json.loads(raw).get("agent_type"))
    except (json.JSONDecodeError, AttributeError):
        return None
def spec_root() -> Path:
    try:
        # 使用进程当前工作目录而非默认工作目录，确保在 worktree 中正确解析
        cwd = Path.cwd()
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, cwd=cwd)
        base = Path(r.stdout.strip()) if r.returncode == 0 else cwd
    except FileNotFoundError:  # 无 git 二进制 → fallback cwd (设计意图: 非 git 也可用)
        base = Path.cwd()
    return base / ".skein" / "spec"
def _validate_budget(budget: int) -> None:
    """预算守卫: 非正数预算抛 ValueError

    Args:
        budget: 预算值 (token 数)

    Raises:
        ValueError: 预算非正数
    """
    if budget <= 0:
        raise ValueError(f"预算必须为正数: {budget}")

def always_budget_tokens() -> int:
    """会话常驻注入 token 软预算: 读 .skein/config.yaml spec.always_budget (字符),
    用换算系数转为 token。
    always_budget 缺失/非正整数 → fallback 到 spec.core_budget (字符) → 默认 517 字符 ≈ 300 token。

    读原始 YAML (非 pydantic Config) 以区分「用户显式设了」和「pydantic 补了默认值」。"""
    from skeinlib.utils.token_conversion import estimate_tokens_from_chars
    import yaml as _yaml

    cfg_path = spec_root().parent / "config.yaml"
    raw_spec: dict[str, Any] = {}
    if cfg_path.exists():
        try:
            raw = _yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            raw_spec = (raw.get("spec") or {}) if isinstance(raw, dict) else {}
        except Exception:
            pass

    # 优先 always_budget (原始 YAML 值, 非 pydantic 补的默认)
    ab = raw_spec.get("always_budget")
    if isinstance(ab, (int, float)) and ab > 0:
        tokens = estimate_tokens_from_chars(int(ab))
        try:
            _validate_budget(tokens)
            return tokens
        except Exception:
            pass

    # fallback: core_budget
    cb = raw_spec.get("core_budget")
    if isinstance(cb, (int, float)) and cb > 0:
        tokens = estimate_tokens_from_chars(int(cb))
        try:
            _validate_budget(tokens)
            return tokens
        except Exception:
            pass

    # 默认 517 字符 ≈ 300 token
    default_tokens = estimate_tokens_from_chars(517)
    _validate_budget(default_tokens)
    return default_tokens
