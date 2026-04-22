---
description: 失败调整。验收未通过时触发，分析失败根因并分类，通过交互让用户选择调整策略（补充上下文/重新对齐/重新规划/放弃）
memory: project
color: yellow
model: sonnet
permissionMode: bypassPermissions
background: false
user-invocable: false
effort: high
context: fork
agent: task:adjust
---

# Adjust Skill

分析校验失败原因，制定修正策略。**1 次交互确认调整方向，所有修复遵循项目现有风格。**

**停滞检测**：相同错误出现 3 次或 A→B→A→B 振荡 → 立即 AskUserQuestion。

## 执行流程

### 步骤 1：读取校验结果和上下文

从 flow 传入的 verify_result 中获取失败标准列表。读取 align.json 获取锁定风格和验收标准，读取 context.json 获取项目上下文。如果 task.json 存在，读取现有执行计划。

### 步骤 2：分析失败根因

对 verify_result 中每条 failed_criteria 分析根本原因：
- 是测试未通过？是 lint 错误？是修改了计划外文件？
- 是引用了不存在的函数？是接口不匹配？

### 步骤 3：分类失败类型

将根因归入以下类型之一：

| 类型 | 特征 | 可自动修复 | 策略 |
|------|------|-----------|------|
| test-failure | 测试未通过、断言失败 | ✅（≤2次） | 重新执行失败子任务 |
| style-violation | lint 错误、命名不一致 | ✅（≤2次） | 运行格式化工具后重验 |
| scope-creep | 修改了计划外文件 | ❌ | 需求偏差 → align |
| missing-context | 引用不存在的函数/模块 | ❌ | 上下文缺失 → explore |
| integration-issue | 接口不匹配、类型不兼容 | ❌ | 重新计划 → plan |

预定义策略详见 [strategies.json](strategies.json)。

### 步骤 4：自动修复判定

如果失败类型为 test-failure 或 style-violation，且自动修复次数 < 2，且不涉及安全/完整性问题 → 自动返回"重新计划"，不问用户。

自动修复上限 2 次。超过后必须进入步骤 5。

### 步骤 5：向用户展示分析并请求策略（必须执行）

通过 AskUserQuestion 一次性展示：
- 失败分析结果（根因、类型、涉及的标准）
- 已尝试的自动修复次数（如有）

提供以下选项：
- **补充上下文**：对项目理解不足，返回 explore
- **重新对齐**：需求理解有偏差，返回 align
- **重新规划**：执行计划有问题，返回 plan
- **重新分析**：分析有误，重新审视失败原因 → 回到步骤 2
- **放弃任务**：无法完成，停止执行

### 步骤 6：返回调整结果

将用户选择映射为 status 返回给 flow：

| 用户选择 | 返回 status |
|---------|------------|
| 补充上下文 | 上下文缺失 |
| 重新对齐 | 需求偏差 |
| 重新规划 | 重新计划 |
| 放弃任务 | 放弃 |

返回 `status` + `reason`（失败原因）。

## 检查清单

- [ ] 根本原因已分析
- [ ] 失败类型已分类
- [ ] 自动修复已判定（≤2 次上限）
- [ ] AskUserQuestion 已执行（自动修复超限或不可自动修复时）
- [ ] 所有修复遵循项目现有风格
- [ ] status 和 reason 已返回
