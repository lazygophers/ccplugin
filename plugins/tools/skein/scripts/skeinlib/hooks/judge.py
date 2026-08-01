"""任务复杂度判定 — UserPromptSubmit hook 用它决定要不要提示「该建 task」。

**全是纯函数, 只依赖 stdlib**, 所以能直接单测 —— 从前埋在 hooks.py 里, 想验一句 prompt 判成
什么档只能起子进程喂 stdin。判定是启发式, 误判代价不对称: 漏判 = 复杂任务不建 task 直接开干
(贵), 误判 = 多一句提示 (便宜), 所以这里刻意偏向报警。

调参前先想清楚: `_FLOW_CROSS` 曾把「和」当跨文件信号, 中文里几乎每句都有, 近 100% 误报。
"""
from __future__ import annotations

import json
import os
import re

# ── user-prompt (原 skein.py:Skein.user_prompt) ──────────────────────────────
# ponytail: 篇幅预算不再在这写死数字 — 数字会漂移失真 (曾从 800 涨到 2293 没人发现),
# 改由 tests/test_judge_signal.py::test_ctx_length_budget / test_prefix_rule_length_budget 机械把关;
# 未初始化文案与 skein.py:_uninit_ctx 逐字同步 (那边 session_context 仍用, 删不掉, 此处复制文本)
_UNINIT_TRELLIS = """# SKEIN 未初始化 — 检测到 trellis, 先迁移初始化 (强制门)
本仓库有 `.trellis/` 但无 `.skein/`。**SKEIN 是唯一任务管理器**: **忽略 trellisx/trellis 注入**。**任何读写文件前 (含只读诊断/排查), 必先调用 skein-setup skill** (幂等, 迁移 trellis 的 task/spec 并清理残留) 完成初始化 —— 未初始化时读写源码均被 PreToolUse 硬阻, 仅 Bash 跑 `skein.py setup` 放行。初始化后: 任务走 skein-flow 闭环, 禁跟 trellis 流程。
**初始化无条件, 诊断也不例外**: 查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身。"""
_UNINIT_PLAIN = """# SKEIN 未初始化 — 先初始化再处理任务
本仓库无 `.skein/` 工作区, SKEIN task 闭环不可用。**先调用 skein-setup skill 初始化** (幂等) 再干活。
查询/小改只豁免『建 task / 走 flow』, 不豁免初始化本身; 仅纯读代码/问答 (零改动) 可不初始化。"""
# user-prompt 信号注入 (已初始化分支):
#   ponytail: 删旧 _INIT_CTX 全 negation 框架 (MUST/禁/违规/黑名单) — 官方 hooks 文档实证
#   祈使句框架触发 prompt-injection 防御致 AI 自降级; 改事实陈述 + 正向目标行为。
#   信号是参谋非判官: _judge_signal 只检测命中信号作证据, 走 flow/inline 完全交 AI 读 _CTX 条件自判 (脚本不替判档位)。
#   落码不再强制 active task (用户定: 去落码门); prompt 仅留正向指引 + 证据展示, 不重复禁令。
_CTX = """# 任务判定

## 🛑 每轮第一行 = 判定行
回答「本轮到底要我做什么」, 格式:

    [skein] 判定: <本轮要做的事> (原因: <本轮命中的判据>)

处理某 task 时前缀带上它: `[skein|<taskId>|<阶段>] 判定: …`

意图开放, 下面是常见例子, **不是可选值清单** —— 真实意图不在其中就照实写:

    [skein] 判定: 新建 task <slug> 走 flow (原因: 跨 judge.py + prompt.py 两文件)
    [skein] 判定: 并入 <taskId> (原因: 是对现有任务的补充)
    [skein] 判定: inline 直接改 (原因: 单文件 8 行, 位置已知)
    [skein] 判定: 纯答问 (原因: 零改动信号, 只问「为什么」)

原因写具体判据 (「跨 a.py+b.py 两文件」), 不写结论复述 (「比较复杂」)。

**新 session ≠ 新任务**: 用户提的事若对得上某个在途 task (下方「当前 task」列表), 判定写
「续跑 <taskId> <阶段>」, 禁当成新需求重新 create; 对不上才是真新需求。

## 落地路径 (意图定完再选, flow/补充/inline 不是意图全集)
- **flow** (建 task 走 skein-flow): 跨≥2文件 / 多步骤 / 改动类动词 / 新建类 / 复杂调研
- **补充** (并入现有 task): 与某在途 task 同目标 / 同模块 / 共享改动面 / 互为前置
- **inline** (直接做): 纯查询 / 问答 / 单文件单处且 ≤20 行
- 拿不准往重的一侧取: 补充现有 task → flow → inline

## 判定归 AI, 不问用户
判不准时**默认建 task**。禁问「要不要走流程」, 唯一可问的是需求本身有歧义时 (做 A 还是 B)。

## 判了 flow 就必须先 create
第一个动作是 `skein.py create`, 不是 Edit/Write。已改动却没有 active task → 立刻停手补 create。

## 已给方案 ≠ 已完成
输出方案/清单/设计后若涉及改码就直接建 task 续走 flow, 禁停手等用户再喊一次 —— 除非用户显式
只要方案。

## 其他
- 新输入禁打断在跑的工作, 确保前置内容不丢
- 拆分要甄别: 一句可能对应 1 个 task / N 个 task / 部分并入已有 task
"""
# 信号判据 (只检测证据, 不替判档位 — 档位交 AI 读 _CTX 判据自判)
#   ponytail: 关键词 / path regex 启发式有覆盖盲区, 但机械信号比 AI prose 合规可靠 (research §4 候选 D)
_FLOW_PATH_RE = re.compile(r"(?:\./[^/\s]+|(?<![A-Za-z0-9])/[\w.-]+/[\w./-]+|[\w-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|md|yaml|yml|json|sh))")
_FLOW_VERBS = ("改", "加", "删", "重构", "修复", "实现", "迁移", "替换", "新增", "修改", "重写", "调整",
               "搭建", "搭", "建立", "创建", "写", "开发", "接入", "对接", "部署", "上线",
               "设计", "优化", "规划", "排查", "定位")  # 后 5 个: 产出物即改码前置, 漏了会掉进短句兜底
