# Go/Rust 等编译型语言在插件中的使用指南

## 核心问题

**Claude Code 插件安装时不会自动编译代码。**

插件安装过程只是：
1. 复制插件文件到本地
2. 解析 `plugin.json` 配置
3. 注册 commands/agents/skills

## 三种解决方案

### 方案1: 预编译二进制（推荐）

**优点**：
- 用户无需编译环境
- 安装即用
- 体积小（只包含二进制）

**缺点**：
- 需要为多平台编译
- 更新需要重新发布

**目录结构**：
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── bin/
│   ├── mytool-darwin-amd64    # macOS Intel
│   ├── mytool-darwin-arm64    # macOS Apple Silicon
│   ├── mytool-linux-amd64     # Linux AMD64
│   └── mytool-windows-amd64.exe
├── scripts/
│   └── detect-platform.sh     # 自动选择合适版本
└── commands/
    └── my-command.md
```

**实现示例**：

1. **编译脚本** (`scripts/build.sh`):
```bash
#!/bin/bash
GOOS=darwin GOARCH=amd64 go build -o ../bin/mytool-darwin-amd64 .
GOOS=darwin GOARCH=arm64 go build -o ../bin/mytool-darwin-arm64 .
GOOS=linux GOARCH=amd64 go build -o ../bin/mytool-linux-amd64 .
GOOS=windows GOARCH=amd64 go build -o ../bin/mytool-windows-amd64.exe .
```

2. **平台检测脚本** (`scripts/detect-platform.sh`):
```bash
#!/bin/bash
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

case "$ARCH" in
    x86_64) ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    i386|i686) ARCH="386" ;;
esac

BINARY="${PLUGIN_ROOT}/bin/mytool-${OS}-${ARCH}"
if [ -f "$BINARY" ]; then
    exec "$BINARY" "$@"
else
    echo "Error: No pre-built binary for ${OS}-${ARCH}"
    exit 1
fi
```

3. **命令引用** (`commands/my-command.md`):
```markdown
---
description: 执行工具
allowed-tools: Bash
---
# my-command

执行工具。

## 执行
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/detect-platform.sh "$@"
```
```

### 方案2: 源码 + 首次运行时编译

**优点**：
- 只需维护源码
- 自动适配平台

**缺点**：
- 用户需要编译环境
- 首次运行慢
- 可能因环境差异失败

**目录结构**：
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── src/
│   ├── main.go             # Go 源码
│   ├── go.mod
│   └── go.sum
├── bin/                    # 编译输出目录
│   └── .gitkeep
├── scripts/
│   └── ensure-build.sh     # 确保已编译
└── commands/
    └── my-command.md
```

**实现示例**：

1. **确保编译脚本** (`scripts/ensure-build.sh`):
```bash
#!/bin/bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
BINARY="$PLUGIN_ROOT/bin/mytool"
SRC_DIR="$PLUGIN_ROOT/src"

# 检查是否已编译
if [ -f "$BINARY" ]; then
    exec "$BINARY" "$@"
fi

# 首次编译
echo "首次运行，正在编译..."
cd "$SRC_DIR"
go build -o "$BINARY" .

if [ $? -eq 0 ]; then
    echo "编译成功！"
    exec "$BINARY" "$@"
else
    echo "编译失败，请检查 Go 环境"
    exit 1
fi
```

2. **命令引用** (`commands/my-command.md`):
```markdown
---
description: 执行工具（首次运行会自动编译）
allowed-tools: Bash
---
# my-command

执行工具。

## 注意
首次运行会自动编译，需要 Go 环境。

## 执行
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/ensure-build.sh "$@"
```
```

### 方案3: 混合方案（推荐用于复杂插件）

**策略**：
- 优先使用预编译二进制
- 回退到源码编译
- 提供清晰错误提示

**目录结构**：
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
├── bin/                     # 预编译二进制
│   ├── mytool-darwin-amd64
│   └── ...
├── src/                     # 源码（备用）
│   ├── main.go
│   ├── go.mod
│   └── go.sum
├── scripts/
│   └── run-tool.sh         # 智能运行脚本
└── commands/
    └── my-command.md
```

**实现示例**：

1. **智能运行脚本** (`scripts/run-tool.sh`):
```bash
#!/bin/bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

# 1. 尝试预编译二进制
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
case "$ARCH" in
    x86_64) ARCH="amd64" ;;
    arm64|aarch64) ARCH="arm64" ;;
esac

PREBUILT="$PLUGIN_ROOT/bin/mytool-${OS}-${ARCH}"

if [ -f "$PREBUILT" ]; then
    exec "$PREBUILT" "$@"
fi

# 2. 回退到源码编译
BINARY="$PLUGIN_ROOT/bin/mytool"
if [ -f "$BINARY" ]; then
    exec "$BINARY" "$@"
fi

# 3. 尝试编译
echo "未找到预编译二进制，尝试从源码编译..."
SRC_DIR="$PLUGIN_ROOT/src"

if [ ! -d "$SRC_DIR" ]; then
    echo "错误：未找到源码目录"
    echo "请安装预编译版本或确保 Go 环境可用"
    exit 1
fi

cd "$SRC_DIR"
if command -v go &> /dev/null; then
    go build -o "$BINARY" .
    if [ $? -eq 0 ]; then
        echo "编译成功！"
        exec "$BINARY" "$@"
    fi
else
    echo "错误：未找到 Go 编译环境"
    echo "请访问 https://golang.org/dl/ 安装 Go"
    exit 1
