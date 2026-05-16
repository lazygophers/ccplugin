# 命名规范插件

> 命名规范插件提供跨编程语言的统一命名规范指南

## 安装

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin naming@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install naming@ccplugin-market
```

## 功能特性

### 🎯 核心功能

- **命名规范指导** - 提供专业的命名建议
  - 变量命名
  - 函数命名
  - 类/接口命名
  - 文件命名

- **多语言支持** - 覆盖主流编程语言
  - Python (PEP 8)
  - JavaScript/TypeScript (camelCase)
  - Java (camelCase/PascalCase)
  - Go (MixedCaps)
  - Rust (snake_case)
  - C/C++ (snake_case)

### 📦 包含组件

| 组件类型 | 名称 | 描述 |
|---------|------|------|
| Skill | `core` | 命名核心规范（覆盖 Python/JavaScript/Java/Go/Rust/C/C++ 等主流语言） |

## 命名规范速查

### Python

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | snake_case | `my_module.py` |
| 类 | PascalCase | `MyClass` |
| 函数 | snake_case | `my_function` |
| 变量 | snake_case | `my_variable` |
| 常量 | UPPER_SNAKE_CASE | `MY_CONSTANT` |

### JavaScript/TypeScript

| 类型 | 规范 | 示例 |
|------|------|------|
| 类/接口 | PascalCase | `MyClass` |
| 函数 | camelCase | `myFunction` |
| 变量 | camelCase | `myVariable` |
| 常量 | UPPER_SNAKE_CASE | `MY_CONSTANT` |
| 文件 | kebab-case | `my-file.ts` |

### Go

| 类型 | 规范 | 示例 |
|------|------|------|
| 包 | lowercase | `mypackage` |
| 导出 | PascalCase | `MyFunction` |
| 私有 | camelCase | `myFunction` |

## 命名原则

1. **描述性** - 名称应清晰表达意图
2. **一致性** - 项目内保持统一风格
3. **简洁性** - 避免过长名称
4. **避免缩写** - 除非是通用缩写（如 URL、ID）

## 参考资源

- [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [Google Style Guides](https://google.github.io/styleguide/)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)

## 许可证

AGPL-3.0-or-later
