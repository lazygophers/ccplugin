---
title: cold-start 模糊信号判据 + Job Story 愿景翻译
layer: recall
category: skill
keywords: [cold-start,模糊需求,Job Story,When/I want/so I can,relentless interview]
source: cold-start-large-req-2026-07-20
authored-by: skein-spec
created: 1784541787
status: active
related: []
updated: 1784541787
---

# cold-start 模糊信号判据 + Job Story 愿景翻译

## 触发场景
收到用户需求时，若需求描述模糊（无动词泛指/无实现路径/字数少/愿景腔），需触发 cold-start 流程，通过 relentless interview 引导用户明确需求。

## 模糊信号判据（命中任一条即触发）
1. **无动词泛指**：需求描述无明确动词（如"优化用户体验"而非"将页面加载时间从 3s 降到 1.5s"）
2. **无实现路径**：仅说结果但无实现思路（如"做个聊天功能"但无协议/存储/实时性方案）
3. **字数 < 15**：需求描述过短，信息密度不足
4. **愿景腔**：纯愿景描述无具体约束（如"让用户更开心"但无业务指标/用户场景）

## Job Story 三段式
```
When [情境],
I want [行为],
so I can [价值/目标].
```

## said/implied/missing 三分法
| 维度 | 定义 | 处理 |
|------|------|------|
| said | 用户明确说出的需求 | 直接实现 |
| implied | 用户暗示的需求（需推理） | 推理后确认 |
| missing | 用户未说但必需的 | 填 Open Questions，≤3 轮假设→Assumptions 段禁埋正文 |

## relentless interview 自写纪律
- 插件内闭环自写问题引导用户明确需求
- 禁依赖外部 `/grilling` 手工驱动
- 每轮返回需含：澄清问题 + 建议答案框架 + 下一步计划
- 假设需显式标记为 Assumptions，禁混入正文

## 适用场景
- 后续大需求（需求字数 > 200 字或涉及多模块）会复用此流程
- 小需求可跳过，直接实现

## 关联
- 参考 `grill 加轴标准范式` 进行需求审查
