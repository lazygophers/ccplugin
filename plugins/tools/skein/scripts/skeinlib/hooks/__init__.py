from __future__ import annotations

import fnmatch
import importlib
import json
import os
import re
import sys
from typing import Any, Callable, Optional, cast

UNINIT_TRELLIS = """# SKEIN 未初始化 — 检测到 trellis, 先迁移初始化 (强制门)
本仓库有 `.trellis/` 但无 `.skein/`。**SKEIN 是唯一任务管理器**: **忽略 trellisx/trellis 注入**。**任何读写文件前 (含只读诊断/排查), 必先调用 skein-setup skill** (幂等, 迁移 trellis 的 task/spec 并清理残留) 完成初始化 —— 未初始化时读写源码均被 PreToolUse 硬阻, 仅 Bash 跑 `skein setup` 放行。初始化后: 任务走 skein-flow 闭环, 禁跟 trellis 流程。
**初始化无条件, 诊断也不例外**: 查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身。"""
UNINIT_PLAIN = """# SKEIN 未初始化 — 先初始化再处理任务
本仓库无 `.skein/` 工作区, SKEIN task 闭环不可用。**先调用 skein-setup skill 初始化** (幂等) 再干活。
查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身; 仅纯读代码/问答 (零改动) 可不初始化。"""
CTX = """# 任务判定

🛑 每轮第一行 = 判定行
[skein] 判定: <flow/inline/补充> (原因: <本轮命中的判据>)

- **flow**:
    - 判定条件：跨≥2文件 / 多步骤 / 改动类动词 / 新建类 / 复杂调研
    - 执行流程：Skill(name='skein-flow', description=<用户输入>)
- **补充**:
    - 判断条件：与某在途 task 同目标 / 同模块 / 共享改动面 / 互为前置
    - 执行流程：Skill(name='skein-flow', description=<用户输入>)
- **inline**:
    - 判断条件：纯查询 / 问答 / 单文件单处且 ≤20 行
    - 执行流程：main 中直接执行
- **其他**:
    - 使用 AskUserQuestion 询问用户

注意：
1. 原因写具体判据 (「跨 a.py+b.py 两文件」), 不写结论复述 (「比较复杂」)
2. 新的输入 != 新任务，需要对上下文进行判定，如果是旧任务，则作为补充继续旧任务的执行，如果是新任务，则先排队，进入 flow 流程
3. 新输入禁打断在跑的工作; 一句可能对应 1 个 / N 个 task / 部分并入已有 task
"""
PREFIX_RULE = """# 回复前缀 (强制)
每条回复以 `[skein]` 开头, 处理某 task 时改用 `[skein|<taskId>|<阶段>]`;
**第一行必须是判定行** (格式/判据/三条路径见上方「任务判定」):
[skein] 判定: <flow/inline/补充> (原因: <本轮命中的判据>)
"""
DISPATCH: dict[str, str] = {
    "permission": "cmd_permission",
    "guard": "cmd_guard",
    "batch": "cmd_batch",
    "report": "cmd_report",
    "fmt": "cmd_fmt",
    "spec-meta": "cmd_spec_meta",
    "flow-gate": "cmd_flow_gate",
    "stop-check": "cmd_stop_check",
    "user-prompt": "cmd_user_prompt",
    "agent-start": "cmd_agent_hook",
    "agent-stop": "cmd_agent_hook",
}
_UNINIT_TRELLIS = UNINIT_TRELLIS
_UNINIT_PLAIN = UNINIT_PLAIN
_CTX = CTX
_PREFIX_RULE = PREFIX_RULE
_ARGV_DISPATCH = {"agent-start", "agent-stop"}


def git_root(start: str) -> str:
    directory = os.path.abspath(start or ".")
    while True:
        if os.path.isdir(os.path.join(directory, ".git")):
            return directory
        parent = os.path.dirname(directory)
        if parent == directory:
            return os.path.abspath(start or ".")
        directory = parent


