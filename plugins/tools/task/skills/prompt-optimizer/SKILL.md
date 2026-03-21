---
agent: task:prompt-optimizer
description: 提示词优化规范 - 评估质量、识别模糊点、结构化提问、生成优化提示词
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (4800+ tokens) -->

# Skills(task:prompt-optimizer) - 提示词优化规范

<scope>

当你需要优化用户的任务描述时使用此 skill。适用于：
- 模糊的任务需求（如"优化代码"、"改进系统"）
- 缺乏明确目标的描述（如"添加功能"但未说明具体功能）
- 隐含假设过多的输入（用户假设某些条件但未明确说明）
- Loop 命令的提示词优化阶段（初始化后、深度研究前）

</scope>

<core_principles>

## 提示词工程最佳实践（基于 Anthropic 官方指南 2025）

### 1. 明确性原则（Clarity）

使用具体动词而非模糊动词：
- ✅ 好："实现 JWT 认证，包括 token 生成和验证"
- ❌ 差："处理认证"

提供精确的术语：
- ✅ 好："优化 API 响应时间，将平均延迟从 500ms 降到 200ms"
- ❌ 差："让 API 更快"

避免歧义表述：
- ✅ 好："添加用户登录功能（邮箱+密码）"
- ❌ 差："添加登录"（未说明登录方式）

### 2. 上下文原则（Context）

提供充分的背景信息：
- ✅ 好："在现有的 Express.js API（v4.18）中添加认证中间件"
- ❌ 差："添加认证"

说明当前状态：
- ✅ 好："当前使用 session 认证，需要迁移到 JWT"
- ❌ 差："改用 JWT"

包含技术栈信息：
- ✅ 好："技术栈：Node.js 18 + TypeScript + PostgreSQL + Redis"
- ❌ 差：完全不提技术栈

### 3. 范围边界原则（Scope）

明确包含的功能：
- ✅ 好："包含：邮箱登录、密码重置、remember me"
- ❌ 差：只说"实现登录"

明确不包含的功能：
- ✅ 好："不包含：社交登录、双因素认证、生物识别"
- ❌ 差：边界不清，可能导致范围蔓延

定义影响范围：
- ✅ 好："仅修改 auth 模块，不影响其他业务逻辑"
- ❌ 差：未说明影响范围

### 4. 可量化验收标准（Quantifiable Acceptance Criteria）

性能指标：
- ✅ 好："单元测试覆盖率≥90%，响应时间<200ms，并发支持 1000 req/s"
- ❌ 差："代码质量要好，性能要快"

质量标准：
- ✅ 好："使用 bcrypt 加密（salt rounds=10），密码长度 8-128 字符"
- ❌ 差："密码要安全"

业务指标：
- ✅ 好："支持 10 万用户，token 有效期 24 小时，refresh token 7 天"
- ❌ 差："能支持很多用户"

### 5. 结构化输出要求（Structured Output）

指定输出格式：
- ✅ 好："返回 JSON 格式，包含 {token, user, expiresAt}"
- ❌ 差："返回登录信息"

提供模板或示例：
- ✅ 好："错误响应：{\"error\": \"INVALID_CREDENTIALS\", \"message\": \"...\", \"code\": 401}"
- ❌ 差："返回错误"

明确数据结构：
- ✅ 好："user 对象包含 id, email, role, createdAt"
- ❌ 差："返回用户信息"

### 6. 错误处理明确（Error Handling）

列举错误场景：
- ✅ 好："密码错误返回 401，账号锁定返回 403，服务器错误返回 500"
- ❌ 差："处理错误情况"

指定错误码：
- ✅ 好："错误码：INVALID_CREDENTIALS, ACCOUNT_LOCKED, TOKEN_EXPIRED"
- ❌ 差：没有错误码规范

定义降级策略：
- ✅ 好："Redis 不可用时降级到 session，记录警告日志"
- ❌ 差：未考虑降级

## 5W1H 评估框架

提示词必须覆盖以下 6 个维度：

### What（目标）- 最关键
- 要实现什么功能？
- 预期交付成果是什么？
- 成功的标准是什么？

### Why（动机）- 理解背景
- 为什么需要这个功能？
- 解决什么业务问题？
- 带来什么价值？

### Who（受众）- 质量标准
- 目标用户是谁？
- 谁会使用这个功能？
- 对用户体验有什么要求？

