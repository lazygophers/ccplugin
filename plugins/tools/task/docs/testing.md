# Task 插件测试指南

使用 Claude Agent SDK 模拟 Claude Code 调用来测试插件行为。

## 安装依赖

```bash
uv sync --extra dev
```

## 快速开始

### 基础用法

像 `claude -p` 一样，直接传入提示词：

```bash
# 基础测试
uv run ./scripts/main.py test "修复登录 Bug"

# 使用 opus 模型
uv run ./scripts/main.py test "添加日志功能" --model opus

# 详细输出
uv run ./scripts/main.py test "优化查询性能" -v

# 简写形式
uv run ./scripts/main.py test "重构认证模块" -m haiku -v
```

### 测试插件 Skills

```bash
# 测试 flow skill（完整工作流）
uv run ./scripts/main.py test "/task:flow 修复登录验证逻辑错误"

# 测试 explore skill（上下文探索）
uv run ./scripts/main.py test "/task:explore 了解当前项目的测试框架"

# 测试 align skill（范围对齐）
uv run ./scripts/main.py test "/task:align 添加新的日志模块"

# 测试 plan skill（任务规划）
uv run ./scripts/main.py test "/task:plan 重构数据库访问层"
```

## 命令选项

### 位置参数

- `PROMPT` - 要测试的提示词（必需）

### 可选参数

- `--model, -m [sonnet|opus|haiku]` - 使用的模型（默认: sonnet）
- `--verbose, -v` - 详细输出，显示工具调用和中间步骤
- `--timeout, -t INTEGER` - 超时时间（秒，默认: 300）
- `--tools TEXT` - 允许使用的工具（可多次指定）

## 模型选择

支持三种固定模型：

- `sonnet` - 平衡性能和速度（默认）
- `opus` - 最强性能，适合复杂任务
- `haiku` - 最快速度，适合简单任务

实际的模型映射由环境变量决定：
- `ANTHROPIC_DEFAULT_SONNET_MODEL`
- `ANTHROPIC_DEFAULT_OPUS_MODEL`
- `ANTHROPIC_DEFAULT_HAIKU_MODEL`

## 环境配置

测试命令会自动继承当前 shell 的环境变量：

- `ANTHROPIC_BASE_URL` - API 端点
- `ANTHROPIC_AUTH_TOKEN` - 认证令牌
- `ANTHROPIC_DEFAULT_SONNET_MODEL` - sonnet 模型映射
- `ANTHROPIC_DEFAULT_OPUS_MODEL` - opus 模型映射
- `ANTHROPIC_DEFAULT_HAIKU_MODEL` - haiku 模型映射

示例：

```bash
# 设置环境变量
export ANTHROPIC_BASE_URL="https://api.example.com"
export ANTHROPIC_AUTH_TOKEN="your-token"

# 运行测试
uv run ./scripts/main.py test "修复 Bug"
```

或临时指定：

```bash
ANTHROPIC_BASE_URL="https://api.example.com" \
ANTHROPIC_AUTH_TOKEN="your-token" \
uv run ./scripts/main.py test "修复 Bug"
```

## 工具控制

默认允许使用的工具：
- Read, Write, Edit
- Glob, Grep
- Bash
- AskUserQuestion

### 自定义工具集

```bash
# 仅允许读取和搜索
uv run ./scripts/main.py test "分析代码结构" \
  --tools Read \
  --tools Glob \
  --tools Grep

# 仅允许 Bash 命令
uv run ./scripts/main.py test "运行测试" --tools Bash
```

## 测试输出

### 标准输出

测试会实时输出模型的响应：

```
测试提示词: 修复登录 Bug
使用模型: sonnet
允许工具: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
------------------------------------------------------------

[模型的响应输出...]

============================================================
测试摘要
============================================================
消息数量: 15
工具调用数: 8

调用的工具:
  - Bash: 1 次
  - Edit: 2 次
  - Grep: 2 次
  - Read: 3 次

状态转换: pending → align → explore → plan → exec → verify → done
最终状态: done
============================================================
```

### 详细输出（-v）

添加 `-v` 标志会显示：
- 会话初始化信息
- 每次工具调用的详细信息
- 中间输出文本

```bash
uv run ./scripts/main.py test "修复 Bug" -v
```

## 测试场景示例

### 1. Bug 修复

```bash
uv run ./scripts/main.py test "修复用户登录时的验证逻辑错误" -m sonnet
```

### 2. 新功能开发

```bash
uv run ./scripts/main.py test "添加日志记录功能到所有 API 端点" -m opus -v
```

### 3. 代码重构

```bash
uv run ./scripts/main.py test "重构数据库访问层，使用连接池" -m sonnet
```

### 4. 测试完整工作流

```bash
# 使用 flow skill 触发完整的状态机流程
uv run ./scripts/main.py test "/task:flow 优化查询性能" -m opus -v
```

### 5. 仅探索上下文

```bash
# 使用 explore skill 了解项目结构
uv run ./scripts/main.py test "/task:explore 了解项目的测试框架和工具链" -m sonnet
```

### 6. 仅对齐需求

```bash
# 使用 align skill 明确任务范围
uv run ./scripts/main.py test "/task:align 添加用户权限管理功能" -m sonnet
```

## 常见问题

### 测试超时

默认超时 300 秒（5 分钟），对于复杂任务可能需要更长时间：

```bash
uv run ./scripts/main.py test "复杂重构任务" -t 600
```

### 环境变量未设置

如果看到 API 错误，检查环境变量是否正确设置：

```bash
echo $ANTHROPIC_BASE_URL
echo $ANTHROPIC_AUTH_TOKEN
```

### 测试中断

使用 `Ctrl+C` 可以随时中断测试。测试摘要仍会显示已收集的信息。

### 工具调用失败

如果某个工具调用失败，会在输出中显示错误信息。使用 `-v` 查看详细的工具调用过程。

## 高级用法

### 组合使用

```bash
# 复杂任务，使用 opus 模型，详细输出，长超时
uv run ./scripts/main.py test \
  "/task:flow 重构整个认证系统，支持 OAuth2" \
  -m opus \
  -v \
  -t 900
```

### 限制工具权限

```bash
# 只允许读取和分析，不允许修改
uv run ./scripts/main.py test \
  "分析代码质量和潜在问题" \
  --tools Read \
  --tools Glob \
  --tools Grep \
  --tools Bash
```

### 脚本化测试

创建测试脚本：

```bash
#!/bin/bash
# test-scenarios.sh

# 测试多个场景
scenarios=(
  "修复登录 Bug"
  "添加日志功能"
  "优化查询性能"
)

for scenario in "${scenarios[@]}"; do
  echo "测试场景: $scenario"
  uv run ./scripts/main.py test "$scenario" -m sonnet
  echo "---"
done
```

## 与 Claude Code 的区别

| 特性 | Claude Code CLI | Task 测试命令 |
|------|----------------|--------------|
| 用途 | 交互式开发 | 自动化测试 |
| 输出 | 完整对话 | 聚焦结果 |
| 工具 | 所有工具 | 可限制工具集 |
| 配置 | 全局配置 | 项目配置 |
| 统计 | 无 | 工具调用统计 |

## 参考

- [Claude Agent SDK 文档](https://code.claude.com/docs/en/agent-sdk/overview)
- [Task 插件 README](../README.md)
- [状态管理文档](./状态管理.md)
