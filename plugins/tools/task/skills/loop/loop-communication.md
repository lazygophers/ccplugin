# Loop 通信和协作

本文档是 Loop 通信和协作的索引，详细内容已拆分为以下文件：

## 文件结构

### 基础通信
- **文件**: [loop-communication-basics.md](loop-communication-basics.md)
- **内容**:
  - Agent 通信规则（严格禁止、正确方式）
  - 消息格式（Agent 发送、Team Leader 处理、Agent 接收）
  - 消息类型（Question、Response、Report、Alert、Request）
  - 协作模式（顺序协作、并行协作、反馈循环）

### 最佳实践
- **文件**: [loop-communication-practices.md](loop-communication-practices.md)
- **内容**:
  - 清晰的消息边界
  - 超时处理
  - 错误传播
  - 状态同步
  - 消息优先级
  - 重试机制
  - 消息批处理

### 通信安全
- **文件**: [loop-communication-security.md](loop-communication-security.md)
- **内容**:
  - 消息验证
  - 防止消息循环
  - 消息加密
  - 访问控制
  - 审计日志

## 快速导航

- 如果你需要了解基本通信规则 → 查看 [基础通信](loop-communication-basics.md)
- 如果你需要最佳实践指导 → 查看 [最佳实践](loop-communication-practices.md)
- 如果你需要安全相关内容 → 查看 [通信安全](loop-communication-security.md)
