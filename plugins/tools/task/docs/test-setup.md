# 测试环境设置指南

## 环境变量配置

测试命令需要以下环境变量才能正常工作：

### 方法 1: 使用主配置文件的环境变量

如果你已经配置了 Claude Code，可以从主配置中导出环境变量：

```bash
# 读取 ~/.claude/settings.json 中的环境变量
export ANTHROPIC_BASE_URL=$(jq -r '.env.ANTHROPIC_BASE_URL' ~/.claude/settings.json)
export ANTHROPIC_AUTH_TOKEN=$(jq -r '.env.ANTHROPIC_AUTH_TOKEN' ~/.claude/settings.json)

# 验证
echo "ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
echo "ANTHROPIC_AUTH_TOKEN: ${ANTHROPIC_AUTH_TOKEN:0:20}..."
```

### 方法 2: 使用特定配置文件

如果你有多个配置文件（如 settings.glm.json）：

```bash
# 使用 glm 配置
export ANTHROPIC_BASE_URL=$(jq -r '.env.ANTHROPIC_BASE_URL' ~/.claude/settings.glm.json)
export ANTHROPIC_AUTH_TOKEN=$(jq -r '.env.ANTHROPIC_AUTH_TOKEN' ~/.claude/settings.glm.json)
```

### 方法 3: 手动设置

```bash
export ANTHROPIC_BASE_URL="https://your-api-endpoint.com"
export ANTHROPIC_AUTH_TOKEN="your-auth-token"
```

## 模型映射配置（可选）

如果你使用自定义模型映射：

```bash
export ANTHROPIC_DEFAULT_SONNET_MODEL="your-sonnet-model"
export ANTHROPIC_DEFAULT_OPUS_MODEL="your-opus-model"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="your-haiku-model"
```

## 快速设置脚本

创建 `scripts/setup-test-env.sh`：

```bash
#!/bin/bash
# 从主配置加载环境变量

CONFIG_FILE="${1:-$HOME/.claude/settings.json}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "配置文件不存在: $CONFIG_FILE"
    exit 1
fi

export ANTHROPIC_BASE_URL=$(jq -r '.env.ANTHROPIC_BASE_URL // empty' "$CONFIG_FILE")
export ANTHROPIC_AUTH_TOKEN=$(jq -r '.env.ANTHROPIC_AUTH_TOKEN // empty' "$CONFIG_FILE")

# 可选：模型映射
export ANTHROPIC_DEFAULT_SONNET_MODEL=$(jq -r '.env.ANTHROPIC_DEFAULT_SONNET_MODEL // "sonnet"' "$CONFIG_FILE")
export ANTHROPIC_DEFAULT_OPUS_MODEL=$(jq -r '.env.ANTHROPIC_DEFAULT_OPUS_MODEL // "opus"' "$CONFIG_FILE")
export ANTHROPIC_DEFAULT_HAIKU_MODEL=$(jq -r '.env.ANTHROPIC_DEFAULT_HAIKU_MODEL // "haiku"' "$CONFIG_FILE")

# 其他相关变量
while IFS= read -r key; do
    value=$(jq -r ".env.\"$key\"" "$CONFIG_FILE")
    if [ "$value" != "null" ] && [ -n "$value" ]; then
        export "$key=$value"
    fi
done < <(jq -r '.env | keys[]' "$CONFIG_FILE")

echo "环境变量已加载:"
echo "  ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
echo "  ANTHROPIC_AUTH_TOKEN: ${ANTHROPIC_AUTH_TOKEN:0:20}..."
echo "  ANTHROPIC_DEFAULT_SONNET_MODEL: $ANTHROPIC_DEFAULT_SONNET_MODEL"
echo "  ANTHROPIC_DEFAULT_OPUS_MODEL: $ANTHROPIC_DEFAULT_OPUS_MODEL"
echo "  ANTHROPIC_DEFAULT_HAIKU_MODEL: $ANTHROPIC_DEFAULT_HAIKU_MODEL"
```

使用方法：

```bash
# 使用默认配置
source scripts/setup-test-env.sh

# 使用特定配置
source scripts/setup-test-env.sh ~/.claude/settings.glm.json

# 运行测试
uv run ./scripts/main.py test "测试提示词"
```

## 验证环境配置

运行以下命令验证配置是否正确：

```bash
# 检查环境变量
env | grep ANTHROPIC

# 快速测试（应该能正常响应）
uv run ./scripts/main.py test "hello" -t 30
```

如果测试正常响应（不超时），说明配置正确。

## 常见问题

### 1. 测试超时

**症状**：测试一直挂起，最后超时

**原因**：环境变量未设置或 API 端点不可达

**解决**：
```bash
# 检查环境变量
echo $ANTHROPIC_BASE_URL
echo $ANTHROPIC_AUTH_TOKEN

# 测试 API 连接
curl -I $ANTHROPIC_BASE_URL
```

### 2. 认证失败

**症状**：401 Unauthorized 错误

**原因**：AUTH_TOKEN 无效或过期

**解决**：更新 token 或检查配置文件

### 3. 模型不存在

**症状**：模型相关错误

**原因**：模型映射配置错误

**解决**：
```bash
# 检查模型配置
echo $ANTHROPIC_DEFAULT_SONNET_MODEL

# 或使用默认模型（不设置环境变量）
```

## 完整示例

```bash
# 1. 加载环境变量
export ANTHROPIC_BASE_URL=$(jq -r '.env.ANTHROPIC_BASE_URL' ~/.claude/settings.json)
export ANTHROPIC_AUTH_TOKEN=$(jq -r '.env.ANTHROPIC_AUTH_TOKEN' ~/.claude/settings.json)

# 2. 验证配置
echo "API: $ANTHROPIC_BASE_URL"

# 3. 运行测试
uv run ./scripts/main.py test "分析 Python 文件" -m sonnet

# 4. 测试 task skill
uv run ./scripts/main.py test "/task:explore 了解项目结构" -m sonnet -v
```

## 保存配置

将环境变量添加到你的 shell 配置文件（如 `~/.zshrc` 或 `~/.bashrc`）：

```bash
# 添加到 ~/.zshrc
cat >> ~/.zshrc << 'EOF'

# Task 插件测试环境
export ANTHROPIC_BASE_URL="https://your-api-endpoint.com"
export ANTHROPIC_AUTH_TOKEN="your-token"
EOF

# 重新加载配置
source ~/.zshrc
```
