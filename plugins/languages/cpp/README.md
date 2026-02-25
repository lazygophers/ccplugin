# C++ 开发插件

> C++ 开发插件提供高质量的 C++ 代码开发指导和 LSP 支持

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin cpp@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install cpp@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **C++ 开发专家代理** - 提供专业的 C++ 开发支持
  - 高质量代码实现
  - 架构设计指导
  - 性能优化建议
  - 模板元编程支持

- **开发规范指导** - 完整的现代 C++ 开发规范
  - C++17/20/23 标准特性
  - RAII 和智能指针
  - STL 容器和算法
  - 并发编程模式

- **代码智能支持** - 通过 clangd LSP 提供
  - 实时代码诊断
  - 代码补全和导航
  - 格式化和重构建议
  - 类型检查和错误报告

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Agent | `dev` | C++ 开发专家 |
| Agent | `test` | 测试专家 |
| Agent | `debug` | 调试专家 |
| Agent | `perf` | 性能优化专家 |
| Skill | `core` | C++ 核心规范 |
| Skill | `memory` | 内存管理规范 |
| Skill | `concurrency` | 并发编程规范 |
| Skill | `performance` | 性能优化规范 |
| Skill | `template` | 模板编程规范 |
| Skill | `tooling` | 工具链规范 |

## 前置条件

### clangd 安装

```bash
# macOS
brew install llvm

# Linux (Ubuntu/Debian)
apt install clangd

# 验证安装
which clangd
clangd --version
```

## C++ 标准支持

| 标准 | 关键特性 | 状态 |
|------|---------|------|
| C++17 | 结构化绑定、std::optional、std::variant | 完全支持 |
| C++20 | Concepts、Ranges、协程 | 完全支持 |
| C++23 | std::expected、std::print | 部分支持 |

## 核心规范

### 必须遵守

1. **现代优先** - 优先使用 C++17/23 特性
2. **RAII 原则** - 资源获取即初始化
3. **智能指针** - 使用 std::unique_ptr/std::shared_ptr
4. **STL 优先** - 优先使用标准库
5. **类型安全** - 使用 auto、模板、概念
6. **异常安全** - 提供强异常安全保证
7. **零开销** - 抽象不应带来运行时开销

### 禁止行为

- 使用 C 风格类型转换
- 使用 malloc/free
- 使用裸指针管理资源
- 使用 C 风格数组
- 忽略异常安全

## 最佳实践

### 智能指针

```cpp
// unique_ptr - 独占所有权
auto ptr = std::make_unique<MyClass>();

// shared_ptr - 共享所有权
auto shared = std::make_shared<MyClass>();
```

### STL 算法

```cpp
// 排序
std::ranges::sort(data);

// 查找
auto it = std::ranges::find(data, value);

// 变换
std::ranges::transform(data, output, [](int x) { return x * 2; });
```

## 参考资源

- [cppreference.com](https://en.cppreference.com/w/) - C++ 参考
- [C++ 标准提案](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/)

## 许可证

AGPL-3.0-or-later