def load_stdin() -> Optional[dict[str, Any]]:
    try:
        return cast(dict[str, Any], json.load(sys.stdin))
    except (json.JSONDecodeError, ValueError):
        return None


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    frontmatter: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip().strip("[]")
    return frontmatter


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def find_filematch_specs(spec_root: str) -> list[tuple[Any, list[str], str]]:
    from pathlib import Path
    if not os.path.exists(spec_root):
        return []
    matches: list[tuple[Any, list[str], str]] = []
    try:
        for root, _, files in os.walk(spec_root):
            for filename in files:
                if not filename.endswith(".md"):
                    continue
                path = Path(root) / filename
                try:
                    text = path.read_text()
                    metadata = parse_frontmatter(text)
                    if metadata.get("inclusion", "") != "fileMatch":
                        continue
                    globs = [item.strip() for item in metadata.get("globs", "").split(",") if item.strip()]
                    body = strip_frontmatter(text).strip()
                    if globs and body:
                        matches.append((path, globs, body))
                except (OSError, UnicodeDecodeError):
                    continue
    except OSError:
        return []
    return matches


def file_matches_globs(file_path: str, globs: list[str], workspace_root: str) -> bool:
    from pathlib import PurePath
    try:
        absolute_path = os.path.abspath(file_path)
        absolute_root = os.path.abspath(workspace_root)
        if not absolute_path.startswith(absolute_root):
            return False
        relative_path = os.path.relpath(absolute_path, absolute_root)
    except ValueError:
        return False
    return any(fnmatch.fnmatch(relative_path, glob) or PurePath(relative_path).match(glob) for glob in globs)


def filematch_context(file_path: str, workspace_root: str) -> str:
    sections: list[str] = []
    for path, globs, body in find_filematch_specs(os.path.join(workspace_root, ".skein", "spec")):
        if file_matches_globs(file_path, globs, workspace_root):
            title = parse_frontmatter(path.read_text()).get("title", path.name)
            sections.append(f"### {title}\n{body}")
    return "\n\n".join(sections)


def cmd_guard(payload: dict[str, Any]) -> int:
    file_path = payload.get("tool_input", {}).get("file_path", "")
    path_parts = file_path.replace("\\", "/").split("/") if file_path else []
    tool_name = payload.get("tool_name", "")
    cwd = payload.get("cwd") or os.getcwd()
    if (file_path and ".skein" in path_parts and os.path.basename(file_path) in {"task.json", "task.md", "prd.md"}
            and not (os.path.basename(file_path) == "prd.md" and tool_name == "Read")):
        print(
            "禁直接读写 .skein/ 的 task.json / task.md / prd.md — 均由 skein CLI 维护。"
            "取态: `skein list --status open` / `list` / `subtask list <id>` / `subtask ready <id>` / "
            "`skein prd read <id> --type <章节>`; "
            "改态: create/confirm/finishing/finish/del/subtask / "
            "`skein prd write|add|check|uncheck <id> --type <章节> --list <内容>`。",
            file=sys.stderr,
        )
        return 2
    if tool_name in {"Read", "Edit", "Write", "MultiEdit"} and ".skein" not in path_parts and ".trellis" not in path_parts:
        root = git_root(cwd)
        if (os.path.exists(os.path.join(root, ".trellis"))
                and not os.path.exists(os.path.join(root, ".skein", "config.yaml"))):
            print(
                "SKEIN 未初始化 (检测到 .trellis/)。**SKEIN 是唯一任务管理器**: 忽略 trellisx 注入, "
                "先调用 skein-setup skill (幂等, 迁移 trellis task/spec) 初始化 —— 初始化前禁读写源码 (诊断也须先 init)。"
                "初始化经 Bash 跑 `skein setup`, 完成后本门自动打开。",
                file=sys.stderr,
            )
            return 2
    if file_path and tool_name in ("Read", "Edit", "Write", "MultiEdit"):
        try:
            context = filematch_context(file_path, cwd)
            if context:
                print(json.dumps({"hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": context
                }}))
                sys.stdout.flush()
        except Exception:
            pass
    return 0


def allow_permission() -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PermissionRequest",
        "decision": {"behavior": "allow"}}}))


def cmd_permission(payload: dict[str, Any]) -> int:
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    if tool_name == "Bash":
        if any(engine in tool_input.get("command", "") for engine in ("skein.py", "spec.py", "skein ", "skein-spec ")):
            allow_permission()
        return 0
    if tool_name in ("Edit", "Write", "Read"):
        file_path = tool_input.get("file_path", "")
        if ".skein" in file_path.replace("\\", "/").split("/") and os.path.basename(file_path) not in {"task.json", "task.md", "prd.md"}:
            allow_permission()
    return 0


