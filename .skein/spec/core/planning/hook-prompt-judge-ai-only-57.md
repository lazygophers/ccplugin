---
title: hook 判定防自降级护栏
layer: core
category: planning
keywords: [hook,判定,自降级,修饰词,TaskCreate,flow,inline,防御,信号证据,证据展示]
source: hook-prompt-judge-ai-only
authored-by: skein-spec
created: 1784619036
status: active
related: []
updated: 1784619036
---

# 铁律
- MUST：hook prompt 判定行禁修饰词 — 判定结论尾部禁止附加「但/先/只是/不过」等弱化后缀
- MUST：判定行走 flow 即必须走 flow，禁转头 inline 自降级
- MUST：禁用 harness 内置 TaskCreate (TodoWrite 类) 冒充 skein create — 跨文件任务必须走正式建 task 流程
- MUST：信号从判官降为参谋 — _judge_signal 只检测命中信号作证据（返回 list[str]），走 flow/inline 完全交 AI 读 _CTX 判据自判，脚本不替判档位
- MUST：单一 _CTX 展示判据 + {evidence} 动态证据 + 建议语调（非强制），禁三套 _CTX_FLOW/_CTX_INLINE/_CTX_GREY 分档注入

## 反例表
| 禁 | 改为 |
|---|--|
| 判定: 走 flow 但先纯查询探索 | 判定: 走 flow (直接走流程) |
| 判定: 豁免 只是改个常量 | 判定: 豁免 (直接做) |
| 用 TaskCreate 绕过建 task | skein create 正式建 task |
| _judge_signal 返回 flow/inline/grey 档位 | 返回 list[str] 证据清单（如 `["文件路径×2", "改动类动词"]`） |
| 三套 _CTX_FLOW/_CTX_INLINE/_CTX_GREY 选档注入 | 单一 _CTX 含判据 + {evidence} + 建议语调 |

## 触发场景
- AI 判走 flow 后用修饰词借口自降级 inline (如「走 flow 但先探索」)
- 用 TaskCreate×5 冒充正式 task 绕过建 task 流程
- hooks.py cmd_user_prompt 实现（信号检测 + _CTX 注入）

## 信号证据展示范式
**从档位判定到证据收集**（落实「判定权交给 AI」）:

- 旧: `_judge_signal(prompt)` → `"flow"/"inline"/"grey"` 档位 → 三套 _CTX_FLOW/_CTX_INLINE/_CTX_GREY 选档注入
- 新: `_judge_signal(prompt)` → `list[str]` 证据清单（如 `["文件路径×2", "改动类动词"]`） → 单一 _CTX 展示判据 + {evidence} 动态插入 + 建议语调，AI 读判据自判

**关键变化**:
1. `_judge_signal` 返回 `list[str]`（证据）而非 `"flow"/"inline"/"grey"` 档位
2. 三常量 `_CTX_FLOW`/`_CTX_INLINE`/`_CTX_GREY` 合并为单一 `_CTX`:
   ```
   _CTX = """# SKEIN 判定 (信号仅建议, AI 综合上下文定夺)
   判据: 走 flow = 跨≥2文件/多步骤/改动类动词/新建类 | 可 inline = 纯查询/问答/单文件单处 | 判不清 = AskUserQuestion。
   本次命中: {evidence}
   → 倾向 flow: skein create 建 task 走 skein-flow; 倾向 inline: 直接答/改; 判不清: AskUserQuestion。"""
   ```
3. `cmd_user_prompt` 直接 `_CTX.format(evidence=", ".join(_judge_signal(prompt)))` 注入，删 dict 选档逻辑

**证据检测维度**（保持原有启发式）:
- 文件路径（`_FLOW_PATH_RE` 检测 → `文件路径×N`）
- 改动类动词（`改/加/删/重构/修复/实现/迁移/替换/新增/修改/重写/调整`）
- 跨文件连接词（`和/与/及/同时`）
- 多步骤标记（`然后/接着/之后`）
- 新建类信号（`新模块/新功能/新接口/新页面/新组件/新端点`）
- 查询类词（`什么/为什么/怎么/如何/解释`）

**约束**:
- MUST：{evidence} 占位符必须被替换（脚本内 `format` 调用，非残留占位符）
- MUST：_CTX 文本禁 MUST/禁/违规/黑名单（正向化，避免 prompt-injection 防御触发自降级）
- MUST：判定语调为建议（"倾向 flow/可 inline/判不清"），非强制

## 关联
- 铁律: start 强制 prd 硬门 (planning)
- 实现细节: hook prompt 判定权交给 AI (删除脚本预筹 _classify_prompt)
- 代码证据: plugins/tools/skein/scripts/hooks.py `_judge_signal` + `_CTX` + cmd_user_prompt
- 演进 commits: 7302da23→e6714966→d4432bb1→8bf64241→6f2b153 (最终态 6f2b153)
