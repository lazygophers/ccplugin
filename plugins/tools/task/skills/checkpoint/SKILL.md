---
description: 检查点管理 - 保存/恢复/清理任务执行状态，支持中断恢复
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Skills(task:checkpoint) - 检查点管理

为MindFlow Loop提供状态持久化，允许中断后恢复执行。阶段转换时自动保存检查点。

## 核心API

### save_checkpoint()

**时机**：计划设计/确认/执行/验证/调整完成后

**参数**：`(user_task, iteration, phase, context, plan_md_path?, additional_state?)`

**逻辑**：生成task_hash(MD5[:12]) → 写入`.claude/checkpoints/{hash}.json` → 含user_task/iteration/phase/context/timestamp/additional_state

### load_checkpoint()

**时机**：Loop初始化

**参数**：`(user_task)` → 返回dict或None

**逻辑**：匹配task_hash → 验证必需字段(user_task/iteration/phase/context/timestamp) → 时效检查(>24h过期) → 询问用户恢复/重新开始

### cleanup_checkpoint()

**时机**：任务完成/用户选择重新开始

**参数**：`(user_task)` → 返回bool

**逻辑**：删除对应检查点文件

## 注意事项

- 文件位置：`.claude/checkpoints/{task_hash}.json`
- 哈希：MD5(user_task)[:12]
- 时效：>24h过期
- 恢复前必须询问用户
- 单任务同时只有一个检查点
- 检查点包含完整上下文确保恢复连续

## 相关文档

[集成与示例](./integration-examples.md) | [状态序列化](./state-serializer.md)

<!-- /STATIC_CONTENT -->
