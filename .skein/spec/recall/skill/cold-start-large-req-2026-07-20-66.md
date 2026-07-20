---
title: grill 加轴标准范式
layer: recall
category: skill
keywords: [grill,加轴,反例表,wishful,SMARC,drift,scope]
source: cold-start-large-req-2026-07-20
authored-by: skein-spec
created: 1784541802
status: active
related: []
updated: 1784541802
---

# grill 加轴标准范式

## 触发场景
需求审查需加轴或删轴时，必须同步更新审查轴表 + 反例表，防止遗漏对照。

## 标准范式

### 审查轴表加轴
- 加轴时：在审查轴表中新增行（轴名 + 判据）
- **必须同步**：在反例表中新增对照行（反例 + 改为 + 违反的轴）

### 反例表配套
- 反例表结构：`| 反例 | 改为 | 违反轴 |`
- 加轴时必填对应反例，禁留空反例表行
- 禁用 `|` 代替"改为"，必须显式写出正向方案

### wishful 词清单（可复用判据）
常见 wishful 词作为需求模糊的信号判据：
- user-friendly（无具体指标）
- 快速（无基线/目标）
- 好用（无场景/任务）
- 灵活（无约束范围）

### SMARC/drift/scope 三轴
| 轴 | 判据 |
|----|------|
| **SMARC** | AC 可测性：验收条件可量化验证 |
| **drift** | 产出 vs 愿景：实现结果与 Job Story 价值对齐 |
| **scope** | 边界守卫：不超源诉求，防 gold-plating |

## 适用场景
- 需求审查时每次加轴/删轴必须同步双表
- 反例表用于快速对照检查

## 关联
- 参考 `cold-start 模糊信号判据 + Job Story 愿景翻译`
