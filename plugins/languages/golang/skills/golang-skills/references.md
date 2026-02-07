# Golang 风格 - 参考资源

本文档包含与 golang-skills 规范相关的外部参考资源和实现示例。

## golang-skills 官方资源

### 核心库

- **[lazygophers/utils](https://github.com/lazygophers/utils)** - 综合工具库
    - `candy` - 函数式编程（Map/Filter/Each/Reverse/Unique/Sort）
    - `stringx` - 字符串转换（CamelCase/SnakeCase）
    - `osx` - 文件操作（IsFile/IsDir/Stat）
    - `json` - JSON 处理
    - `cryptox` - 加密/哈希
    - `xtime` - 时间处理
    - `defaults` - 默认值处理
    - `pterm` - 终端输出美化

- **[lazygophers/log](https://github.com/lazygophers/log)** - 高性能日志库
    - 支持多种日志级别（Info/Warn/Error/Fatal）
    - 高效的日志输出
    - 缓冲优化

- **[lazygophers/lrpc - 数据库](https://github.com/lazygophers/lrpc/tree/master/middleware/storage/db)** - 数据库访问
    - 类型安全的数据库操作
    - 支持泛型
    - 链式查询

- **[lazygophers/lrpc - 缓存](https://github.com/lazygophers/lrpc/tree/master/middleware/storage/cache)** - 缓存管理
    - 高性能缓存
    - 支持多种缓存后端
    - 缓存过期策略

- **[lazygophers/lrpc - i18n](https://github.com/lazygophers/lrpc/tree/master/middleware/i18n)** - 国际化
    - 多语言支持
    - 翻译管理
    - 格式化输出

- **[lazygophers/lrpc - error](https://github.com/lazygophers/lrpc/tree/master/middleware/xerror)** - 错误处理
    - 统一错误码
    - 错误包装
    - 错误日志

## 工具和框架

### golang-skills 生态中常用的库

- **Web Framework**：Fiber（轻量级、高性能）
- **Database**：lazygophers/lrpc（类型安全、支持泛型）
- **Logging**：lazygophers/log（高性能、统一格式）
- **Utilities**：lazygophers/utils（多功能工具库）

### 补充库

- **Testing**：[testify](https://github.com/stretchr/testify) - 断言和 mock
- **Errors**：[errors](https://golang.org/pkg/errors/) - Go 1.13+ 错误处理
- **Context**：[context](https://golang.org/pkg/context/) - 上下文管理

## 性能优化参考

- **[High Performance Go](https://dave.cheney.net/high-performance-go-survey/2019-02)** - 性能优化调查
- **[Optimization in Go](https://go.dev/blog/pprof)** - 优化技巧
- **[Memory Optimization](https://golang.org/doc/diagnostics)** - 内存优化

## 设计模式

- **[Functional Options Pattern](https://dave.cheney.net/2014/10/17/functional-options-for-friendly-apis)** - Go 推荐的选项模式
- **[Design Patterns in Go](https://refactoring.guru/design-patterns/go)** - 设计模式实现
