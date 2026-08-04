from __future__ import annotations

import re

from skeinlib.hooks import CTX, PREFIX_RULE, UNINIT_PLAIN, UNINIT_TRELLIS, judge_signal, task_phase_hints

_CTX = CTX
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
_judge_signal = judge_signal
_task_phase_hints = task_phase_hints
