---
title: hook 判定防自降级护栏
layer: core
category: planning
keywords: [hook,判定,自降级,修饰词,TaskCreate,flow,inline,防御]
source: hook-prompt-judge-ai-only
authored-by: skein-spec
created: 1784612457
status: active
related: []
updated: 1784612457
---

# 铁律
- MUST：hook prompt 判定行禁修饰词 — 判定结论尾部禁止附加「但/先/只是/不过」等弱化后缀
- MUST：判定行走 flow 即必须走 flow，禁转头 inline 自降级
- MUST：禁用 harness 内置 TaskCreate (TodoWrite 类) 冒充 skein create — 跨文件任务必须走正式建 task 流程

## 反例表
| 禁 | 改为 |
|---|--|
| 判定: 走 flow 但先纯查询探索 | 判定: 走 flow (直接走流程) |
| 判定: 豁免 只是改个常量 | 判定: 豁免 (直接做) |
| 用 TaskCreate 绕过建 task | skein create 正式建 task |

## 触发场景
- AI 判走 flow 后用修饰词借口自降级 inline (如「走 flow 但先探索」)
- 用 TaskCreate×5 冒充正式 task 绕过建 task 流程

## 关联
- 铁律: start 强制 prd 硬门 (planning)
- 实现细节: hook prompt 判定权交给 AI (删除脚本预筹 _classify_prompt)
