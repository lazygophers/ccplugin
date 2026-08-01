"""PostToolUse 写后处理 —— 三个子命令都在「文件已经落盘了, 现在补一下」这个位置。

fmt        prd.md 写后规范化 (幂等)
spec-meta  spec 页写后校 frontmatter (只 warning)
flow-gate  源码写后若无 active task 且已跨 ≥2 文件 → 提示补 create (一次)

共同纪律: **永不返回非零**。写已经发生了, 这层再阻断也收不回来, 只会打断用户的 Edit/Write。
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

from skeinlib.hooks.util import git_root

# ── fmt (PostToolUse: prd.md 写后规范化) ────────────────────────────────────
PRD_RE = re.compile(r"(?:^|/)\.skein/task/([^/]+)/prd\.md$")


def cmd_fmt(d: dict[str, Any]) -> int:
    """写 .skein/task/<id>/prd.md 后自动跑一次 skein fmt <id> (幂等; python 写回不经工具层 → 不递归)。"""
    fp = d.get("tool_input", {}).get("file_path", "")
    if not fp:
        return 0
    norm = fp.replace("\\", "/")
    m = PRD_RE.search(norm)
    if not m:
        return 0  # 非 prd.md 放行
    tid = m.group(1)
    root = norm[:m.start()] or (d.get("cwd") or os.getcwd())  # .skein 所在仓库根作 cwd
    # 局部 import: 仅本子命令用。paths 拉 pathlib、subprocess 也不轻, 而 dispatch 是懒加载的
    # (cli.py), 所以 permission/user-prompt 那些热子命令根本不会付这份钱。
    import subprocess

    from skeinlib.paths import SKEIN_ENTRY
    try:
        subprocess.run([sys.executable, str(SKEIN_ENTRY), "fmt", tid], cwd=root,
                       capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass  # 非阻塞 hook: fmt 失败不影响写入
    return 0


# ── spec-meta (PostToolUse: spec 文件 metadata 合法性检查) ──────────────────
SPEC_RE = re.compile(r"(?:^|/)\.skein/spec/[^/]+/[^/]+/.+\.md$")
SPEC_REQUIRED = ("title", "namespace", "inclusion", "keywords")
SPEC_INCLUSIONS = ("always", "auto", "fileMatch", "manual")


def _parse_fm(text: str) -> dict[str, str]:
    """简单 YAML frontmatter 解析 (只取顶层 key: value, 无嵌套)。返回 dict 或 {}。"""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[4:end] if text[3] == "\n" else text[3:end]
    fm: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line or line.startswith((" ", "\t", "-")):
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm


def cmd_spec_meta(d: dict[str, Any]) -> int:
    """写 .skein/spec/**/*.md 后检查 frontmatter: 必填缺失 + layer 合法。非阻塞 warning。"""
    fp = d.get("tool_input", {}).get("file_path", "")
    if not fp:
        return 0
    norm = fp.replace("\\", "/")
    if not SPEC_RE.search(norm):
        return 0
    try:
        with open(fp, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return 0
    fm = _parse_fm(text)
    short = norm.split(".skein/spec/")[-1] if ".skein/spec/" in norm else norm
    warns: list[str] = []
    for k in SPEC_REQUIRED:
        v = fm.get(k, "")
        if k == "keywords":
            inner = v.strip("[] ").strip()
            if not inner:
                warns.append("缺失: keywords")
            continue
        if not v:
            warns.append(f"缺失: {k}")
            continue

    # 提取 frontmatter 部分（用于更精确的字段检查）
    fm_text = ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            fm_text = text[4:end] if text[3] == "\n" else text[3:end]

    # inclusion:fileMatch 缺 globs 告警
    inclusion = fm.get("inclusion", "")
    if inclusion == "fileMatch":
        # 检查 frontmatter 中是否有 globs 字段（更精确的检查）
        if "globs:" not in fm_text.lower() and "globs =" not in fm_text.lower():
            warns.append("缺失: inclusion=fileMatch 时需配置 globs")

    # namespace:product|map 缺 anchors 告警
    namespace = fm.get("namespace", "")
    if namespace in ("product", "map"):
        # 检查 frontmatter 中是否有 anchors 字段（更精确的检查）
        if "anchors:" not in fm_text.lower() and "anchors =" not in fm_text.lower():
            warns.append(f"缺失: namespace={namespace} 时需配置 anchors")
    if warns:
        ctx = f"⚠️ spec metadata 检查 ({short}):\n  - " + "\n  - ".join(warns)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": ctx}}))
    return 0


# ── flow-gate (PostToolUse: 无 active task 却在跨文件改源码 → 软提示补 create) ──────
# 背景: 旧「落码门」(改源码前强制 active task) 被移除过 (见 judge._CTX 上方注释), 之后
# 「判了 flow 却不建 task 直接开干」就只剩提示词自觉约束, 长会话必漂移。
# 本门是它的软替代, 刻意避开当初被移除的原因:
#   ① PostToolUse 不 PreToolUse — 只提示不阻断, 不打断工作流, 不误伤诊断只读
#   ② 累计 ≥2 个源码文件才提 — 单文件小改是 inline 的合法豁免, 不该被 nag
#   ③ 提示一次即落 flag — 不刷屏
_SRC_EXT = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb", ".php",
            ".c", ".cc", ".cpp", ".h", ".hpp", ".swift", ".kt", ".sh")
_TALLY_MAX_AGE = 4 * 3600  # tally 超此秒数视为上个会话残留, 重新计数


def cmd_flow_gate(d: dict[str, Any]) -> int:
    """写源码后: 无 active task 且本轮已跨 ≥2 源码文件 → 注入补 create 提示 (非阻塞, 一次)。"""
    fp = (d.get("tool_input", {}) or {}).get("file_path", "")
    if not fp or not fp.endswith(_SRC_EXT):
        return 0
    norm = fp.replace("\\", "/")
    if ".skein/" in norm or "/tests/" in norm or "/test_" in norm:
        return 0  # spec 库与测试文件不计入 (测试常跟着单文件改动走)
    root = git_root(d.get("cwd") or os.getcwd())
    dir_ = os.path.join(root, ".skein")
    if not os.path.exists(os.path.join(dir_, "config.yaml")):
        return 0  # 未初始化归 user-prompt 的 _UNINIT_* 提示, 本门不重复 nag
    # 有 active task → 已在 flow 内, 清 tally 直接放行
    try:
        with open(os.path.join(dir_, "task.json"), encoding="utf-8") as f:
            rows = json.loads(f.read()).get("tasks", [])
        if any(r.get("status") in ("进行中", "检查中") for r in rows):
            for p in (os.path.join(dir_, ".edit-tally"), os.path.join(dir_, ".edit-tally.warned")):
                if os.path.exists(p):
                    os.remove(p)
            return 0
    except (OSError, ValueError):
        return 0
    tally, warned = os.path.join(dir_, ".edit-tally"), os.path.join(dir_, ".edit-tally.warned")
    if os.path.exists(warned):
        return 0  # 已提过, 不刷屏
    import time  # 局部: 仅本门用, 不拖其他子命令启动
    try:
        seen: set[str] = set()
        if os.path.exists(tally) and time.time() - os.path.getmtime(tally) < _TALLY_MAX_AGE:
            with open(tally, encoding="utf-8") as f:
                seen = {ln.strip() for ln in f if ln.strip()}
        seen.add(norm)
        with open(tally, "w", encoding="utf-8") as f:
            f.write("\n".join(sorted(seen)))
        if len(seen) < 2:
            return 0
        open(warned, "w").close()
    except (OSError, ValueError):
        # ValueError 覆盖 UnicodeDecodeError (tally 被写坏成二进制) — PostToolUse 永不该失败,
        # 一个坏掉的计数文件不值得打断用户的 Edit/Write。
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": (
        f"⚠️ 已改动 {len(seen)} 个源码文件但**无 active task** — 跨 ≥2 文件正是 flow 的判据线。\n"
        "若这本该走 flow: 立刻 `skein.py create` 建 task, 把已改的纳入首个 subtask, 后续改动在 flow 内做。\n"
        "若确属 inline 豁免 (如同一处改动波及两文件): 忽略本提示, 继续。\n"
        f"已改: {', '.join(sorted(seen)[:5])}")}}))
    return 0
