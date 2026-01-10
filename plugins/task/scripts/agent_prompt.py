#!/usr/bin/env python3
"""
Task Plugin Agent Prompt
任务管理插件的系统提示词定义
"""

# 任务管理插件的系统提示词（内置魔法字符串）
TASK_AGENT_PROMPT = """### 任务管理插件

**必须使用`task@ccplugin-market`插件作为任务管理工具**

当需要对项目任务进行管理时，使用 `task@ccplugin-market` 插件。其主要功能包括：

- 创建新任务
- 更新任务状态
- 查看任务列表
- 导出任务到 Markdown 文件

完整的 **skills** 信息位于 `${CLAUDE_PLUGIN_ROOT}/skills/task/SKILL.md` 文件中。
"""


def get_task_agent_prompt() -> str:
    """获取任务管理插件的系统提示词"""
    return TASK_AGENT_PROMPT


__all__ = ["TASK_AGENT_PROMPT", "get_task_agent_prompt"]
