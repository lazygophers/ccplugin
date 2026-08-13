#!/usr/bin/env python3
"""novelist 插件目录结构 lint.

校验插件目录结构/文件名/文件夹组织是否符合 plugin-development.md 规范。
独立工具, 不依赖 scripts/check.py (后者有 skills.bak bug)。

7 规则:
  R1 plugin.json 存在 + 合法 + name 合规
  R2 commands/agents/skills 在插件根 (不在 .claude-plugin/ 内)
  R3 skill 子目录 kebab-case + 含大写 SKILL.md
  R4 agents/*.md 文件名 kebab-case
  R5 产物/临时文件不泄漏
  R6 plugin.json 中 agents/skills/commands 路径真实存在
  R7 skill SKILL.md frontmatter name == 目录名

Usage:
  python3 lint.py [--plugin-dir <path>] [--fix-hints]
  # 默认 --plugin-dir = 上溯找 .claude-plugin/ 的目录
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

KEBAB_RE = re.compile(r"^[a-z0-9-]+$")
NAME_RE = re.compile(r"^[a-z0-9-]+$")

# 产物 pattern (R5)
ARTIFACT_FILES = {".DS_Store", ".darwin-results.tsv"}
ARTIFACT_SUFFIXES = {".pyc", ".pyo"}
ARTIFACT_DIRS = {"__pycache__"}
ARTIFACT_DIR_SUFFIXES = {".bak"}


@dataclass
class Violation:
    rule: str
    severity: str  # "error" | "warning"
    path: str
    message: str

    @property
    def fix_hint(self) -> str:
        hints = {
            "R1": "补 .claude-plugin/plugin.json, name 字段匹配 ^[a-z0-9-]+$",
            "R2": "把目录移到插件根 (不在 .claude-plugin/ 内)",
            "R3": "目录名改 kebab-case + 确保含大写 SKILL.md (非 skill.md)",
            "R4": "agent 文件名改 kebab-case (如 chapter-writer.md)",
            "R5": "删除产物文件 (rm <path>) 或加 .gitignore",
            "R6": "修正 plugin.json 中路径指向真实存在的文件/目录",
            "R7": "SKILL.md frontmatter name 改为与目录名一致",
        }
        return hints.get(self.rule, "")


@dataclass
class LintReport:
    plugin_dir: Path
    violations: list[Violation] = field(default_factory=list)

    def add(self, rule: str, severity: str, path: str, message: str) -> None:
        self.violations.append(Violation(rule, severity, path, message))

    @property
    def errors(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[Violation]:
        return [v for v in self.violations if v.severity == "warning"]


def _rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


def _parse_frontmatter(text: str) -> dict | None:
    """简易 YAML frontmatter 解析 (只取顶层 key: value)."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm: dict = {}
    for line in text[3:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip().strip("'\"")
    return fm


# ---- 规则实现 ----

def check_r1(report: LintReport) -> None:
    """R1: plugin.json 存在 + 合法 JSON + name 匹配 NAME_RE."""
    root = report.plugin_dir
    pj = root / ".claude-plugin" / "plugin.json"
    if not pj.exists():
        report.add("R1", "error", ".claude-plugin/plugin.json", "plugin.json 不存在")
        return
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        report.add("R1", "error", _rel(pj, root), f"plugin.json 解析失败: {e}")
        return
    name = data.get("name")
    if not name:
        report.add("R1", "error", _rel(pj, root), "缺 name 字段")
        return
    if not NAME_RE.match(str(name)):
        report.add("R1", "error", _rel(pj, root),
                   f"name={name!r} 不匹配 ^[a-z0-9-]+$")


def check_r2(report: LintReport) -> None:
    """R2: commands/agents/skills 不在 .claude-plugin/ 内."""
    root = report.plugin_dir
    cp = root / ".claude-plugin"
    if not cp.is_dir():
        return
    for sub in ("commands", "agents", "skills"):
        bad = cp / sub
        if bad.exists():
            report.add("R2", "error", _rel(bad, root),
                       f"{sub}/ 误入 .claude-plugin/ 内, 须在插件根")


def check_r3(report: LintReport) -> None:
    """R3: skill 子目录 kebab-case + 含大写 SKILL.md."""
    root = report.plugin_dir
    skills = root / "skills"
    if not skills.is_dir():
        return
    for sub in sorted(skills.iterdir()):
        if not sub.is_dir() or sub.name.startswith("."):
            continue
        if not KEBAB_RE.match(sub.name):
            report.add("R3", "error", _rel(sub, root),
                       f"skill 目录名 {sub.name!r} 非 kebab-case")
            continue
        skill_md = sub / "SKILL.md"
        if not skill_md.exists():
            # 检查是否有小写变体 (常见错误)
            lower = sub / "skill.md"
            detail = "找到 skill.md (应大写 SKILL.md)" if lower.exists() else "缺 SKILL.md"
            report.add("R3", "error", _rel(sub, root), detail)


def check_r4(report: LintReport) -> None:
    """R4: agents/*.md 文件名 kebab-case."""
    root = report.plugin_dir
    agents = root / "agents"
    if not agents.is_dir():
        return
    for f in sorted(agents.glob("*.md")):
        if not KEBAB_RE.match(f.stem):
            report.add("R4", "error", _rel(f, root),
                       f"agent 文件名 {f.stem!r} 非 kebab-case")


def check_r5(report: LintReport) -> None:
    """R5: 产物/临时文件不泄漏."""
    root = report.plugin_dir
    for p in sorted(root.rglob("*")):
        if not p.exists():
            continue
        rel = _rel(p, root)
        # 跳过 lint.py 自身所在 skill 目录的合法文件
        if p.is_file():
            if p.name in ARTIFACT_FILES:
                report.add("R5", "warning", rel,
                           f"产物文件泄漏: {p.name}")
            elif p.suffix in ARTIFACT_SUFFIXES:
                report.add("R5", "warning", rel, f"编译产物泄漏: {p.name}")
        elif p.is_dir():
            if p.name in ARTIFACT_DIRS:
                report.add("R5", "warning", rel, f"缓存目录泄漏: {p.name}")
            elif any(p.name.endswith(s) for s in ARTIFACT_DIR_SUFFIXES):
                report.add("R5", "warning", rel, f"备份目录泄漏: {p.name}")


def check_r6(report: LintReport) -> None:
    """R6: plugin.json 中 agents/skills/commands 路径真实存在."""
    root = report.plugin_dir
    pj = root / ".claude-plugin" / "plugin.json"
    if not pj.exists():
        return
    try:
        data = json.loads(pj.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return  # R1 已报
    for field_name in ("commands", "agents", "skills", "hooks"):
        val = data.get(field_name)
        if val is None:
            continue
        paths = val if isinstance(val, list) else [val]
        for entry in paths:
            entry_str = str(entry)
            # 支持 ./ 前缀
            target = root / entry_str.lstrip("./").lstrip("/")
            if not target.exists():
                report.add("R6", "error", _rel(pj, root),
                           f"{field_name} 路径 {entry_str!r} 不存在 "
                           f"(期望 {target.relative_to(root)})")


def check_r7(report: LintReport) -> None:
    """R7: skill SKILL.md frontmatter name == 目录名."""
    root = report.plugin_dir
    skills = root / "skills"
    if not skills.is_dir():
        return
    for sub in sorted(skills.iterdir()):
        if not sub.is_dir() or sub.name.startswith("."):
            continue
        skill_md = sub / "SKILL.md"
        if not skill_md.exists():
            continue  # R3 已报
        try:
            text = skill_md.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = _parse_frontmatter(text)
        if fm is None:
            continue
        fm_name = fm.get("name")
        if fm_name and fm_name != sub.name:
            report.add("R7", "warning", _rel(skill_md, root),
                       f"frontmatter name={fm_name!r} != 目录名 {sub.name!r}")


ALL_CHECKS = [
    ("R1", check_r1), ("R2", check_r2), ("R3", check_r3),
    ("R4", check_r4), ("R5", check_r5), ("R6", check_r6),
    ("R7", check_r7),
]


def find_plugin_root(start: Path) -> Path | None:
    """从 start 上溯找含 .claude-plugin/ 的目录."""
    p = start.resolve()
    for candidate in [p, *p.parents]:
        if (candidate / ".claude-plugin" / "plugin.json").exists():
            return candidate
    return None


def print_report(report: LintReport, fix_hints: bool) -> int:
    root = report.plugin_dir
    name = root.name
    print(f"\n{name} lint report")
    print("─" * (len(name) + 13))

    # 每规则聚合输出
    for rule_id, _ in ALL_CHECKS:
        rule_vs = [v for v in report.violations if v.rule == rule_id]
        if not rule_vs:
            print(f"✓ {rule_id:<28} PASS")
        else:
            sev = rule_vs[0].severity.upper()
            mark = "✗" if rule_vs[0].severity == "error" else "!"
            print(f"{mark} {rule_id:<28} {sev}  ({len(rule_vs)} 项)")
            for v in rule_vs:
                print(f"      {v.path}")
                print(f"        {v.message}")
                if fix_hints and v.fix_hint:
                    print(f"        fix: {v.fix_hint}")

    n_err = len(report.errors)
    n_warn = len(report.warnings)
    print(f"\nSummary: {n_err} error, {n_warn} warning", end="")
    if n_err == 0 and n_warn == 0:
        print(" → 全 PASS")
        return 0
    if n_err > 0:
        print(f" → exit 1 (有 error)")
        return 1
    print(f" → exit 2 (仅 warning)")
    return 2


def main() -> int:
    ap = argparse.ArgumentParser(description="novelist 插件目录结构 lint")
    ap.add_argument("--plugin-dir", type=Path, default=None,
                    help="插件根目录 (默认上溯找 .claude-plugin/)")
    ap.add_argument("--fix-hints", action="store_true",
                    help="每条违规附修复建议 (只打印, 不执行)")
    args = ap.parse_args()

    if args.plugin_dir:
        root = args.plugin_dir.resolve()
    else:
        root = find_plugin_root(Path(__file__).resolve())
    if root is None or not (root / ".claude-plugin" / "plugin.json").exists():
        print("ERROR: 找不到插件根 (含 .claude-plugin/plugin.json)", file=sys.stderr)
        return 3

    report = LintReport(plugin_dir=root)
    for _, check in ALL_CHECKS:
        try:
            check(report)
        except Exception as e:
            report.add("RUNTIME", "error", str(check.__name__),
                       f"lint 自身异常: {e!r}")

    return print_report(report, args.fix_hints)


if __name__ == "__main__":
    sys.exit(main())