fi
```

## 完整示例：Go 插件

### 目录结构

```
go-tool-plugin/
├── .claude-plugin/
│   └── plugin.json
├── src/                     # Go 源码
│   ├── main.go
│   ├── go.mod
│   └── go.sum
├── bin/                     # 预编译二进制（发布时包含）
│   ├── mytool-darwin-amd64
│   ├── mytool-darwin-arm64
│   ├── mytool-linux-amd64
│   └── mytool-windows-amd64.exe
├── scripts/
│   ├── build.sh            # 编译脚本（开发者用）
│   └── run.sh              # 运行脚本（用户用）
├── commands/
│   └── process.md
└── README.md
```

### plugin.json

```json
{
  "name": "go-tool-plugin",
  "version": "1.0.0",
  "description": "Go 工具插件示例",
  "author": {
    "name": "Your Name"
  },
  "commands": "./commands/",
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/run.sh --check"
      }
    ]
  }
}
```

### Go 源码 (src/main.go)

```go
package main

import "fmt"

func main() {
    fmt.Println("Hello from Go tool!")
}
```

### 编译脚本 (scripts/build.sh)

```bash
#!/bin/bash
set -e

echo "Building Go tool for multiple platforms..."

mkdir -p ../bin

GOOS=darwin GOARCH=amd64 go build -o ../bin/mytool-darwin-amd64 .
GOOS=darwin GOARCH=arm64 go build -o ../bin/mytool-darwin-arm64 .
GOOS=linux GOARCH=amd64 go build -o ../bin/mytool-linux-amd64 .
GOOS=windows GOARCH=amd64 go build -o ../bin/mytool-windows-amd64.exe .

echo "Build complete!"
ls -lh ../bin/
```

### 运行脚本 (scripts/run.sh)

```bash
#!/bin/bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

# 平台检测
detect_platform() {
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64) ARCH="amd64" ;;
        arm64|aarch64) ARCH="arm64" ;;
    esac
    echo "${OS}-${ARCH}"
}

# 查找二进制
BINARY=""
PLATFORM=$(detect_platform)

# 1. 预编译版本
PREBUILT="$PLUGIN_ROOT/bin/mytool-${PLATFORM}"
if [ -f "$PREBUILT" ]; then
    BINARY="$PREBUILT"
fi

# 2. 通用编译版本
if [ -z "$BINARY" ]; then
    GENERIC="$PLUGIN_ROOT/bin/mytool"
    if [ -f "$GENERIC" ]; then
        BINARY="$GENERIC"
    fi
fi

# 3. 执行或编译
if [ -n "$BINARY" ]; then
    exec "$BINARY" "$@"
else
    echo "未找到预编译二进制 (${PLATFORM})"
    echo "正在尝试从源码编译..."
    if command -v go &> /dev/null; then
        cd "$PLUGIN_ROOT/src"
        go build -o "$PLUGIN_ROOT/bin/mytool" .
        exec "$PLUGIN_ROOT/bin/mytool" "$@"
    else
        echo "错误：需要 Go 环境来编译"
        echo "请访问 https://golang.org/dl/ 安装 Go"
        exit 1
    fi
fi
```

### 命令定义 (commands/process.md)

```markdown
---
description: 使用 Go 工具处理数据
argument-hint: [input]
allowed-tools: Bash
---
# process

使用 Go 工具处理数据。

## 使用方法

/process [input-file]

## 执行
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/run.sh "$@"
```
```

## Rust 特殊说明

Rust 与 Go 类似，但有一些特殊考虑：

### Cargo 构建脚本

```bash
#!/bin/bash
# scripts/build.sh

cargo build --release
mkdir -p ../bin
cp target/release/mytool ../bin/
```

### 交叉编译

```bash
#!/bin/bash
# 安装交叉编译目标
rustup target add x86_64-apple-darwin
rustup target add aarch64-apple-darwin
rustup target add x86_64-unknown-linux-gnu

# 交叉编译
cargo build --release --target x86_64-apple-darwin
cargo build --release --target aarch64-apple-darwin
cargo build --release --target x86_64-unknown-linux-gnu
```

### 运行脚本

```bash
#!/bin/bash
# scripts/run.sh

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"

# 检查预编译版本
# (类似 Go 的实现)

# 回退到 cargo run
if [ ! -f "$BINARY" ]; then
    cd "$PLUGIN_ROOT"
    if command -v cargo &> /dev/null; then
        cargo run --release "$@"
    else
        echo "错误：需要 Rust 环境"
        exit 1
    fi
fi
```

## 发布检查清单

### 预编译方案（推荐）

- [ ] 为所有目标平台编译
  - [ ] macOS Intel (x86_64)
  - [ ] macOS ARM (arm64)
  - [ ] Linux AMD64
  - [ ] Windows AMD64
- [ ] 测试各平台二进制
- [ ] 更新版本号
- [ ] 不包含源码（可选）

### 源码方案

- [ ] 包含完整源码
- [ ] 提供编译脚本
- [ ] 文档说明依赖要求
- [ ] 提供回退方案

### 混合方案

- [ ] 包含主要平台预编译版本
- [ ] 包含完整源码
- [ ] 提供智能运行脚本
- [ ] 清晰的错误提示

## 总结

| 方案 | 推荐度 | 用户体验 | 开发成本 |
|------|--------|----------|----------|
| 预编译 | ⭐⭐⭐⭐⭐ | 最佳 | 高 |
| 源码编译 | ⭐⭐ | 较差 | 低 |
| 混合方案 | ⭐⭐⭐⭐ | 良好 | 中 |

**推荐策略**：
- 小工具 → 预编译
- 大型项目 → 混合方案
- 开发测试 → 源码编译
