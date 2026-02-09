# 插件本地配置

## 配置模式

插件支持通过 `.claude/plugin-name.local.md` 文件进行项目级配置：

```
.claude/
├── plugin-name.local.md    # 插件本地配置
└── plugin-name.local.json  # 也可以是 JSON 格式
```

## 用途场景

- 存储 API 密钥和凭证
- 配置插件行为参数
- 设置项目特定规则
- 定义自定义模板

## 配置格式

### Markdown 格式

```markdown
---
# 配置字段
api-key: ${OPENAI_API_KEY}
model: gpt-4
temperature: 0.7

# 插件特定配置
max-tokens: 4096
output-format: json
---

## 项目自定义规则

本项目使用特定的输出格式...
```

### JSON 格式

```json
{
  "api-key": "${OPENAI_API_KEY}",
  "model": "gpt-4",
  "temperature": 0.7,
  "max-tokens": 4096
}
```

## 使用变量

支持环境变量引用：

```markdown
---
api-key: ${OPENAI_API_KEY}
api-secret: ${API_SECRET}
custom-path: ${CLAUDE_PLUGIN_ROOT}/data
---
```

## 配置优先级

1. **项目配置** (`.claude/plugin.local.md`) - 最高
2. **全局配置** (`~/.claude/plugin.local.md`)
3. **默认配置** (插件内置)

## 安全注意事项

```markdown
# ✅ 正确 - 使用环境变量
api-key: ${OPENAI_API_KEY}

# ❌ 避免 - 硬编码密钥
api-key: sk-xxxactual_key_xxx
```

## 完整示例

```markdown
---
# API 配置
model: gpt-4o
temperature: 0.5
max-tokens: 8192

# 项目特定规则
project-name: ccplugin
output-dir: ./outputs
template-dir: ./templates

# 启用功能
features:
  - analysis
  - export
  - notification
---

## ccplugin 项目配置

本项目使用 ccplugin 进行插件开发管理。

### 自定义规则

- 所有输出保存到 `./outputs` 目录
- 使用 `ccplugin-` 前缀命名
- 遵循项目编码规范
```
