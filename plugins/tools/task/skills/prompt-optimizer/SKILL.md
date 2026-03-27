---
description: 提示词优化规范 - 评估质量、识别模糊点、结构化提问、生成优化提示词
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (2500+ tokens) -->

# Skills(task:prompt-optimizer) - 提示词优化规范

## 范围

优化模糊/不完整的用户任务描述。适用于：模糊需求("优化代码")、缺乏目标("添加功能")、隐含假设过多、Loop提示词优化阶段。

## 核心原则（Anthropic 2025）

| 原则 | 好 | 差 |
|------|---|---|
| 明确性 | "实现JWT认证，含token生成和验证" | "处理认证" |
| 上下文 | "在Express.js API v4.18中添加认证中间件" | "添加认证" |
| 范围边界 | "包含：邮箱登录。不包含：社交登录" | "实现登录" |
| 可量化 | "覆盖率≥90%，响应<200ms" | "质量要好" |
| 结构化输出 | "返回JSON {token, user, expiresAt}" | "返回信息" |
| 错误处理 | "密码错误401，锁定403，服务错误500" | "处理错误" |

## 5W1H 评估框架

| 维度 | 关键问题 |
|------|---------|
| What(目标) | 功能/交付物/成功标准 |
| Why(动机) | 业务问题/价值 |
| Who(受众) | 目标用户/体验要求 |
| When(时间) | 完成时间/优先级/里程碑 |
| Where(范围) | 影响模块/部署环境/交互组件 |
| How(方式) | 技术方案/栈/架构模式 |

质量评分：清晰度(0-10) + 完整性(0-10) + 可执行性(0-10)。详见 best-practices.md。

<!-- /STATIC_CONTENT -->

<!-- DYNAMIC_CONTENT -->

## 调用

`Skill(skill="task:prompt-optimizer", args="优化用户提示词：\n原始提示：{input}\n要求：1.评估质量 2.得分<6搜索最佳实践 3.5W1H提问 4.生成优化提示词 5.得分≥8返回no_optimization_needed")`

结果处理：status=no_optimization_needed→使用原始 | status=optimized→使用优化后提示词

## 优化模板

`# 任务目标` → `## 背景和动机` → `## 技术上下文`(类型/栈/状态/依赖) → `## 具体要求` → `## 范围边界`(包含/不包含) → `## 验收标准` → `## 时间和优先级`

## 输出格式

JSON：status(optimized/no_optimization_needed) + quality_score{clarity,completeness,actionability,overall} + original_prompt + optimized_prompt + improvements[] + questions_asked + web_searches + report

<!-- /DYNAMIC_CONTENT -->
