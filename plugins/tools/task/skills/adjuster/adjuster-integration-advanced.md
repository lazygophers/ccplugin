# Adjuster 高级集成

## 自定义场景

- **单次失败**：传入task_id+error → Retry策略
- **批量失败**：传入failed_tasks JSON → 识别共同模式 → 统一或独立修复
- **条件调整**：传入task+conditions → 根据条件选择策略

## 停滞检测

检测最近3次错误签名(`{type, message, task_id}`)的相似度：
- 不同type → 0.0
- 不同task_id → 0.5
- 相同message → 1.0
- 部分匹配 → 0.7

所有相似度≥0.9 → 停滞

## 指数退避

公式：`2^(failure_count-1)`秒，上限60秒。`backoff_seconds>0`时等待。

## 错误处理

- **无效策略**：检查strategy∈{retry,debug,replan,ask_user}，否则抛异常
- **超过重试**：`current_retry>=max_retries(默认3)` → 返回True
