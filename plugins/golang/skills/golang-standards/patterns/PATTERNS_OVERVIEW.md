# Golang 标准规范 - 设计模式概述

本目录包含 Golang 官方标准规范和最佳实践。

## 已创建的模式文档

### ✅ 已完成

- **error-handling.md** - 错误处理规范
- **function-design.md** - 函数设计规范
- **package-organization.md** - 分库分包规范
- **architecture-design.md** - 架构设计规范
- **naming-conventions.md** - 命名规范

## 模式之间的关系

```
命名规范（基础）
    ↓
分库分包规范（组织）
    ↓
函数设计规范（实现）
    ↓
架构设计规范（全局）
    ↓
错误处理规范（横切）
```

## 官方标准参考

本规范基于以下官方指导文档：

- **Effective Go** - Go 官方风格指南
- **Go Code Review Comments** - Go 代码审查意见
- **Standard Go Project Layout** - 标准项目布局

## 核心原则

1. **代码风格** - 遵循官方 Effective Go 指南
2. **错误处理** - 显式处理，不允许忽略
3. **接口设计** - 小而专一，不超过 3 个方法
4. **项目结构** - 清晰分层，降低耦合度
5. **注释规范** - 公开符号必须有注释

## 参考文档

- [错误处理规范](./error-handling.md)
- [函数设计规范](./function-design.md)
- [分库分包规范](./package-organization.md)
- [架构设计规范](./architecture-design.md)
- [命名规范](./naming-conventions.md)
- [参考资源](../references.md)

## 更新时间

最后更新于 2026-01-09
