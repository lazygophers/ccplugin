# C++ 开发插件

C++ 开发插件提供高质量的 C++ 代码开发指导和 LSP 支持。包括现代 C++17/23 特性、STL、内存管理、模板元编程和并发编程规范。

## 功能特性

### 核心功能

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

## 安装

### 前置条件

1. **clangd 安装**

```bash
# macOS
brew install llvm

# Linux (Ubuntu/Debian)
apt install clangd

# 验证安装
which clangd
clangd --version
```

2. **Claude Code 版本**
   - 需要支持 LSP 的 Claude Code 版本（v2.0.74+）

### 安装插件

```bash
# 方式 1: 使用本地路径安装
claude code plugin install /path/to/plugins/languages/cpp

# 方式 2: 复制到插件目录
cp -r /path/to/plugins/languages/cpp ~/.claude/plugins/
```

## 使用指南

### C++ 标准支持

插件支持以下 C++ 标准：

| 标准 | 关键特性 | 状态 |
|------|---------|------|
| C++17 | 结构化绑定、std::optional、std::variant、if constexpr | 完全支持 |
| C++20 | Concepts、Ranges、协程、三向比较、std::format | 完全支持 |
| C++23 | std::expected、std::print、Deducing this | 部分支持 |

### 开发代理

插件提供 4 个专业代理：

1. **dev** - C++ 开发专家
   - 代码实现与架构设计
   - 现代 C++ 特性应用
   - 模板编程指导

2. **test** - C++ 测试专家
   - 单元测试编写
   - Catch2/gtest 使用
   - 测试覆盖率优化

3. **debug** - C++ 调试专家
   - 内存问题诊断
   - 未定义行为检测
   - GDB/LLDB 使用

4. **perf** - C++ 性能优化专家
   - 性能瓶颈分析
   - 零开销优化
   - 并发优化

### LSP 代码智能

插件自动配置 clangd LSP 支持：

- 实时代码诊断
- 代码补全和导航
- 快速信息（悬停查看定义）
- 重构建议
- 格式化支持

## 项目结构

```
cpp/
├── .claude-plugin/
│   └── plugin.json                      # 插件清单
├── .lsp.json                            # LSP 配置（clangd）
├── agents/
│   ├── dev.md                           # 开发专家代理
│   ├── test.md                          # 测试专家代理
│   ├── debug.md                         # 调试专家代理
│   └── perf.md                          # 性能优化代理
├── skills/cpp-skills/
│   ├── SKILL.md                         # 核心规范入口
│   ├── development-practices.md         # RAII、智能指针、STL
│   ├── architecture-tooling.md          # 架构和工具链
│   ├── coding-standards/                # 编码规范
│   │   ├── naming.md                    # 命名规范
│   │   ├── formatting.md                # 格式规范
│   │   ├── documentation.md             # 文档规范
│   │   ├── error-handling.md            # 错误处理
│   │   ├── concurrency.md               # 并发规范
│   │   ├── performance.md               # 性能规范
│   │   ├── security.md                  # 安全编码
│   │   └── maintainability.md           # 可维护性
│   ├── specialized/                     # 高级主题
│   │   ├── template-programming.md      # 模板元编程
│   │   ├── memory-management.md         # 内存管理
│   │   ├── concurrency.md               # 并发编程
│   │   └── performance.md               # 性能优化
│   ├── examples/                        # 代码示例
│   │   ├── raii_smart_pointers.cpp
│   │   ├── modern_features.cpp
│   │   ├── stl_containers_algorithms.cpp
│   │   └── template_metaprogramming.cpp
│   └── references.md                    # 参考资料
├── hooks/hooks.json                     # Hook 配置
├── scripts/
│   ├── main.py                          # CLI 入口
│   └── hooks.py                         # Hook 处理
└── README.md                            # 本文档
```

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
- 使用 varargs
- 忽略异常安全
- 使用宏（用 constexpr/inline）

## 工作流程

### 典型开发流程

```bash
# 1. 创建 CMake 项目
mkdir myproject && cd myproject
cmake_minimum_required(VERSION 3.20)
project(MyProject LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 23)

# 2. 编写代码
# 使用现代 C++ 特性、智能指针、STL

# 3. 编写测试
# 使用 Catch2 或 gtest

# 4. 静态分析
clang-tidy src/*.cpp
cppcheck --enable=all src/

# 5. 性能分析
perf record ./app
perf report

# 6. LSP 支持
# 编辑器自动提供代码智能
```

## 最佳实践

### 现代 C++ 特性

```cpp
// 结构化绑定
auto [key, value] = map.extract(it);

// if constexpr
template<typename T>
auto get_value(T t) {
    if constexpr(std::is_pointer_v<T>)
        return *t;
    else
        return t;
}

// Ranges
std::ranges::sort(data);
std::ranges::find_if(data, predicate);
```

### 智能指针

```cpp
// unique_ptr - 独占所有权
auto ptr = std::make_unique<MyClass>();

// shared_ptr - 共享所有权
auto shared = std::make_shared<MyClass>();

// weak_ptr - 弱引用（避免循环）
std::weak_ptr<MyClass> weak = shared;
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

### 官方文档

- [cppreference.com](https://en.cppreference.com/w/) - C++ 参考
- [C++ Reference (中文)](https://zh.cppreference.com/) - 中文参考
- [C++ 标准提案](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/)

### 推荐图书

- C++ Primer - Stanley Lippman
- Effective C++ - Scott Meyers
- Effective Modern C++ - Scott Meyers
- C++ Concurrency in Action - Anthony Williams

## 许可证

AGPL-3.0-or-later

---

**作者**：lazygophers
**版本**：1.0.0
**最后更新**：2026-02-09