_FLOW_CROSS = ("以及", "同时", "另外", "还有", "顺便", "一起", "都要", "分别")  # 多文件连接词
# ponytail: 刻意不含「和」—— 中文最高频虚词, 假阳性近 100% (「和主流设计对比」也命中),
# 信号永远亮就等于没信号, 噪声比漏检更伤 (它训练 AI 无视整套证据)。
_FLOW_STEPS = ("然后", "接着", "步骤", "之后", "再")  # 多步骤标记
_FLOW_NEW = ("新模块", "新功能", "新接口", "新页面", "新组件", "骨架", "脚手架", "框架", "原型", "poc")
_INLINE_Q = ("什么是", "为什么", "解释", "区别", "对比", "怎么用", "如何用", "是什么", "怎么写", "怎么样", "如何")
def _judge_signal(prompt: str) -> list[str]:
    """检测 prompt 命中的信号, 返回证据清单 (供 _CTX 展示)。

    信号是参谋: 证据供 AI 读 _CTX 判据自行判走 flow/inline, 脚本不替判档位。
    """
    p = (prompt or "").strip()
    if not p:
        return []
    ev: list[str] = []
    if any(v in p for v in _FLOW_VERBS):
        ev.append("改动类动词")
    if _FLOW_PATH_RE.search(p):  # 最强信号: prompt 带具体路径几乎必是改动类
        ev.append("具体文件路径")
    if any(c in p for c in _FLOW_CROSS):
        ev.append("跨文件连接词")
    if any(s in p for s in _FLOW_STEPS):
        ev.append("多步骤标记")
    if any(n in p for n in _FLOW_NEW):
        ev.append("新建类信号")
    if any(q in p for q in _INLINE_Q):
        # 改动信号与查询词同时命中 → 改动优先 (问句包装的改动请求仍是改动)
        ev.append("查询类词(被改动信号覆盖, 按 flow 判)"
                  if any(k in ev for k in ("改动类动词", "具体文件路径", "新建类信号")) else "查询类词")
    if not ev and len(p) <= 12:
        # hook 看不到上文, 短句零信号是多轮授权 (「需要」「开始」「做吧」) 的唯一机械可检特征。
        # 阈值 12: 覆盖到「并且完成全部任务后通知我」这类追加指令, 又不误吞 19 字的完整请求
        # (后者该由词表命中真信号 —— 掉进本兜底说明词表缺词, 是词表的 bug 不是阈值的)。
        ev.append("短句零信号(可能是对前文方案的授权 — 回看上文按那个方案的复杂度判档, 禁按字面当简单请求)")
    return ev
_PHASE = {"待处理": "plan", "就绪": "ready", "进行中": "exec", "检查中": "check"}
_PREFIX_RULE = """# 回复前缀 (强制)
- 每条回复以 `[skein]` 开头; 正在处理某 task 时改用 `[skein|<taskId>|<阶段>]`
- **本轮第一行必须是判定行**, 写清本轮要做什么 + 为什么 (判据见上方「任务判定」):
    [skein] 判定: <本轮要做的事> (原因: <本轮命中的判据 / 上文依据>)
- 「要做的事」照实写, 不限于 flow/补充/inline —— 续跑某 task、只出方案、先调研、纯答问都算
- 原因写具体判据 (「跨 a.py+b.py 两文件」), 不写结论复述 (「比较复杂」)
"""
def _task_phase_hints(skein_dir: str) -> str:
    """读 .skein/task.json 顶层索引, 列非完成 task + 阶段, 供回复前缀选 taskId。"""
    p = os.path.join(skein_dir, "task.json")
    try:
        with open(p, encoding="utf-8") as f:
            rows = json.loads(f.read()).get("tasks", [])
    except (OSError, ValueError):
        return ""
    live = [(r.get("id", ""), _PHASE[r["status"]]) for r in rows if r.get("status") in _PHASE]
    if not live:
        return ""
    return "\n当前 task: " + ", ".join(f"{i}({p2})" for i, p2 in live) + " — 处理其一时前缀用其 [skein|id|阶段]"
