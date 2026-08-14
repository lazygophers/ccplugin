from __future__ import annotations

import json
import os
import re

from skeinlib.hooks.util import git_root

_EXPLICIT = {
	"go", "exec", "do", "plan", "继续", "continue",
	"continue from where you left off",
	"please continue from where you left off",
	"continue the conversation from where we left it off",
}
_SLASH_COMMAND_RE = re.compile(r"^/[A-Za-z][\w:-]*(?=\s|$)")
_WRAPPER_RE = re.compile(r"<(ide_[a-z_]+|system-reminder)\b[^>]*>.*?</\1>\s*", re.DOTALL)


def _user_prompt_text(prompt: str) -> str:
	return _WRAPPER_RE.sub("", prompt).strip()


def task_phase_hints() -> str:
	"""从 task 包取结构化 task 列表, 只列 plan(pending)/research 两个阶段的 (id | 阶段 | name)。"""
	from skeinlib.core.workspace import Workspace
	from skeinlib.task.model import TaskStatus
	live = [t for t in Workspace().store.all_tasks()
	        if t["status"] in (TaskStatus.PENDING, TaskStatus.RESEARCH)]
	if not live:
		return ""
	rows = "\n".join(f"- {t['id']} | {'plan' if t['status'] == TaskStatus.PENDING else 'research'} | {t.get('name', '')}"
	                 for t in live)
	return f"""

当前 task (plan/research):
{rows}
处理其一时前缀用其 [skein|id|阶段]"""


def cmd_user_prompt(payload: dict[str, object]) -> int:
	raw = payload.get("prompt", "") or ""
	prompt = raw if isinstance(raw, str) else str(raw)
	prompt_text = _user_prompt_text(prompt)

	# 开头点名了 skill/command: 锁 inline, 禁判定层推 flow 建 task。
	# 点的是 skein 自家 skill 时放行 —— 它们各自有闭环, 降级成 inline 等于把用户明确选的路径废掉。
	if _SLASH_COMMAND_RE.match(prompt_text) or prompt_text.startswith("skein-"):
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
	phase_hints = task_phase_hints()
	if not explicit_continuation:
		print(json.dumps({"hookSpecificOutput":
			{
				"hookEventName": "UserPromptSubmit",
				"additionalContext": f"""用户输入了指令，你需要先根据指令判断任务类型，判定行格式: `[skein] 判定: <flow/plan/inline/补充> (原因: <本轮命中的判据>)。然后继续执行，并确保不会因为用户新的指令就丢失了前序内容。
对于不确定的内容，除非是特别简单的任务或查询类、调研类的，都按 flow 判。
如果用户指定了 skills, 则按 inline 判。
{phase_hints}"""},
		}))
	return 0


__all__ = ["cmd_user_prompt", "task_phase_hints"]
