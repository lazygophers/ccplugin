"""`skein-spec analyze <tid>` — 只读一致性核查 (对齐 spec-kit `/speckit.analyze`)。

五类检查, 全部只读 task.json (TaskSpec 字段) / design.md + 已有 spec 规则库, 不写任何盘:
  验收覆盖率  task 验收项 (acceptance) ↔ subtask 验收项, 报关键词无命中的验收条 (候选未覆盖)
  硬规冲突    design.md ↔ inclusion=always 规则的否定式表述, 报候选 (不断言违规)
  范围蔓延    subtask 名/desc ↔ task spec 关键词 (desc/边界), 报无命中的 subtask (候选蔓延)
  置信度      design.md 提及的规则标题 ↔ 该规则 status=proposed, 报未验证引用
  接缝存在性  design.md「测试接缝」段声明的路径/符号 ↔ codebase, 报未找到

每类判据全是启发式关键词/子串匹配 —— 语义判断本就只能给候选交人判 (design.md §3), 报告
措辞统一带「候选」字样, 禁断言。零命中就如实报零冲突, 不硬凑。
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from typing import Any, cast

from pydantic import BaseModel, Field

from skeinlib.utils.errors import SkeinError
from skeinlib.spec.text import _frontmatter

# 硬规否定式关键词 + 其后紧跟的短语 (最多 20 字, 到常见分隔符为止) — 用于硬规冲突候选提取
_NEG_RE = re.compile(r"(禁止?|不可|不得|严禁|禁用|MUST NOT)\s*([^\n,，。;；:：]{2,20})")
_BACKTICK_RE = re.compile(r"`([^`\n]+)`")
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}")


def _keywords(text: str) -> set[str]:
    """粗粒度关键词集: 英文/数字连续片段 (≥2 字符) ∪ 中文相邻二字 bigram。
    纯启发式子串重合判据, 非分词 — 够用来判「有没有沾边」, 不追求精确分词。"""
    toks = set(_TOKEN_RE.findall(text))
    han = re.sub(r"[^一-鿿]", "", text)
    toks |= {han[i:i + 2] for i in range(len(han) - 1)}
    return {t for t in toks if len(t) >= 2}


def _spec_text(t: dict[str, Any]) -> str:
    """task.json 的 TaskSpec 字段 (desc/边界/验收) 拼接文本 — analyze 的需求侧输入。"""
    b = t.get("boundary") or {}
    return " ".join([t.get("desc") or "", *(b.get("should") or []), *(b.get("should_not") or []),
                     *(t.get("acceptance") or [])])


def _design_section(text: str, name: str) -> str:
    m = re.search(rf"^##\s+{re.escape(name)}\b.*$", text, re.MULTILINE)
    if not m:
        return ""
    nxt = re.search(r"^##\s+", text[m.end():], re.MULTILINE)
    return text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]


class SpecFinding(BaseModel):
    """spec analyze 候选问题。"""
    kind: str = Field(description="问题类型")
    text: str = Field(description="展示文本")


class AnalyzeMixin:
    # ---- analyze 子命令 (只读, 见 SpecBase 提供的 root/_scan_namespaces/_rules/_inclusion) ----
    def analyze(self, a: argparse.Namespace) -> None:
        tid = cast(str, a.tid)
        as_json = bool(getattr(a, "json", False))
        tasks_dir = self.root.parent / "task"  # type: ignore[attr-defined]  # SpecBase.root = .skein/spec
        tdir = tasks_dir / tid
        if not tdir.exists():
            raise SkeinError(f"task 不存在: {tid} (查 {tdir})")

        t: dict[str, Any] = {}
        task_json = tdir / "task.json"
        if task_json.exists():
            t = json.loads(task_json.read_text())
        design_text = (tdir / "design.md").read_text() if (tdir / "design.md").exists() else ""

        findings: list[SpecFinding] = []
        findings += self._analyze_coverage(t)
        findings += self._analyze_hardrule(design_text)
        findings += self._analyze_scope(t)
        findings += self._analyze_confidence(design_text)
        findings += self._analyze_seam(design_text)

        if as_json:
            print(json.dumps({"tid": tid, "count": len(findings), "findings": [f.model_dump() for f in findings]},
                              ensure_ascii=False))
            return
        if not findings:
            print(f"analyze {tid}: 零冲突 (验收覆盖/硬规冲突/范围蔓延/置信度/接缝 五类检查均无问题)")
            return
        print(f"analyze {tid}: {len(findings)} 条候选 (启发式, 需人判):")
        for fd in findings:
            print(f"  [{fd.kind}] {fd.text}")

    # ---- 1. 验收覆盖率: task 验收项 (acceptance) ↔ subtask 验收项 ----
    def _analyze_coverage(self, t: dict[str, Any]) -> list[SpecFinding]:
        items = [i.strip() for i in (t.get("acceptance") or []) if i.strip()]
        if not items:
            return []
        sub_kw: set[str] = set()
        for s in t.get("subtasks") or []:
            sub_kw |= _keywords(f"{s.get('name', '')} {s.get('desc', '')} "
                                 f"{' '.join(s.get('acceptance') or [])}")
        out = []
        for item in items:
            if not (_keywords(item) & sub_kw):
                out.append(SpecFinding(kind="coverage",
                                       text=f"[候选未覆盖] task 验收条「{item}」未在任何 subtask 找到关键词对应"))
        return out

    # ---- 2. 硬规冲突: design.md ↔ inclusion=always 规则的否定式表述 (报候选交人判, 不断言) ----
    def _analyze_hardrule(self, design_text: str) -> list[SpecFinding]:
        if not design_text:
            return []
        out: list[SpecFinding] = []
        for ns in self._scan_namespaces():  # type: ignore[attr-defined]
            for f, title, body in self._rules(ns):  # type: ignore[attr-defined]
                if self._inclusion(f) != "always":  # type: ignore[attr-defined]
                    continue
                for m in _NEG_RE.finditer(body):
                    phrase = m.group(2).strip()
                    if len(phrase) < 2:
                        continue
                    for dm in re.finditer(re.escape(phrase), design_text):
                        ctx_before = design_text[max(0, dm.start() - 6):dm.start()]
                        if _NEG_RE.search(ctx_before + phrase):
                            continue  # design 本身也是否定表述, 与硬规同向, 非冲突
                        line_start = design_text.rfind("\n", 0, dm.start()) + 1
                        line_end = design_text.find("\n", dm.start())
                        line = design_text[line_start:line_end if line_end != -1 else len(design_text)].strip()
                        out.append(SpecFinding(kind="hardrule",
                                               text=f"[候选,需人判] design.md 疑似违反硬规「{title}」"
                                                    f"({f.parent.parent.name}/{f.parent.name}/{f.stem}): "
                                                    f"规则要求「{m.group(0).strip()}」, design 上下文: {line}"))
        return out

    # ---- 3. 范围蔓延: subtask 名/desc ↔ task spec 关键词 (desc/边界) ----
    def _analyze_scope(self, t: dict[str, Any]) -> list[SpecFinding]:
        spec_kw = _keywords(_spec_text(t))
        if not spec_kw:
            return []
        out = []
        for s in t.get("subtasks") or []:
            sub_kw = _keywords(f"{s.get('name', '')} {s.get('desc', '')}")
            if sub_kw and not (sub_kw & spec_kw):
                out.append(SpecFinding(kind="scope",
                                       text=f"[候选] subtask {s.get('sid')} 「{s.get('name', '')}」"
                                            f"在 task spec (desc/边界) 无关键词对应, 疑似范围蔓延"))
        return out

    # ---- 4. 置信度: design 引用的规则 status=proposed ----
    def _analyze_confidence(self, design_text: str) -> list[SpecFinding]:
        if not design_text:
            return []
        out = []
        for ns in self._scan_namespaces():  # type: ignore[attr-defined]
            for f, title, _body in self._rules(ns):  # type: ignore[attr-defined]
                if not title or title not in design_text:
                    continue
                meta = _frontmatter(f.read_text())
                if meta.get("status") == "proposed":
                    out.append(SpecFinding(kind="confidence",
                                       text=f"[未验证] design.md 引用规则「{title}」"
                                            f"({f.parent.parent.name}/{f.parent.name}/{f.stem}) "
                                            f"status=proposed, 尚未验证"))
        return out

    # ---- 5. 接缝存在性: design.md「测试接缝」段声明的路径/符号 ↔ codebase ----
    def _analyze_seam(self, design_text: str) -> list[SpecFinding]:
        body = _design_section(design_text, "测试接缝")
        if not body:
            return []
        repo_root = self.root.parent.parent  # type: ignore[attr-defined]  # .skein/spec → 仓库根
        out: list[SpecFinding] = []
        seen: set[str] = set()
        for tok in _BACKTICK_RE.findall(body):
            cand = tok.strip().split()[0].strip() if tok.strip() else ""
            if not cand or cand in seen:
                continue
            seen.add(cand)
            if "/" in cand or re.search(r"\.\w{1,4}$", cand):  # 路径型
                if not (repo_root / cand.lstrip("./")).exists():
                    out.append(SpecFinding(kind="seam",
                                               text=f"[缺失] design.md 声明接缝「{cand}」在 codebase 未找到该路径"))
                continue
            try:  # 命令/符号型 → git grep 全库找引用
                r = subprocess.run(["git", "grep", "-q", "-F", cand], cwd=repo_root,
                                   capture_output=True, timeout=10)
                if r.returncode != 0:
                    out.append(SpecFinding(kind="seam",
                                               text=f"[缺失] design.md 声明接缝「{cand}」在 codebase 未找到引用 (git grep 无命中)"))
            except (OSError, subprocess.TimeoutExpired):
                pass  # 无 git 二进制/超时 — 跳过该候选, 不因环境问题误报
        return out
