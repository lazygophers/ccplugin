---
name: plugin-quality-check
description: 插件质量检查工具 - 验证 AI 对优化后插件组件的理解准确性
---

# 插件质量检查

## 验证命令

对于 commands、skills、agents、agent.md 的优化、简化，必须通过以下命令检查 AI 是否可以正确理解识别，是否符合预期：

```bash
claude --settings ~/.claude/settings.glm-4.5-flash.json -p "<待测试的内容>" \
  --output-format stream-json | \
  jq -r 'select(.type == "result" and .subtype == "success") | .result' | \
  tr -d '\n'
```

## 使用场景

在以下情况下使用此验证命令：
- 优化或简化 `commands/` 文件后
- 优化或简化 `skills/` 文件后
- 优化或简化 `agents/` 文件后
- 优化或简化 `AGENT.md` 文件后

## 验收标准

验证通过需满足：
1. 返回结果非空
2. 返回结果准确反映原始内容的语义
3. AI 能正确识别文件类型和角色
4. 无明显的理解偏差或信息丢失

## 前置要求

- 已安装 `jq` 命令行工具
- 已安装 Claude Code CLI (`claude`)
- 已配置对应的模型设置文件（如 `~/.claude/settings.glm-4.5-flash.json`）

## 示例

```bash
# 验证一个优化后的 command 文件
claude --settings ~/.claude/settings.glm-4.5-flash.json \
  -p "$(cat commands/loop.md)" \
  --output-format stream-json | \
  jq -r 'select(.type == "result" and .subtype == "success") | .result'
```