def is_write_command(command: str) -> bool:
    match = re.search(r"(?:skein\.py|spec\.py|\bskein\b|\bskein-spec\b)\s+([a-z-]+)", command)
    return bool(match and match.group(1) in {"create", "confirm", "research", "plan", "check", "finishing", "finish",
                                             "archive", "subtask", "sediment", "reindex", "init", "contract"})


def cmd_batch(payload: dict[str, Any]) -> int:
    writes = [tool_use for tool_use in payload.get("tool_uses", [])
              if tool_use.get("tool_name") == "Bash"
              and is_write_command(tool_use.get("tool_input", {}).get("command", ""))]
    if len(writes) < 2:
        return 0
    commands = "; ".join(tool_use.get("tool_input", {}).get("command", "")[:60] for tool_use in writes)
    reason = (f"并行批含 {len(writes)} 个 .skein 状态写命令 ({commands}) — 同写 task.json/spec 有竞态, "
              "后写覆盖前写。改为串行: 一个命令一个回合, 或用 `subtask claim` 一次性认领整批。")
    print(json.dumps({"decision": "block", "reason": reason,
                      "hookSpecificOutput": {"hookEventName": "PostToolBatch",
                                             "additionalContext": reason}}))
    return 0


def cmd_report(payload: dict[str, Any]) -> int:
    command = payload.get("tool_input", {}).get("command", "")
    if not (any(marker in command for marker in ("skein.py", "spec.py", "CLAUDE_PLUGIN_ROOT"))
            or re.search(r"(?:^|[\s;&|(])(?:skein-spec|skein)(?:\s|$)", command)):
        return 0
    error = (payload.get("tool_error", "") or "").strip()[:800]
    output: dict[str, Any] = {}
    if "Traceback (most recent call last)" in error:
        output["hookSpecificOutput"] = {"hookEventName": "PostToolUseFailure", "additionalContext": (
            f"SKEIN 脚本崩溃 (未捕获异常):\n命令: {command[:200]}\n错误: {error}\n"
            "这不是参数问题 — 引擎的门拒绝只出一行人话, 出 traceback 说明有异常没接住。")}
        output["systemMessage"] = (
            "⚠️ SKEIN 脚本崩溃 (traceback), 疑似插件 bug 请手动开 issue: https://github.com/lazygophers/ccplugin/issues/new "
            "(附命令+错误+复现步骤)")
    else:
        output["hookSpecificOutput"] = {"hookEventName": "PostToolUseFailure", "additionalContext": (
            f"SKEIN 命令被拒 (非崩溃, 属正常校验):\n命令: {command[:200]}\n错误: {error}\n"
            "照错误提示改参数/补前置状态即可 — 这是引擎的门在起作用, 不是 bug。")}
    print(json.dumps(output))
    return 0