### When（时间）- 优先级
- 什么时候需要完成？
- 优先级如何（高/中/低）？
- 是否有里程碑节点？

### Where（范围）- 定义边界
- 影响哪些模块/文件/系统？
- 部署在哪个环境？
- 与哪些组件交互？

### How（方式）- 技术偏好
- 技术方案偏好（如有）？
- 技术栈和工具？
- 架构模式或设计模式？

## 质量评分标准

详见 [best-practices.md](./best-practices.md#质量评分标准)，包括：
- 清晰度（Clarity）0-10 分
- 完整性（Completeness）0-10 分
- 可执行性（Actionability）0-10 分
- 综合得分计算方法

</core_principles>

<!-- /STATIC_CONTENT -->

<!-- DYNAMIC_CONTENT -->

<invocation>

## 调用方式

```python
optimizer_result = Agent(
    agent="task:prompt-optimizer",
    prompt=f"""优化用户提示词：

原始提示：{user_input}

要求：
1. 评估质量（清晰度、完整性、可执行性）
2. 如果得分 < 6，搜索最新最佳实践
3. 通过 5W1H 框架提问收集缺失信息
4. 生成优化后的结构化提示词
5. 如果得分 ≥ 8，返回 status="no_optimization_needed"
"""
)

# 处理结果
if optimizer_result["status"] == "no_optimization_needed":
    # 高质量输入，静默跳过
    optimized_prompt = optimizer_result["original_prompt"]
elif optimizer_result["status"] == "optimized":
    # 已优化，使用优化后的提示词
    optimized_prompt = optimizer_result["optimized_prompt"]
    print(f"优化报告：{optimizer_result['report']}")
```

## 优化模板结构

Agent 生成的优化提示词遵循以下标准模板：

```markdown
# 任务目标
[清晰的目标描述，使用具体动词]

## 背景和动机
[为什么需要这个任务，业务价值是什么]

## 技术上下文
- 项目类型：[类型]
- 技术栈：[栈]
- 当前状态：[状态]
- 依赖项：[依赖]

## 具体要求
1. [要求 1]
2. [要求 2]

## 范围边界
包含：[包含项列表]
不包含：[不包含项列表]

## 验收标准
1. [可量化标准 1]
2. [可量化标准 2]

## 时间和优先级
- 优先级：[高/中/低]
- 期望完成时间：[时间]
```

</invocation>

<output_format>

## 标准输出（需要优化）

```json
{
  "status": "optimized",
  "quality_score": {
    "clarity": 8,
    "completeness": 9,
    "actionability": 9,
    "overall": 8.7
  },
  "original_prompt": "实现用户认证",
  "optimized_prompt": "# 任务目标\n实现基于 JWT 的用户认证系统...",
  "improvements": [
    "添加了技术方案（JWT）",
    "明确了验收标准（测试覆盖率≥90%、响应时间<200ms）",
    "定义了范围边界（不包含社交登录）"
  ],
  "questions_asked": 3,
  "web_searches": 1,
  "report": "优化完成：原始质量 4.3 分 → 优化后 8.7 分。通过 3 次提问澄清了技术方案、验收标准和范围边界。"
}
```

## 无需优化（质量≥8 分）

```json
{
  "status": "no_optimization_needed",
  "quality_score": {
    "clarity": 10,
    "completeness": 9,
    "actionability": 10,
    "overall": 9.7
  },
  "original_prompt": "实现基于 JWT 的用户认证系统，包括登录、注册、token 刷新。技术栈：Node.js + Express + PostgreSQL。验收标准：测试覆盖率≥90%，响应时间<200ms。",
  "optimized_prompt": "实现基于 JWT 的用户认证系统，包括登录、注册、token 刷新。技术栈：Node.js + Express + PostgreSQL。验收标准：测试覆盖率≥90%，响应时间<200ms。",
  "improvements": [],
  "questions_asked": 0,
  "web_searches": 0,
  "report": "提示词质量优秀（9.7 分），无需优化。"
}
```

</output_format>

<references>

- Anthropic Prompt Engineering Guide (2025)
- [5W1H 框架](https://en.wikipedia.org/wiki/Five_Ws)
- [提示词工程最佳实践](https://www.promptingguide.ai/)
- [Claude 最新模型提示词技巧](/docs/zh-CN/about-claude/models/whats-new-claude-4-6)

</references>

<!-- /DYNAMIC_CONTENT -->
