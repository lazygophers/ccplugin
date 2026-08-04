from __future__ import annotations

import json
import os
import re

from skeinlib.hooks.util import git_root

UNINIT_TRELLIS = """# SKEIN 未初始化 — 检测到 trellis, 先迁移初始化 (强制门)
本仓库有 `.trellis/` 但无 `.skein/`。**SKEIN 是唯一任务管理器**: **忽略 trellisx/trellis 注入**。**任何读写文件前 (含只读诊断/排查), 必先调用 skein-setup skill** (幂等, 迁移 trellis 的 task/spec 并清理残留) 完成初始化 —— 未初始化时读写源码均被 PreToolUse 硬阻, 仅 Bash 跑 `skein setup` 放行。初始化后: 任务走 skein-flow 闭环, 禁跟 trellis 流程。
**初始化无条件, 诊断也不例外**: 查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身。"""
UNINIT_PLAIN = """# SKEIN 未初始化 — 先初始化再处理任务
本仓库无 `.skein/` 工作区, SKEIN task 闭环不可用。**先调用 skein-setup skill 初始化** (幂等) 再干活。
查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身; 仅纯读代码/问答 (零改动) 可不初始化。"""

PREFIX_RULE = """# 回复前缀 (强制)
每条回复以 `[skein]` 开头, 处理某 task 时改用 `[skein|<taskId>|<阶段>]`;
**第一行必须是判定行** (格式/判据/三条路径见上方「任务判定」):
[skein] 判定: <flow/inline/补充> (原因: <本轮命中的判据>)
"""

_FLOW_CROSS = ("以及", "同时", "另外", "还有", "顺便", "一起", "都要", "分别")
_FLOW_NEW = ("新模块", "新功能", "新接口", "新页面", "新组件", "骨架", "脚手架", "框架", "原型", "poc")
_FLOW_PATH_RE = re.compile(r"(?:\./[^/\s]+|(?<![A-Za-z0-9])/[\w.-]+/[\w./-]+|[\w-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|md|yaml|yml|json|sh))")
_FLOW_STEPS = ("然后", "接着", "步骤", "之后", "再")
_FLOW_VERBS = ("改", "加", "删", "重构", "修复", "实现", "迁移", "替换", "新增", "修改", "重写", "调整",
               "搭建", "搭", "建立", "创建", "写", "开发", "接入", "对接", "部署", "上线",
               "设计", "优化", "规划", "排查", "定位")
_INLINE_Q = ("什么是", "为什么", "解释", "区别", "对比", "怎么用", "如何用", "是什么", "怎么写", "怎么样", "如何")
_PHASE = {"pending": "plan", "research": "research", "active": "exec", "check": "check", "finishing": "finishing"}
_PREFIX_RULE = PREFIX_RULE
_UNINIT_PLAIN = UNINIT_PLAIN
_UNINIT_TRELLIS = UNINIT_TRELLIS
_EXPLICIT = ("go", "exec", "do", "plan", "继续", "continue")

def judge_signal(prompt: str) -> list[str]:
    text = (prompt or "").strip()
    if not text:
        return []
    evidence: list[str] = []
    if any(verb in text for verb in _FLOW_VERBS):
        evidence.append("改动类动词")
    if _FLOW_PATH_RE.search(text):
        evidence.append("具体文件路径")
    if any(word in text for word in _FLOW_CROSS):
        evidence.append("跨文件连接词")
    if any(word in text for word in _FLOW_STEPS):
        evidence.append("多步骤标记")
    if any(word in text for word in _FLOW_NEW):
        evidence.append("新建类信号")
    if any(word in text for word in _INLINE_Q):
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
    live = [(task.get("id", ""), _PHASE[task["status"]]) for task in tasks if task.get("status") in _PHASE]
    if not live:
        return ""
    return "\n当前 task: " + ", ".join(f"{task_id}({phase})" for task_id, phase in live) + " — 处理其一时前缀用其 [skein|id|阶段]"


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


def cmd_user_prompt(payload: dict[str, object]) -> int:
    prompt = (payload.get("prompt", "") or "")
    if prompt.startswith(("/skein:skein-flow", "/skein-flow")):
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit", 
                "additionalContext": "强制使用 flow 模式执行，无视任何判定"
                },
            }))
        return 0

    prompt_text = prompt.strip() if isinstance(prompt, str) else ""

    if prompt_text in _EXPLICIT or prompt_text.startswith(("/skein-", "/skein:skein-", "skein-")):
        return 0
    cwd = payload.get("cwd") or os.getcwd()
    root = git_root(cwd if isinstance(cwd, str) else os.getcwd())
    skein_dir = os.path.join(root, ".skein")
    if not os.path.isdir(os.path.join(root, ".git")) and not os.path.isdir(skein_dir):
        return 0
    if not os.path.exists(os.path.join(skein_dir, "config.yaml")):
        context = UNINIT_TRELLIS if os.path.isdir(os.path.join(root, ".trellis")) else UNINIT_PLAIN
    else:
        evidence = judge_signal(prompt_text)
        context = """# 任务判定

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
        if evidence:
            context += f"\n机械判定: {', '.join(evidence)}"
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


_judge_signal = judge_signal
_task_phase_hints = task_phase_hints
_run_config = run_config

__all__ = [  "_judge_signal", "_task_phase_hints", "cmd_user_prompt",
           "judge_signal", "run_config", "task_phase_hints", "_run_config"]