def cmd_fmt(payload: dict[str, Any]) -> int:
    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return 0
    normalized_path = file_path.replace("\\", "/")
    match = re.search(r"(?:^|/)\.skein/task/([^/]+)/prd\.md$", normalized_path)
    if not match:
        return 0
    root = normalized_path[:match.start()] or (payload.get("cwd") or os.getcwd())
    import subprocess
    from skeinlib.paths import SKEIN_ENTRY
    try:
        subprocess.run([sys.executable, str(SKEIN_ENTRY), "fmt", match.group(1)], cwd=root,
                       capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass
    return 0


def parse_spec_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[4:end] if text[3] == "\n" else text[3:end]
    frontmatter: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line or line.startswith((" ", "\t", "-")):
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip()
    return frontmatter


def spec_frontmatter_text(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end < 0:
        return ""
    return text[4:end] if text[3] == "\n" else text[3:end]


def cmd_spec_meta(payload: dict[str, Any]) -> int:
    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return 0
    normalized_path = file_path.replace("\\", "/")
    if not re.search(r"(?:^|/)\.skein/spec/[^/]+/[^/]+/.+\.md$", normalized_path):
        return 0
    try:
        with open(file_path, encoding="utf-8") as file:
            text = file.read()
    except OSError:
        return 0
    metadata = parse_spec_frontmatter(text)
    warnings: list[str] = []
    for key in ("title", "namespace", "inclusion", "keywords"):
        value = metadata.get(key, "")
        if key == "keywords" and not value.strip("[] ").strip():
            warnings.append("缺失: keywords")
        elif key != "keywords" and not value:
            warnings.append(f"缺失: {key}")
    frontmatter_text = spec_frontmatter_text(text).lower()
    if metadata.get("inclusion", "") == "fileMatch" and "globs:" not in frontmatter_text and "globs =" not in frontmatter_text:
        warnings.append("缺失: inclusion=fileMatch 时需配置 globs")
    namespace = metadata.get("namespace", "")
    if namespace in ("product", "map") and "anchors:" not in frontmatter_text and "anchors =" not in frontmatter_text:
        warnings.append(f"缺失: namespace={namespace} 时需配置 anchors")
    if warnings:
        short_path = normalized_path.split(".skein/spec/")[-1] if ".skein/spec/" in normalized_path else normalized_path
        context = f"⚠️ spec metadata 检查 ({short_path}):\n  - " + "\n  - ".join(warnings)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": context}}))
    return 0


def cmd_flow_gate(payload: dict[str, Any]) -> int:
    file_path = (payload.get("tool_input", {}) or {}).get("file_path", "")
    if not file_path or not file_path.endswith((".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb",
                                               ".php", ".c", ".cc", ".cpp", ".h", ".hpp", ".swift", ".kt", ".sh")):
        return 0
    normalized_path = file_path.replace("\\", "/")
    if ".skein/" in normalized_path or "/tests/" in normalized_path or "/test_" in normalized_path:
        return 0
    skein_dir = os.path.join(git_root(payload.get("cwd") or os.getcwd()), ".skein")
    if not os.path.exists(os.path.join(skein_dir, "config.yaml")):
        return 0
    try:
        with open(os.path.join(skein_dir, "task.json"), encoding="utf-8") as file:
            tasks = json.loads(file.read()).get("tasks", [])
        if any(task.get("status") in ("进行中", "检查中") for task in tasks):
            for path in (os.path.join(skein_dir, ".edit-tally"), os.path.join(skein_dir, ".edit-tally.warned")):
                if os.path.exists(path):
                    os.remove(path)
            return 0
    except (OSError, ValueError):
        return 0
    tally_path = os.path.join(skein_dir, ".edit-tally")
    warned_path = os.path.join(skein_dir, ".edit-tally.warned")
    if os.path.exists(warned_path):
        return 0
    import time
    try:
        seen: set[str] = set()
        if os.path.exists(tally_path) and time.time() - os.path.getmtime(tally_path) < 4 * 3600:
            with open(tally_path, encoding="utf-8") as file:
                seen = {line.strip() for line in file if line.strip()}
        seen.add(normalized_path)
        with open(tally_path, "w", encoding="utf-8") as file:
            file.write("\n".join(sorted(seen)))
        if len(seen) < 2:
            return 0
        open(warned_path, "w").close()
    except (OSError, ValueError):
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": (
        f"⚠️ 已改动 {len(seen)} 个源码文件但**无 active task** — 跨 ≥2 文件正是 flow 的判据线。\n"
        "若这本该走 flow: 立刻 `skein task create` 建 task, 把已改的纳入首个 subtask, 后续改动在 flow 内做。\n"
        "若确属 inline 豁免 (如同一处改动波及两文件): 忽略本提示, 继续。\n"
        f"已改: {', '.join(sorted(seen)[:5])}")}}))
    return 0


def judge_signal(prompt: str) -> list[str]:
    text = (prompt or "").strip()
    if not text:
        return []
    evidence: list[str] = []
    if any(verb in text for verb in ("改", "加", "删", "重构", "修复", "实现", "迁移", "替换", "新增", "修改", "重写", "调整",
                                     "搭建", "搭", "建立", "创建", "写", "开发", "接入", "对接", "部署", "上线",
                                     "设计", "优化", "规划", "排查", "定位")):
        evidence.append("改动类动词")
    if re.search(r"(?:\./[^/\s]+|(?<![A-Za-z0-9])/[\w.-]+/[\w./-]+|[\w-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|md|yaml|yml|json|sh))", text):
        evidence.append("具体文件路径")
    if any(word in text for word in ("以及", "同时", "另外", "还有", "顺便", "一起", "都要", "分别")):
        evidence.append("跨文件连接词")
    if any(word in text for word in ("然后", "接着", "步骤", "之后", "再")):
        evidence.append("多步骤标记")
    if any(word in text for word in ("新模块", "新功能", "新接口", "新页面", "新组件", "骨架", "脚手架", "框架", "原型", "poc")):
        evidence.append("新建类信号")
    if any(word in text for word in ("什么是", "为什么", "解释", "区别", "对比", "怎么用", "如何用", "是什么", "怎么写", "怎么样", "如何")):
        if any(item in evidence for item in ("改动类动词", "具体文件路径", "新建类信号")):
            evidence.append("查询类词(被改动信号覆盖, 按 flow 判)")
        else:
            evidence.append("查询类词")
    if not evidence and len(text) <= 12:
        evidence.append("短句零信号(可能是对前文方案的授权 — 回看上文按那个方案的复杂度判档, 禁按字面当简单请求)")
    return evidence


