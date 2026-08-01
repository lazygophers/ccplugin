"""core 正文组装 + SessionStart / SubagentStart 两个 hook 的注入产出。

**这是每次会话/每次派 agent 都要付的 token**, 所以两处都过 `budget_guard` 硬预算:
SessionStart 只注索引 (400 token), SubagentStart 按 agent 类目注全文 (2000 token)。
超预算不是软警告 —— 直接截断, 免 model 忽视警告后上下文无限膨胀。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from skeinlib.hooks.runner import budget_guard
from skeinlib.spec.model import (AGENT_CATEGORIES, INDEX_BUDGET_TOKENS, STALE_DAYS,
                                 SUBAGENT_BUDGET_TOKENS, _read_hook_stdin, always_budget, now)
from skeinlib.spec.text import _sections, _strip_frontmatter


class InjectMixin:
    # 仅供 mypy 用的属性声明: root/_always_files/_mtimes/_age_days 由兄弟类 SpecBase
    # 提供 (组装成 Spec 时混入)。TYPE_CHECKING 块运行时永不执行, 零行为改动, 只消除单看
    # 本 mixin 时的 attr-defined 噪声。
    if TYPE_CHECKING:
        root: Path
        def _always_files(self) -> list[Path]: ...
        def _mtimes(self, use_git: bool = True) -> dict[Path, int]: ...
        def _age_days(self, f: Path, mtimes: dict[Path, int], now_ts: int) -> int: ...

    # ---- core 正文 (供 inject-core / session-start 复用) ----
    def _core_text_raw(self) -> str:
        parts = [_strip_frontmatter(f.read_text()).strip() for f in self._always_files()]
        return "\n\n".join(p for p in parts if p)
    def _core_text(self) -> str:
        text = self._core_text_raw()
        budget = always_budget()
        if len(text) > budget:
            sys.stderr.write(
                f"core 规则 {len(text)} 字符 > 预算 {budget} — "
                "常驻注入过重, 考虑降级部分到 recall\n")
        return text
    # ---- inject-core (按需拉全文正文) ----
    def inject_core(self, _: argparse.Namespace) -> None:
        sys.stdout.write(self._core_text())
    # ---- core 极简索引 (章节粒度, 每条规则 1 行: [类目] 主题 · title) ----
    def _core_index(self) -> str:
        rules = [(f, t, b) for f in self._always_files() for t, b in _sections(f.read_text())]
        return "\n".join(f"- [{f.parent.name}/{f.stem}] {title}"
                         for f, title, _ in rules if title)
    # ---- session-start (SessionStart hook: 只注入极简索引, 全文按需 inject-core) ----
    def session_start(self, _: argparse.Namespace) -> None:
        idx = self._core_index().strip()
        if not idx:
            return
        ctx = budget_guard(
            "# SKEIN core 规则索引 (仅标题; 需全文跑 `spec.py inject-core`)\n\n" + idx,
            INDEX_BUDGET_TOKENS, "spec:session-start")
        # maintain 提示: core 超预算 或 最老规则 > 180 天 → 1 行提醒 (不挤 INDEX 预算)
        core_text = self._core_text_raw()
        now_ts = now()
        # hook 热路径: 不跑 git log (use_git=False), 文件系统 mtime 够判"该体检了"
        mt = self._mtimes(use_git=False)
        oldest = max((self._age_days(f, mt, now_ts) for f in self._always_files()), default=0)
        if len(core_text) > always_budget() or oldest > STALE_DAYS:
            ctx += f"\n⚠️ core 超 budget / 有 > {STALE_DAYS}天老规则, 跑 `spec.py maintain` 体检"
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": ctx}}))
    # ---- core 按类目过滤全文 (命中类目注全文, 其余仅进索引) ----
    def _core_text_by_cat(self, cats: list[str]) -> str:
        parts = [_strip_frontmatter(f.read_text()).strip()
                 for f in self._always_files() if f.parent.name in cats]
        return "\n\n".join(p for p in parts if p)
    # ---- subagent-start (SubagentStart hook: 读 stdin.agent_type 决定注入范围) ----
    def subagent_start(self, _: argparse.Namespace) -> None:
        # matcher 已放开到全 subagent — 非 SKEIN 项目 (无 .skein/spec) 静默不注入, 免污染其他插件的 agent
        if not self.root.exists():
            return
        idx = self._core_index().strip()
        if not idx:
            return
        head = ("# SKEIN spec 纪律 (执行期强制)\n"
                "- 动手前: 相关约定先跑 `spec.py recall <关键词>` 拉 recall 层, 别凭记忆重推。\n"
                "- 命中 core 规则 (下列) 即硬约束, 违反视为未完成。\n"
                "- 踩到「后续同类任务会再犯」的坑 / 定下可复用约定: 在回传给 main 的摘要里标一行 `SPEC:` 供 finish sediment 落盘, 别让它随 worktree 销毁蒸发。\n")
        recall_tail = "\n## 需要其他类目全文? 跑 `spec.py recall <关键词>` 或 inject-core\n"
        cats = AGENT_CATEGORIES.get(_read_hook_stdin() or "", [])
        if cats:
            body = self._core_text_by_cat(cats).strip()
            ctx = head + f"\n## core 规则 (命中类目 {cats})\n\n{body}\n\n## 全量 core 索引\n\n{idx}{recall_tail}"
        else:  # 空映射/非 skein agent/stdin 失败 → 全 core 正文 + 索引 (对齐 help: 每 subagent 注 core 全文)
            body = self._core_text().strip()
            ctx = head + f"\n## core 规则 (全量)\n\n{body}\n\n## core 索引\n\n{idx}{recall_tail}"
        ctx = budget_guard(ctx, SUBAGENT_BUDGET_TOKENS, "spec:subagent-start")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SubagentStart", "additionalContext": ctx}}))
