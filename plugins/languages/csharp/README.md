# C# 开发插件

> C# 开发插件提供高质量的 C# 代码开发指导和 LSP 支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin csharp@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install csharp@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **C# 开发专家代理** - 提供专业的 C# 开发支持
  - 高质量代码实现
  - 架构设计指导
  - 性能优化建议
  - 异步编程支持

- **开发规范指导** - 完整的 C# 开发规范
  - **C# 14/.NET 10** - 使用最新 C# 特性
  - **LINQ 和函数式编程** - 数据处理最佳实践
  - **async/await** - 异步编程模式

- **代码智能支持** - 通过 C# LSP 提供
  - 实时代码诊断
  - 代码补全和导航
  - 格式化和重构建议

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `dev` | C# 开发专家 |
| Agent | `test` | 测试专家 |
| Agent | `debug` | 调试专家 |
| Agent | `perf` | 性能优化专家 |
| Skill | `core` | C# 核心规范 |
| Skill | `async` | 异步编程规范 |
| Skill | `linq` | LINQ 规范 |
| Skill | `testing` | 测试规范 |

## 前置条件

### .NET SDK 安装

```bash
# macOS
brew install dotnet@8

# 验证安装
dotnet --version
```

## 核心规范

### 必须遵守

1. **使用 C# 12 特性** - 主构造函数、集合表达式
2. **启用 Nullable** - 启用 nullable reference types
3. **异步最佳实践** - 使用 async/await，避免 .Result
4. **LINQ 优先** - 优先使用 LINQ 处理数据
5. **依赖注入** - 使用 DI 容器管理依赖

### 禁止行为

- 使用 .Result 或 .Wait()
- 忽略 nullable 警告
- 使用魔术字符串
- 过度使用反射

## 最佳实践

### 异步编程

```csharp
// ✅ 好的异步代码
public async Task<User> GetUserAsync(int id)
{
    return await _dbContext.Users.FindAsync(id);
}

// ❌ 不好的异步代码
public User GetUser(int id)
{
    return _dbContext.Users.FindAsync(id).Result;
}
```

### LINQ

```csharp
// ✅ 使用 LINQ
var activeUsers = users
    .Where(u => u.IsActive)
    .OrderBy(u => u.Name)
    .Select(u => u.Name);

// ❌ 使用循环
var activeUsers = new List<string>();
foreach (var u in users)
{
    if (u.IsActive)
        activeUsers.Add(u.Name);
}
activeUsers.Sort();
```

## 参考资源

- [.NET 文档](https://docs.microsoft.com/dotnet/)
- [C# 编程指南](https://docs.microsoft.com/dotnet/csharp/programming-guide/)

## 许可证

AGPL-3.0-or-later
