"""文档里的 CLI 示例必须真能跑 — 拿真实 Typer help 逐条校验。

## 为什么需要这条
skill / agent 文档里的命令示例**会被 AI 照抄执行**。一条写错的示例不是排版问题, 是 agent 当场
发出无效命令然后开始猜。而 CLI 改了参数、文档没跟上, 没有任何东西会报警 —— 首次跑这个校验时
一次性揪出 16 处失效示例, 包括 `skein cancel`(命令不存在)、`skein finish --force`、
`skein deps --tree/--reverse`、`skein list --all`、`skein task show`(应为 `skein status`)、
`skein-spec archive --deep=`(archive 只认 --namespace) 等。

## 合法面从哪来
不硬编码, 现跑 `--help` 解析: 顶层子命令 → 各自 flag → 二级子命令 (`prd read` / `subtask add`
/ `config set` …) 及其 flag。所以新增命令自动纳入, 删掉的也不会留下永远红的断言。

## 刻意不管的
- `/skein-spec reconstruct` 这类**斜杠开头**的是 skill 模式 (slash command), 不是 CLI 子命令,
  跳过。文档里若把模式名写成 `skein-spec reconstruct` (无斜杠) 会被判错 —— 这正是要抓的,
  因为那样写 agent 会真去敲 CLI。
- `del/delete/rm/remove` 四个别名需要逐个校验。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import MEM, SCRIPTS, SKEIN  # noqa: E402

PLUGIN = SCRIPTS.parent
ALIASES = ("del", "delete", "rm", "remove")   # dispatch 里有, --help 不列
# 散文里的假阳性: README 讲名字来源「skein of yarn」
PROSE_SKIP = ("skein of",)

CMD_RE = re.compile(
    r"(?:`|^|\s|\"|<br/>)(skein-spec|skein\.py|spec\.py|skein)\s+([a-z][a-z0-9\-_]*)"
    r"((?:\s+[^\n`|\"]*)?)")


def _commands_from_help(text: str) -> list[str]:
    out, started = [], False
    for ln in text.splitlines():
        if "<command>" in ln or " Commands " in ln:
            started = True
            continue
        if not started:
            continue
        if " Options " in ln or ln.strip().startswith(("options:", "optional", "╰")):
            break
        # Typer rich: `│ init              ...`; argparse: `    init              ...`。
        m = re.match(r"^\s*(?:│\s*)?([a-z][a-z0-9\-_]*)(?:\s{2,}|$)", ln)
        if m:
            out.append(m.group(1))
    return sorted(set(out))


def _top_subs(script: Path) -> list[str]:
    r = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    return _commands_from_help(r.stdout)


def _probe(script: Path, *sub: str) -> tuple[set[str], set[str]] | tuple[None, None]:
    """返回 (该命令的 flag 集, 它的二级子命令集)。命令不存在 → (None, None)。"""
    r = subprocess.run([sys.executable, str(script), *sub, "--help"], capture_output=True, text=True)
    if r.returncode != 0:
        return None, None
    usage = r.stdout.split("positional")[0]      # flag 只认 usage 行, 免把说明文字里的词当参数
    subs = set(_commands_from_help(r.stdout))
    m = re.search(r"\{([a-z0-9,\-_]+)\}", r.stdout)
    if m:
        subs |= set(m.group(1).split(","))
    return set(re.findall(r"(--[a-z][a-z0-9\-]*)", usage)), subs


def _cli_surface() -> dict[str, dict[str, set[str]]]:
    surface: dict[str, dict[str, set[str]]] = {}
    for tool, script in (("skein", SKEIN), ("spec", MEM)):
        surface[tool] = {}
        for cmd in _top_subs(script):
            flags, subs = _probe(script, cmd)
            surface[tool][cmd] = flags or set()
            for s in subs or ():
                f2, _ = _probe(script, cmd, s)
                surface[tool][f"{cmd} {s}"] = f2 or set()
    for a in ALIASES:
        flags, _ = _probe(SKEIN, a)
        if flags is not None:
            surface["skein"][a] = flags
    return surface


def _doc_files() -> list[Path]:
    files = [p for p in PLUGIN.rglob("*.md") if ".archive" not in str(p)]
    files += list((PLUGIN / "docs").glob("*.mmd"))
    return sorted(files)


def _scan(files: list[Path] | None = None) -> list[str]:
    cli = _cli_surface()
    problems: list[str] = []
    for f in (files if files is not None else _doc_files()):
        for i, ln in enumerate(f.read_text(errors="ignore").splitlines(), 1):
            if any(s in ln for s in PROSE_SKIP):
                continue
            for m in CMD_RE.finditer(ln):
                if m.group(0).lstrip().startswith("/"):
                    continue                      # slash command = skill 模式, 非 CLI
                tool = "spec" if m.group(1) in ("skein-spec", "spec.py") else "skein"
                cmd, rest = m.group(2), (m.group(3) or "")
                rel = f.relative_to(PLUGIN) if PLUGIN in f.parents else f.name
                if cmd not in cli[tool]:
                    problems.append(f"{rel}:{i} `{tool} {cmd}` 不是 CLI 子命令 — {ln.strip()[:80]}")
                    continue
                words = rest.split()
                key = f"{cmd} {words[0]}" if words and f"{cmd} {words[0]}" in cli[tool] else cmd
                legal = cli[tool][key] | {"--help"}
                for flag in re.findall(r"(--[a-z][a-z0-9\-]*)", rest):
                    if flag not in legal:
                        problems.append(f"{rel}:{i} `{tool} {key}` 没有 {flag} — {ln.strip()[:80]}")
    return problems


def test_all_doc_command_examples_are_valid() -> None:
    problems = _scan()
    assert not problems, (
        f"文档里有 {len(problems)} 条 CLI 示例跑不通 (AI 会照抄执行):\n  " + "\n  ".join(problems))


def test_scanner_actually_catches_bad_examples(tmp_path: Path) -> None:
    """自检: 喂假文档必须被抓出来 —— 否则上面那条哪天因正则写崩而永远绿, 谁也发现不了。

    喂进去的四行分别覆盖: 假子命令 / 假参数 / slash 命令(该放行) / 真命令(该放行)。
    """
    doc = tmp_path / "fake.md"
    doc.write_text(
        "| `skein cancel <id>` | 假子命令 |\n"
        "| `skein list --all` | 假参数 |\n"
        "`/skein-spec reconstruct` 是 skill 模式, 该放行\n"
        "`skein confirm <id> --approved` 是真命令, 该放行\n")
    problems = _scan([doc])
    assert len(problems) == 2, f"该抓 2 条 (假子命令+假参数), 实际 {len(problems)}: {problems}"
    joined = "\n".join(problems)
    assert "cancel" in joined and "--all" in joined, joined
    assert "reconstruct" not in joined, "slash 开头的 skill 模式被误判成 CLI 命令"
    assert "--approved" not in joined, "真命令被误判"


def test_confirm_gate_flags_are_documented() -> None:
    """人审门的两个参数必须在文档里出现 —— 否则 main 不知道该怎么走对话确认那条路。"""
    joined = "\n".join(p.read_text(errors="ignore") for p in _doc_files())
    for token in ("--summary", "--approved", "AskUserQuestion"):
        assert token in joined, f"文档没写 {token}, main 无从知道人审门怎么过"


if __name__ == "__main__":
    probs = _scan()
    for p in probs:
        print("  " + p)
    print(f"文档命令校验: {len(probs)} 处问题")
    raise SystemExit(1 if probs else 0)
