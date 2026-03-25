---
description: HITL 审批技能 - 在关键决策点插入人工审批，实现风险分级审批策略，满足 EU AI Act 2026 合规要求
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (5200+ tokens) -->

# Skills(task:hitl) - HITL 审批规范

## 技能概述

Human-in-the-Loop (HITL) 审批技能负责在 task:loop 的关键决策点插入人工审批机制，确保高风险操作得到用户明确确认。基于 EU AI Act 2026 Article 14（Human Oversight）的要求，所有高风险 AI 系统必须有人工监督机制。

**核心能力**：
- 风险分级：基于操作类型、影响范围、可逆性等维度自动评估风险等级
- 三级审批：auto（自动通过）、review（需审查）、mandatory（强制审批）
- 审批追溯：完整记录所有审批决策，支持合规审计
- 超时保护：审批超时后按策略阻塞或拒绝，防止意外执行

**设计原则**：
1. **安全优先**：默认拒绝高风险操作，宁可阻塞也不误执行
2. **用户体验**：80%+ 操作自动通过（auto），不打断用户工作流
3. **可追溯性**：所有决策记录在案，符合合规要求

---

## 风险分级体系

详见 `risk-classifier.md`，核心分类：

| 级别 | 风险评分 | 审批行为 | 示例 |
|------|---------|---------|------|
| **auto** | 0-3 | 自动通过 | Read、Grep、go test |
| **review** | 4-6 | 需审查确认 | Edit、Write、npm install |
| **mandatory** | 7-10 | 强制审批 | rm -rf、git push --force |

风险评估维度：可逆性(40%)、影响范围(30%)、敏感性(20%)、外部影响(10%)

---

## API 接口

### 主接口：`hitl_approve_operation(operation, context, user_config)`

返回：`{"approved": bool, "risk_classification": {...}, "approval": {...}}`

详见 `approval-policies.md` 获取完整 API 规范和参数说明。

---

## 集成点（Loop 流程）

### 集成点 1: 计划确认
**位置**：`skills/loop/flows/plan.md` - 阶段 4
**时机**：planner 生成计划后，执行前
**审批**：展示风险评估摘要（auto/review/mandatory 操作分布）

### 集成点 2: 任务执行
**位置**：`skills/loop/detailed-flow.md` - 阶段 4
**时机**：每个任务执行前，逐个工具调用
**审批**：拦截 Edit、Write、Bash 等操作，根据风险等级决定是否需要用户确认

### 集成点 3: 危险操作拦截
**位置**：`skills/loop/detailed-flow.md` - 阶段 6
**时机**：adjuster 建议执行危险操作时
**审批**：自愈操作（删除文件、修改配置）需要用户明确确认

详见 `detailed-flow.md` 和 `flows/plan.md` 获取完整集成代码。

---

## 配置选项

详见 `approval-policies.md` 获取完整配置说明。

核心配置（`.claude/task.local.md`）：
- `enabled`: 启用/禁用 HITL 审批
- `trust_mode`: 信任模式（review → auto）
- `timeout`: 审批超时时间（review: 5分钟，mandatory: 10分钟）
- `overrides`: 风险等级覆盖规则

---

## 审批日志

日志存储：`.claude/plans/{task_hash}/approval-log.json`

包含：操作详情、风险分级、用户决策、执行结果、统计数据

---

## 合规性（EU AI Act）

符合 EU AI Act Article 14 要求：
- 高风险操作需人工监督
- 决策可追溯（审批日志）
- 时间戳记录
- 审计能力（支持导出 CSV）

---

## 使用示例

```python
# 文件修改（review 级别）
approval = hitl_approve_operation({"tool": "Edit", "files": ["src/api/auth.go"]})
if approval["approved"]:
    Edit(file="src/api/auth.go", ...)

# 破坏性操作（mandatory 级别）
approval = hitl_approve_operation({"tool": "Bash", "command": "rm -rf dist/"})
# 用户需输入确认文本或拒绝
```

---

## 验收标准

1. 风险操作（rm -rf、git force push）触发 mandatory 审批
2. 低风险操作（Read、Grep、测试）自动通过
3. 审批超时后按策略处理（阻塞/拒绝）
4. 审批记录追溯到 approval-log.json
5. 支持用户配置覆盖和信任模式
6. mandatory 级别要求输入确认文本
7. 符合 EU AI Act Article 14 要求

详见 `risk-classifier.md` 和 `approval-policies.md` 获取完整验收标准。

<!-- /STATIC_CONTENT -->