def task_phase_hints(skein_dir: str) -> str:
    try:
        with open(os.path.join(skein_dir, "task.json"), encoding="utf-8") as file:
            tasks = json.loads(file.read()).get("tasks", [])
    except (OSError, ValueError):
        return ""
    phases = {"pending": "plan", "research": "research", "active": "exec", "check": "check", "finishing": "finishing"}
    live = [(task.get("id", ""), phases[task["status"]]) for task in tasks if task.get("status") in phases]
    if not live:
        return ""
    return "\n当前 task: " + ", ".join(f"{task_id}({phase})" for task_id, phase in live) + " — 处理其一时前缀用其 [skein|id|阶段]"


_judge_signal = judge_signal
_task_phase_hints = task_phase_hints


def run_config(skein_dir: str) -> tuple[bool, int, bool]:
    from skeinlib.config import CONFIG_DEFAULTS, Config
    try:
        config = Config(os.path.join(skein_dir, "config.yaml")).cfg.model_dump(by_alias=True)
    except (OSError, ValueError):
        config = CONFIG_DEFAULTS
    worker_limit = config["pools"]["work"]
    env_worker_limit = os.environ.get("CLAUDE_PLUGIN_OPTION_MAX_ACTIVE")
    if env_worker_limit and env_worker_limit.strip().isdigit():
        worker_limit = int(env_worker_limit)
    return bool(config["worktree"]["enabled"]), int(worker_limit), bool(config["auto_commit"])


def cmd_user_prompt(payload: dict[str, Any]) -> int:
    prompt = (payload.get("prompt", "") or "").strip()
    if prompt in ("go", "exec", "do", "plan", "继续", "continue") or prompt.startswith(("/skein-", "/skein:skein-", "skein-")):
        return 0
    root = git_root(payload.get("cwd") or os.getcwd())
    skein_dir = os.path.join(root, ".skein")
    if not os.path.isdir(os.path.join(root, ".git")) and not os.path.isdir(skein_dir):
        return 0
    if not os.path.exists(os.path.join(skein_dir, "config.yaml")):
        context = UNINIT_TRELLIS if os.path.isdir(os.path.join(root, ".trellis")) else UNINIT_PLAIN
    else:
        evidence = judge_signal(payload.get("prompt", "") or "")
        context = CTX
        if evidence:
            context += f"\n本次命中: {', '.join(evidence)}"
        phase_hints = task_phase_hints(skein_dir)
        context += "\n\n" + PREFIX_RULE + phase_hints
        if phase_hints:
            worktree_enabled, worker_limit, auto_commit = run_config(skein_dir)
            worktree_text = "启用 (task 各开 worktree 隔离)" if worktree_enabled else "禁用 (原地执行, 无 worktree)"
            auto_commit_text = ("强制 (worktree 模式必自动 commit, 本配置不生效)" if worktree_enabled
                                else ("启用 (finish 时自动 commit)" if auto_commit else "禁用 (改动需手动 commit)"))
            context += f"\n\n# SKEIN 运行配置\n- worktree: {worktree_text}\n- 最大并行 subtask: {worker_limit}\n- auto_commit: {auto_commit_text}"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": context}}))
    return 0


def cmd_stop_check(_: dict[str, Any]) -> int:
    from datetime import datetime
    from skeinlib.spec.facade import Spec
    from skeinlib.spec.model import always_budget_tokens
    from skeinlib.token_conversion import estimate_tokens_from_chars
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


