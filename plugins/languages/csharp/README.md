# C# 开发插件

C# 开发插件提供高质量的 C# 代码开发指导和 LSP 支持。包括现代 C# 12/.NET 8 特性、LINQ、async/await 和主流框架开发规范。

## 功能特性

### 核心功能

- **C# 开发专家代理** - 提供专业的 C# 开发支持
  - 高质量代码实现
  - 架构设计指导
  - 性能优化建议
  - 框架开发支持

- **开发规范指导** - 完整的现代 C# 开发规范
  - C# 12 新特性
  - LINQ 和异步编程
  - ASP.NET Core、WPF、MAUI、Blazor

- **代码智能支持** - 通过 OmniSharp LSP 提供
  - 实时代码诊断
  - 代码补全和导航
  - 格式化和重构建议

## 安装

### 前置条件

1. **.NET SDK 安装**

```bash
# macOS
brew install --cask dotnet-sdk

# Linux (Ubuntu)
wget https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install -y dotnet-sdk-8.0

# 验证安装
dotnet --version
```

2. **OmniSharp 安装**

```bash
# 通过 NuGet 安装
dotnet tool install --global OmniSharp

# 或使用 VS Code 扩展
code --install-extension ms-dotnettools.csharp
```

### 安装插件

```bash
# 方式 1: 使用本地路径安装
claude code plugin install /path/to/plugins/languages/csharp

# 方式 2: 复制到插件目录
cp -r /path/to/plugins/languages/csharp ~/.claude/plugins/
```

## 项目结构

```
csharp/
├── .claude-plugin/
│   └── plugin.json                      # 插件清单
├── .lsp.json                            # LSP 配置（OmniSharp）
├── agents/
│   ├── dev.md                           # 开发专家代理
│   ├── test.md                          # 测试专家代理
│   ├── debug.md                         # 调试专家代理
│   └── perf.md                          # 性能优化代理
├── skills/csharp-skills/
│   ├── SKILL.md                         # 核心规范入口
│   ├── development-practices.md         # LINQ、async/await、DI
│   ├── framework-development.md          # 框架开发
│   ├── specialized/                     # 高级主题
│   │   ├── async-programming.md         # 异步编程进阶
│   │   ├── linq.md                       # LINQ 高级用法
│   │   ├── wpf-development.md           # WPF 开发
│   │   └── aspnet-development.md        # ASP.NET Core
│   └── references.md                    # 参考资料
├── hooks/hooks.json                     # Hook 配置
├── scripts/
│   ├── main.py                          # CLI 入口
│   └── hooks.py                         # Hook 处理
└── README.md                            # 本文档
```

## 核心规范

### 必须遵守

1. **现代优先** - 优先使用 C# 12 特性
2. **异步优先** - IO 操作使用 async/await
3. **空安全** - 启用可空引用类型
4. **LINQ 优先** - 使用 LINQ 进行数据操作
5. **依赖注入** - 使用 DI 容器

### 禁止行为

- 使用 .Result 或 .Wait()
- 不传递 CancellationToken
- 禁用可空引用类型
- 使用 async void（除事件处理）
- LINQ 查询中的副作用

## 参考资源

### 官方文档

- [.NET 文档](https://learn.microsoft.com/dotnet/)
- [C# 指南](https://learn.microsoft.com/dotnet/csharp/)
- [ASP.NET Core](https://learn.microsoft.com/aspnet/core/)

## 许可证

AGPL-3.0-or-later

---

**作者**：lazygophers
**版本**：1.0.0
**最后更新**：2026-02-09
