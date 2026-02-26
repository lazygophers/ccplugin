# 插件开发支持的语言

> Claude Code 插件开发语言选择指南

## 目录

1. [概述](#概述)
2. [核心语言](#核心语言)
3. [脚本语言](#脚本语言)
4. [编程语言](#编程语言)
5. [语言选择指南](#语言选择指南)

## 概述

Claude Code 插件开发采用**多语言混合**模式：

```
插件开发语言架构：
┌─────────────────────────────────────────┐
│         Claude Code 插件系统            │
├─────────────────────────────────────────┤
│  配置层 (必需)                           │
│  - Markdown (commands/agents/skills)    │
│  - JSON (plugin.json, hooks.json)       │
├─────────────────────────────────────────┤
│  脚本层 (可选)                           │
│  - Shell / Bash                         │
│  - Python                               │
│  - Node.js                              │
├─────────────────────────────────────────┤
│  逻辑层 (可选)                           │
│  - 任意编译语言 (Go, Rust, C++)          │
│  - 任意解释语言 (Python, JS, Java)      │
└─────────────────────────────────────────┘
```

## 核心语言

### Markdown (.md)

**用途**：定义 commands、agents、skills

**必需性**：强制

**文件位置**：

```
plugin/
├── commands/
│   └── my-command.md      # 命令定义
├── agents/
│   └── my-agent.md        # 代理定义
└── skills/
    └── my-skill/
        └── SKILL.md       # 技能定义
```

**格式要求**：

- Frontmatter (YAML)
- Markdown 内容
- UTF-8 编码

**示例**：

```markdown
---
description: 命令描述
allowed-tools: Bash, Read
---

# 命令名称

命令详细说明。
```

### JSON (.json)

**用途**：配置文件

**必需性**：强制

**文件类型**：

| 文件 | 描述 |
|------|------|
| `plugin.json` | 插件清单 |
| `hooks.json` | 钩子配置 |
| `marketplace.json` | 市场清单 |
| `.mcp.json` | MCP 服务器配置 |
| `.lsp.json` | LSP 服务器配置 |

**示例**：

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "插件描述"
}
```

## 脚本语言

### Python

**推荐度**：⭐⭐⭐⭐⭐

**适用场景**：

- 复杂逻辑处理
- 数据处理和分析
- API 调用
- 文本分析
- MCP 服务器

**优点**：

- 语法简洁
- 生态丰富
- 跨平台
- 易于维护

**缺点**：

- 需要 Python 环境
- 启动较慢

**示例**：

```python
#!/usr/bin/env python3
"""插件主脚本."""
import sys
import json


def main():
    """主函数."""
    data = json.loads(sys.stdin.read())
    result = process_data(data)
    print(json.dumps(result))


def process_data(data):
    """处理数据."""
    return {"result": data}


if __name__ == "__main__":
    main()
```

### Shell / Bash

**推荐度**：⭐⭐⭐⭐⭐

**适用场景**：

- Hooks 脚本
- 系统操作
- 文件处理
- Git 操作

**优点**：

- 系统原生支持
- 执行效率高
- 无需额外依赖

**缺点**：

- 跨平台兼容性差
- 复杂逻辑难维护

**示例**：

```bash
#!/bin/bash
# scripts/format.sh

for file in "$@"; do
  case "${file##*.}" in
    js|ts) npx prettier --write "$file" ;;
    py) black "$file" ;;
    go) gofmt -w "$file" ;;
  esac
done
```

### Node.js / JavaScript

**推荐度**：⭐⭐⭐⭐

**适用场景**：

- Web 相关工具
- 前端构建
- 包管理
- API 开发

**优点**：

- 生态庞大
- 异步处理
- npm 生态

**缺点**：

- 需要 Node 环境
- 版本管理复杂

**示例**：

```javascript
#!/usr/bin/env node
const { execSync } = require('child_process');

function formatCode(filePath) {
  execSync(`npx prettier --write ${filePath}`, {
    stdio: 'inherit'
  });
}

formatCode(process.argv[2]);
```

## 编程语言

### Go

**推荐度**：⭐⭐⭐⭐⭐

**适用场景**：

- 高性能工具
- 系统工具
- 微服务
- CLI 应用

**优点**：

- 编译型，性能高
- 单文件部署
- 跨平台编译
- 并发优秀

**缺点**：

- 需要预编译
- 学习曲线

**详细指南**：参见 [编译型语言指南](compiled-languages-guide.md)

### Rust

**推荐度**：⭐⭐⭐⭐

**适用场景**：

- 系统工具
- 高性能服务
- WebAssembly
- CLI 应用

**优点**：

- 内存安全
- 性能极佳
- 跨平台
- 包管理优秀

**缺点**：

- 学习曲线陡
- 编译时间长

**详细指南**：参见 [编译型语言指南](compiled-languages-guide.md)

### C/C++

**推荐度**：⭐⭐⭐

**适用场景**：

- 系统级工具
- 性能关键应用
- 嵌入式

**优点**：

- 性能最佳
- 底层控制
- 广泛支持

**缺点**：

- 内存管理复杂
- 开发效率低
- 跨平台问题

## 语言选择指南

### 按场景选择

| 场景 | 推荐语言 | 理由 |
|------|----------|------|
| **Hooks** | Bash | 系统原生，快速执行 |
| **文本处理** | Python | 强大的字符串处理 |
| **Web 工具** | Node.js | 生态丰富 |
| **系统工具** | Go / Rust | 高性能，单文件 |
| **数据脚本** | Python | 简洁易用 |
| **快速原型** | Python / Bash | 开发效率高 |
| **生产工具** | Go / Rust | 稳定可靠 |
| **MCP 服务器** | Python | 生态完善 |

### 按性能选择

```
性能排名 (从高到低)：
Rust ≈ C/C++ > Go > Java > Node.js > Python > Ruby > Bash
```

### 按开发效率选择

```
开发效率 (从高到低)：
Python ≈ Bash > Ruby > Node.js > Go > Rust > Java > C/C++
```

### 按跨平台选择

| 语言 | Windows | macOS | Linux | 备注 |
|------|---------|-------|-------|------|
| Python | ✅ | ✅ | ✅ | 最佳 |
| Node.js | ✅ | ✅ | ✅ | 优秀 |
| Go | ✅ | ✅ | ✅ | 需编译 |
| Rust | ✅ | ✅ | ✅ | 需编译 |
| Bash | ❌ | ✅ | ✅ | 需WSL/Cygwin |

## 最佳实践

### 语言选择原则

**简单场景**：

- 优先使用 Bash
- 快速原型用 Python

**复杂场景**：

- 逻辑复杂用 Python
- 性能关键用 Go/Rust

**生产环境**：

- 编译为可执行文件
- 提供多平台支持

### 混合语言策略

```
示例插件架构：
├── commands/
│   └── process.md        # Markdown 命令定义
├── scripts/
│   ├── format.sh         # Bash: 快速格式化
│   ├── analyze.py        # Python: 复杂分析
│   └── server            # Go: 高性能服务
└── hooks.json
```

### 依赖管理

**Python**：

```bash
# 使用 pyproject.toml
[project]
dependencies = [
    "requests>=2.28.0",
    "pydantic>=2.0.0",
]

# 使用 uv
uv pip install -e .
```

**Node.js**：

```bash
# 使用 package.json
{
  "dependencies": {
    "prettier": "^3.0.0"
  }
}

# 安装
npm install
```

**Go**：

```bash
# 使用 go.mod
go mod init github.com/user/plugin

# 编译
go build -o bin/mytool .
```

### 环境变量

使用环境变量处理路径：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/my-script.py"
      }
    ]
  }
}
```

```python
import os

plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT')
```

### Shebang 规范

确保脚本可执行：

```bash
#!/usr/bin/env bash    # 推荐
#!/bin/bash           # 也可

#!/usr/bin/env python3
#!/usr/bin/env node
```

## 语言特性对比

| 特性 | Bash | Python | Node.js | Go | Rust |
|------|------|--------|---------|-----|------|
| **类型系统** | 弱 | 动态 | 动态 | 静态 | 静态 |
| **并发** | 差 | 中 | 异步 | 优秀 | 优秀 |
| **性能** | 中 | 中 | 中 | 高 | 极高 |
| **学习曲线** | 简单 | 简单 | 中等 | 中等 | 陡 |
| **跨平台** | 中 | 优秀 | 优秀 | 需编译 | 需编译 |
| **部署** | 脚本 | 脚本 | 脚本 | 单文件 | 单文件 |
| **生态** | 系统命令 | 庞大 | 庞大 | 成长中 | 成长中 |

## 参考资源

### 项目文档

- [插件开发指南](plugin-development.md) - 完整开发教程
- [API 参考](api-reference.md) - 完整 API 文档
- [编译型语言指南](compiled-languages-guide.md) - Go/Rust 开发指南

### 语言资源

- **Python**: [Python Docs](https://docs.python.org/)
- **Bash**: [Bash Guide](https://github.com/Idnan/bash-guide)
- **Node.js**: [Node.js Docs](https://nodejs.org/docs)
- **Go**: [Go Tour](https://go.dev/tour/)
- **Rust**: [Rust Book](https://doc.rust-lang.org/book/)

## 总结

**推荐组合**：

| 级别 | 组合 | 适用场景 |
|------|------|----------|
| 入门级 | Bash + Python | 简单插件开发 |
| Web级 | Node.js + Bash | Web 相关工具 |
| 专业级 | Go + Python + Bash | 高性能工具 |
| 性能级 | Rust + Python + Bash | 极致性能需求 |

**选择依据**：

- 简单任务 → Bash
- 复杂逻辑 → Python
- Web工具 → Node.js
- 系统工具 → Go
- 极致性能 → Rust

**关键原则**：

- 适合 > 流行
- 简单 > 复杂
- 维护 > 性能 (除非性能关键)