def cmd_agent_hook(when: str) -> int:
    argv = sys.argv[2:]
    options = {argv[index][2:]: argv[index + 1] for index in range(0, len(argv) - 1, 2) if argv[index].startswith("--")}
    agent = options.get("agent", "")
    task_id = options.get("tid", "")
    subtask_id = options.get("sid", "")
    root = git_root(options.get("cwd") or os.getcwd())
    import yaml  # type: ignore[import-untyped]
    try:
        config_path = os.path.join(root, ".skein", "config.yaml")
        if not os.path.exists(config_path):
            return 0
        with open(config_path, encoding="utf-8") as file:
            config = yaml.safe_load(file)
    except (OSError, ValueError, yaml.YAMLError):
        return 0
    hooks = config.get("hooks") if isinstance(config, dict) else None
    agents = hooks.get("agent") if isinstance(hooks, dict) else None
    if not isinstance(agents, dict):
        return 0
    commands = [command for key in (agent, "*")
                if isinstance(agents.get(key), dict)
                for command in (agents[key].get(when) or [])]
    if not commands:
        return 0
    _run_hooks("agent", when, {"hooks": commands, "agent": agent, "tid": task_id, "sid": subtask_id, "repo_root": root})
    try:
        from skeinlib.spec.facade import Spec
        Spec()._write_audit("agent-hook", f"agent.{agent}", when, f"{len(commands)} hooks", f"tid={task_id} sid={subtask_id}")
    except (OSError, ValueError):
        pass
    return 0


def debug_enabled(args: Any = None) -> bool:
    if args is not None and getattr(args, "debug", False):
        return True
    return os.environ.get("SKEIN_DEBUG", "").strip().lower() not in ("", "0", "false", "no")


class Debug:
    def __init__(self, enabled: bool) -> None:
        self.enabled = False
        self.c: Optional[Any] = None
        self.enable(enabled)

    def enable(self, on: bool) -> None:
        self.enabled = on
        if on and self.c is None:
            try:
                from rich.console import Console
                self.c = Console(stderr=True)
            except Exception:
                self.c = None

    def log(self, message: str, style: Optional[str] = None) -> None:
        if self.enabled:
            self._emit(message, style)

    def warn(self, message: str) -> None:
        self._emit(message, "yellow")

    def error(self, message: str) -> None:
        self._emit(message, "red")

    def _emit(self, message: str, style: Optional[str] = None) -> None:
        if self.c is None:
            try:
                from rich.console import Console
                self.c = Console(stderr=True)
            except Exception:
                pass
        if self.c:
            self.c.print(message, style=style, markup=False, highlight=False)
        else:
            sys.stderr.write(f"{message}\n")

    def rule(self, title: str) -> None:
        if not self.enabled:
            return
        if self.c:
            self.c.rule(f"[bold cyan]{title}")
        else:
            sys.stderr.write(f"\n──── {title} ────\n")

    def kv(self, mapping: dict[str, Any], title: Optional[str] = None) -> None:
        if not self.enabled or not mapping:
            return
        if self.c:
            from rich.table import Table
            table = Table(show_header=False, box=None, title=title, title_justify="left", title_style="dim")
            table.add_column(style="cyan", no_wrap=True)
            table.add_column(overflow="fold")
            for key, value in mapping.items():
                table.add_row(str(key), str(value))
            self.c.print(table)
        else:
            if title:
                sys.stderr.write(f"{title}\n")
            for key, value in mapping.items():
                sys.stderr.write(f"  {key}: {value}\n")


DBG = Debug(False)


def est_tokens(text: str) -> int:
    return len(text) // 4


def budget_guard(text: str, budget_tokens: int, label: str) -> str:
    tokens = est_tokens(text)
    if tokens <= budget_tokens:
        return text
    sys.stderr.write(
        f"[skein hook:{label}] 注入内容 ~{tokens} token > 预算 {budget_tokens} — "
        f"请简化 (core 规则降级 recall / 精简正文), 已硬截断到 {budget_tokens} token\n")
    return text[:budget_tokens * 4] + "\n\n… (超预算已截断, 见 stderr)"


class HookBlocked(RuntimeError):
    pass


def prefix_lines(tag: str, text: str) -> str:
    return "".join(f"{tag} {line}\n" for line in text.splitlines())


def _prefix_lines(tag: str, text: str) -> str:
    return prefix_lines(tag, text)


