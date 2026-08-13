from __future__ import annotations

import json
import os
import re

from skeinlib.hooks.util import git_root

_FLOW_CROSS = ("以及", "同时", "另外", "还有", "顺便", "一起", "都要", "分别")
_FLOW_NEW = ("新模块", "新功能", "新接口", "新页面", "新组件", "骨架", "脚手架", "框架", "原型", "poc")
_FLOW_PATH_RE = re.compile(r"(?:\./[^/\s]+|(?<![A-Za-z0-9])/[\w.-]+/[\w./-]+|[\w-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|md|yaml|yml|json|sh))")
_FLOW_STEPS = ("然后", "接着", "步骤", "之后", "再")
_FLOW_VERBS = ("改", "加", "删", "重构", "修复", "实现", "迁移", "替换", "新增", "修改", "重写", "调整",
               "搭建", "搭", "建立", "创建", "写", "开发", "接入", "对接", "部署", "上线",
               "设计", "优化", "规划", "排查", "定位")
_INLINE_Q = ("什么是", "为什么", "解释", "区别", "对比", "怎么用", "如何用", "是什么", "怎么写", "怎么样", "如何")
_PHASE = {"pending": "plan", "research": "research", "active": "exec", "check": "check", "finishing": "finishing"}
_EXPLICIT = {
    "go", "exec", "do", "plan", "继续", "continue",
    "continue from where you left off",
    "please continue from where you left off",
    "continue the conversation from where we left it off",
}
_SLASH_COMMAND_RE = re.compile(r"^/[A-Za-z][\w:-]*(?=\s|$)")
# skein 自家 skill: 各自有完整闭环, 判定层放行让 skill 自判, 不锁 inline 也不额外注入。
_SKEIN_SKILLS = {"skein-flow", "skein-plan", "skein-redo", "skein-spec", "skein-grill", "skein-setup"}
_SKEIN_SKILL_RE = re.compile(
    # 长名在前: 避免短前缀先匹上长名被尾界卡掉
    rf"(?<![\w:-])(?:skein:)?(?:{'|'.join(re.escape(s) for s in sorted(_SKEIN_SKILLS, key=len, reverse=True))})(?=$|\s)"
)
_WRAPPER_RE = re.compile(r"<(ide_[a-z_]+|system-reminder)\b[^>]*>.*?</\1>\s*", re.DOTALL)


def _user_prompt_text(prompt: str) -> str:
    return _WRAPPER_RE.sub("", prompt).strip()


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


def cmd_user_prompt(payload: dict[str, object]) -> int:
    raw = payload.get("prompt", "") or ""
    prompt = raw if isinstance(raw, str) else str(raw)
    prompt_text = _user_prompt_text(prompt)

    # 开头点名了 skill/command: 锁 inline, 禁判定层推 flow 建 task。
    # 点的是 skein 自家 skill 时放行 —— 它们各自有闭环, 降级成 inline 等于把用户明确选的路径废掉。
    if _SLASH_COMMAND_RE.match(prompt_text) or prompt_text.startswith("skein-"):
        if _SKEIN_SKILL_RE.search(prompt_text):
            return 0
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": (
                "# 任务判定 (已锁定)\n\n"
                "本轮开头显式点名了 skill/command → 判定固定为 inline: 在 main 里直接执行, "
                "**无论任务多复杂**, 禁调 skein-flow / 禁建 task。\n"
                "判定行照写: `[skein] 判定: inline (原因: 开头显式指定 skill/command)`"),
        }}))
        return 0

    explicit_continuation = prompt_text.rstrip("。.!！?？").casefold() in _EXPLICIT
    cwd = payload.get("cwd") or os.getcwd()
    root = git_root(cwd if isinstance(cwd, str) else os.getcwd())
    skein_dir = os.path.join(root, ".skein")
    if not os.path.isdir(os.path.join(root, ".git")) and not os.path.isdir(skein_dir):
        return 0
    # 未初始化 = 用户没选用 skein, 静默退出。skein 是可选工具, 判定层不劝进也不拦路。
    if not os.path.exists(os.path.join(skein_dir, "config.yaml")):
        return 0
    phase_hints = task_phase_hints(skein_dir)
    if explicit_continuation:
        if not phase_hints:
            return 0
        context = "# SKEIN 续跑上下文"
    else:
        evidence = judge_signal(prompt_text)
        context = "# 任务判定\n\n判定行格式: `[skein] 判定: <flow/plan/inline/补充> (原因: <本轮命中的判据>)`"
        if evidence:
            context += f"\n机械判定: {', '.join(evidence)}"
    if phase_hints:
        context += "\n" + phase_hints
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit", "additionalContext": context}}))
    return 0


__all__ = ["cmd_user_prompt", "judge_signal", "task_phase_hints"]
