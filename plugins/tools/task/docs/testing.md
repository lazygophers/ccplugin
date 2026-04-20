# Task 插件测试指南

使用 Claude Agent SDK 模拟 Claude Code 调用来测试插件行为。

## 安装依赖

```bash
uv sync --extra dev
```

## 快速开始

### 列出所有测试场景

```bash
uv run ./scripts/main.py test list-scenarios
```

### 运行完整工作流测试

```bash
# 使用默认 sonnet 模型
uv run ./scripts/main.py test workflow --scenario simple-bug-fix

# 使用 opus 模型
uv run ./scripts/main.py test workflow --scenario new-feature --model opus

# 详细输出
uv run ./scripts/main.py test workflow --scenario simple-bug-fix --verbose
```

### 测试单个 Skill

```bash
# 测试 explore skill
uv run ./scripts/main.py test skill --name explore

# 测试 align skill
uv run ./scripts/main.py test skill --name align

# 使用自定义场景
uv run ./scripts/main.py test skill --name flow --scenario simple-bug-fix --model opus
```

### 测试单个 Agent

```bash
# 测试 explore agent
uv run ./scripts/main.py test agent --name explore --input "修复登录问题"

# 测试 plan agent，使用 opus 模型
uv run ./scripts/main.py test agent --name plan --input "添加日志功能" --model opus --verbose
```

## 可用选项

### 通用选项

- `--model [sonnet|opus|haiku]` - 使用的模型（默认: sonnet）
- `--verbose` - 详细输出
- `--timeout INTEGER` - 超时时间（秒，默认: 300）

### workflow 命令

```bash
uv run ./scripts/main.py test workflow --scenario <场景名> [选项]
```

可用场景：
- `simple-bug-fix` - 简单 Bug 修复
- `new-feature` - 新功能开发
- `explore-only` - 仅探索上下文
- `align-only` - 仅对齐范围

### skill 命令

```bash
uv run ./scripts/main.py test skill --name <skill名> [选项]
```

可用 skills：
- `flow` - 流程管理
- `align` - 范围对齐
- `explore` - 上下文探索
- `plan` - 任务规划
- `exec` - DAG 执行
- `verify` - 结果校验
- `adjust` - 失败调整
- `done` - 任务完成
- `resume` - 中断恢复

### agent 命令

```bash
uv run ./scripts/main.py test agent --name <agent名> --input <输入> [选项]
```

可用 agents：
- `explore` - 探索代理
- `plan` - 规划代理
- `verify` - 校验代理
- `adjust` - 调整代理
- `done` - 完成代理

## 环境配置

测试命令会自动继承当前 shell 的环境变量，包括：

- `ANTHROPIC_BASE_URL` - API 端点
- `ANTHROPIC_AUTH_TOKEN` - 认证令牌
- `ANTHROPIC_DEFAULT_SONNET_MODEL` - sonnet 模型映射
- `ANTHROPIC_DEFAULT_OPUS_MODEL` - opus 模型映射
- `ANTHROPIC_DEFAULT_HAIKU_MODEL` - haiku 模型映射

## 测试场景配置

测试场景定义在 `scripts/test_scenarios.json` 中。每个场景包含：

```json
{
  "场景名": {
    "name": "显示名称",
    "description": "场景描述",
    "prompt": "测试 prompt",
    "allowed_tools": ["Read", "Edit", ...],
    "expectations": {
      "state_transitions": ["pending", "align", ...],
      "tool_calls": {
        "Read": {"min": 1}
      },
      "final_state": "done",
      "files_created": ["context.json", ...]
    }
  }
}
```

### 添加自定义场景

1. 编辑 `scripts/test_scenarios.json`
2. 添加新的场景配置
3. 运行测试：`uv run ./scripts/main.py test workflow --scenario <新场景名>`

## 验证机制

测试框架会验证以下内容：

### 状态转换验证

检查任务状态转换序列是否符合预期（从 `[flow·{task_id}·{state}]` 提取）。

### 工具调用验证

验证特定工具的调用次数：
- `min` - 最少调用次数
- `max` - 最多调用次数
- `exact` - 精确调用次数

### 最终状态验证

检查任务是否达到预期的最终状态（如 `done`）。

### 文件系统验证

验证预期的文件是否被创建（在 `.lazygophers/tasks/{task_id}/` 目录下）。

## 测试报告

测试完成后会生成报告，包含：

```
============================================================
测试报告
============================================================
总计: 3 | 通过: 3 | 失败: 0

1. ✓ 状态转换正确: pending → align → plan → exec → verify → done
2. ✓ 工具调用符合预期
3. ✓ 最终状态正确: done
============================================================
```

## 常见问题

### 测试超时

默认超时 300 秒，可通过 `--timeout` 调整：

```bash
uv run ./scripts/main.py test workflow --scenario simple-bug-fix --timeout 600
```

### 环境变量未设置

确保设置了必要的环境变量：

```bash
export ANTHROPIC_BASE_URL="https://api.example.com"
export ANTHROPIC_AUTH_TOKEN="your-token"
```

或使用特定配置运行：

```bash
ANTHROPIC_BASE_URL="https://api.example.com" \
uv run ./scripts/main.py test workflow --scenario simple-bug-fix
```

### 测试中断

使用 `Ctrl+C` 可以中断测试，已收集的消息会被保留用于调试。

## 示例

### 完整工作流测试

```bash
# 测试 bug 修复流程（sonnet 模型）
uv run ./scripts/main.py test workflow \
  --scenario simple-bug-fix \
  --model sonnet \
  --verbose

# 测试新功能开发（opus 模型）
uv run ./scripts/main.py test workflow \
  --scenario new-feature \
  --model opus \
  --timeout 600
```

### 独立组件测试

```bash
# 仅测试上下文探索
uv run ./scripts/main.py test skill --name explore

# 测试范围对齐（需要用户交互）
uv run ./scripts/main.py test skill --name align

# 测试 DAG 执行
uv run ./scripts/main.py test skill --name exec
```

### Agent 测试

```bash
# 测试探索 agent
uv run ./scripts/main.py test agent \
  --name explore \
  --input "了解项目测试框架" \
  --verbose

# 测试规划 agent
uv run ./scripts/main.py test agent \
  --name plan \
  --input "添加新的日志模块" \
  --model opus
```

## 贡献

欢迎添加新的测试场景和改进验证逻辑：

1. 在 `scripts/test_scenarios.json` 添加场景
2. 在 `scripts/test_helpers.py` 添加验证函数
3. 提交 PR

## 参考

- [Claude Agent SDK 文档](https://code.claude.com/docs/en/agent-sdk/overview)
- [Task 插件 README](../README.md)
- [状态管理文档](./状态管理.md)