def _run_hooks(scope: str, when: str, context: dict[str, Any]) -> None:
    hooks = context.get("hooks") or []
    if not hooks or os.environ.get("SKEIN_IN_HOOK"):
        return
    blocking = scope != "agent" and when == "before"
    cwd_default = context.get("worktree") or context.get("repo_root") or "."
    env = dict(os.environ)
    env.update({
        "SKEIN_SCOPE": scope, "SKEIN_WHEN": when,
        "SKEIN_AGENT": context.get("agent", ""),
        "SKEIN_TID": context.get("tid", ""), "SKEIN_SID": context.get("sid", ""),
        "SKEIN_TASK_DIR": context.get("task_dir", ""),
        "SKEIN_WORKTREE": context.get("worktree", ""),
        "SKEIN_REPO_ROOT": context.get("repo_root", ""),
        "SKEIN_IN_HOOK": "1",
    })
    import subprocess
    for index, hook in enumerate(hooks, 1):
        tag = f"[hook {scope}.{when}#{index}]"
        timeout = hook.get("timeout", 60)
        continue_on_error = hook.get("continue_on_error", when != "before")
        try:
            result = subprocess.run(hook.get("command", ""), shell=True, cwd=hook.get("cwd") or cwd_default, env=env,
                                    capture_output=True, text=True, timeout=timeout)
            if result.stdout:
                sys.stdout.write(prefix_lines(tag, result.stdout))
            if result.stderr:
                sys.stderr.write(prefix_lines(tag, result.stderr))
            ok, detail = result.returncode == 0, f"exit {result.returncode}"
        except subprocess.TimeoutExpired:
            ok, detail = False, f"超时(>{timeout}s)"
            sys.stderr.write(f"{tag} {detail}\n")
        if ok:
            continue
        if continue_on_error:
            sys.stderr.write(f"{tag} 失败({detail}), continue_on_error=true, 继续\n")
            continue
        message = f"{tag} 失败({detail}), 串行执行终止"
        if blocking:
            raise HookBlocked(message)
        sys.stderr.write(f"{message} (仅告警, 不阻断)\n")
        return


def _resolve(name: str) -> Callable[..., int]:
    return cast(Callable[..., int], globals()[DISPATCH[name]])


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.stderr.write(f"用法: skein-hooks {{{'|'.join(DISPATCH)}}}\n")
        return 2
    name = sys.argv[1]
    command = _resolve(name)
    if name in {"agent-start", "agent-stop"}:
        return command(name.split("-", 1)[1])
    payload = load_stdin()
    if payload is None:
        return 0
    return command(payload)


def self_check() -> int:
    cases: list[tuple[str, list[str]]] = [
        ("改 hooks.py 和 spec.py 的判定", ["具体文件路径", "改动类动词"]),
        ("在 src/auth.py 加 login 函数", ["具体文件路径", "改动类动词"]),
        ("参考 admin-api 搭建骨架, 用 go-zero 脚手架", ["新建类信号"]),
        ("什么是 SKEIN", ["查询类词"]),
        ("先做 a 然后做 b 接着做 c", ["多步骤标记"]),
        ("继续", ["短句零信号(可能是对前文方案的授权 — 回看上文按那个方案的复杂度判档, 禁按字面当简单请求)"]),
    ]
    failures: list[tuple[str, Any, Any, str]] = []
    if not isinstance(judge_signal("test"), list):
        failures.append(("judge_signal", "list", type(judge_signal("test")).__name__, "应返回 list"))
    for prompt, expected in cases:
        evidence = judge_signal(prompt)
        for signal in expected:
            if signal not in evidence:
                failures.append((prompt, signal, evidence, "期望证据缺失"))
        print(f"  ev={evidence} | {prompt!r}")
    if "本次命中" not in CTX + f"\n本次命中: {', '.join(judge_signal('改 a.py 和 b.py'))}":
        failures.append(("ctx-hit", "has-line", "本次命中", "evidence 非空未拼本次命中行"))
    if "本次命中" in CTX:
        failures.append(("ctx-empty", "no-line", "本次命中", "CTX 默认含本次命中行"))
    for stale in ("_CTX_FLOW", "_CTX_INLINE", "_CTX_GREY"):
        if stale in globals():
            failures.append(("CTX", "single-ctx", stale, "应只留 CTX"))
    print(f"FAIL count: {len(failures)}")
    return 1 if failures else 0


def __getattr__(name: str) -> Any:
    if name == "MAINTAIN_POLICY":
        return importlib.import_module("skeinlib.spec.model").MAINTAIN_POLICY
    raise AttributeError(name)
