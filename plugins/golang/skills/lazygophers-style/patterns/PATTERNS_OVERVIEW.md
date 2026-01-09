# Lazygophers 设计模式概述

本目录包含 lazygophers 生态的设计模式和最佳实践。

## 已创建的模式文档

### ✅ 已完成

- **error-handling.md** - 错误处理规范（参考 Linky Server 模式）
- **function-design.md** - 函数设计规范（零分配、函数式、查询构建器）
- **package-organization.md** - 分库分包规范（全局状态模式、避免显式 interface）
- **architecture-design.md** - 架构设计规范（全局状态模式、三层架构）
- **naming-conventions.md** - 命名规范（导出/私有、ID 字段、函数命名）

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

## Linky Server 参考

Linky 服务器实现了完整的 lazygophers 风格 Go 项目：

- **启动流程**：state.Init() → Service Preparation → API Run
- **三层架构**：API (fiber handlers) → Impl (业务逻辑) → State (全局状态)
- **全局状态模式**：所有有状态资源在 state 包中（config、database、cache 等）
- **中间件组织**：单独的 middleware 包（handler.go、logger.go、auth.go、error.go）
- **函数式编程**：99% 代码都是纯函数，无复杂对象方法
- **错误处理**：统一日志 + 多行处理 + 无错误包装

## Ice Cream Heaven 参考

Ice Cream Heaven 生态包含 14+ Go 项目，提供了完整的项目示例：

- **统一错误系统**：错误码 -1/0/1000+
- **泛型模型**：使用泛型实现类型安全的 GORM 操作
- **链式 API**：SetXxx().ApplyConfig() 的流畅接口
- **Goroutine 安全**：routine.GoWithRecover() 的安全并发
- **装饰器模式**：灵活的功能组合

## 最佳实践总结

### 强制规范

1. **必须使用 lazygophers 包库**：
   - candy（集合操作）
   - stringx（字符串转换）
   - osx（文件操作）
   - log（日志）

2. **强制的错误处理**：
   - 多行处理 + 日志
   - 不包装错误（返回原始）
   - 使用 errors.Is/As 判断

3. **全局状态模式**：
   - 所有有状态资源在 internal/state/
   - 无显式 Repository interface
   - Service 层直接使用全局状态

4. **函数式编程**：
   - 优先使用 candy.Map/Filter/Each
   - 查询构建器模式
   - 99% 代码都是纯函数

5. **中间件组织**：
   - 单独的 internal/middleware/ 包
   - handler.go 实现 ToHandler 适配器
   - logger、auth、error 等在同包中

### 目录结构规范

```
internal/
├── state/                  # 全局状态（config、database、cache 等）
├── impl/                   # Service 实现（业务逻辑）
├── api/                    # API 路由
├── middleware/             # 中间件（handler、logger、auth、error）
└── model/                  # 数据模型
```

**禁止**：
- ❌ service/ 目录
- ❌ config/ 目录
- ❌ model/ 目录（在 state 中）
- ❌ test/ 目录
- ❌ cmd/ 子目录

## 参考文档

- [错误处理规范](./error-handling.md)
- [函数设计规范](./function-design.md)
- [分库分包规范](./package-organization.md)
- [架构设计规范](./architecture-design.md)
- [命名规范](./naming-conventions.md)
- [Linky Server 参考](../references.md)

## 更新时间

最后更新于 2026-01-09
