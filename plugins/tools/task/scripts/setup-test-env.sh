#!/bin/bash
# 从 Claude Code 配置加载测试环境变量

CONFIG_FILE="${1:-$HOME/.claude/settings.json}"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ 配置文件不存在: $CONFIG_FILE"
    echo ""
    echo "用法: source $0 [配置文件路径]"
    echo "示例: source $0 ~/.claude/settings.glm.json"
    exit 1
fi

echo "从配置加载环境变量: $CONFIG_FILE"
echo ""

# 加载主要环境变量
export ANTHROPIC_BASE_URL=$(jq -r '.env.ANTHROPIC_BASE_URL // empty' "$CONFIG_FILE")
export ANTHROPIC_AUTH_TOKEN=$(jq -r '.env.ANTHROPIC_AUTH_TOKEN // empty' "$CONFIG_FILE")

# 可选：模型映射
export ANTHROPIC_DEFAULT_SONNET_MODEL=$(jq -r '.env.ANTHROPIC_DEFAULT_SONNET_MODEL // "sonnet"' "$CONFIG_FILE")
export ANTHROPIC_DEFAULT_OPUS_MODEL=$(jq -r '.env.ANTHROPIC_DEFAULT_OPUS_MODEL // "opus"' "$CONFIG_FILE")
export ANTHROPIC_DEFAULT_HAIKU_MODEL=$(jq -r '.env.ANTHROPIC_DEFAULT_HAIKU_MODEL // "haiku"' "$CONFIG_FILE")

# 其他相关变量
while IFS= read -r key; do
    # 跳过已处理的变量
    if [ "$key" = "ANTHROPIC_BASE_URL" ] || [ "$key" = "ANTHROPIC_AUTH_TOKEN" ] || \
       [ "$key" = "ANTHROPIC_DEFAULT_SONNET_MODEL" ] || [ "$key" = "ANTHROPIC_DEFAULT_OPUS_MODEL" ] || \
       [ "$key" = "ANTHROPIC_DEFAULT_HAIKU_MODEL" ]; then
        continue
    fi

    value=$(jq -r ".env.\"$key\"" "$CONFIG_FILE")
    if [ "$value" != "null" ] && [ -n "$value" ]; then
        export "$key=$value"
    fi
done < <(jq -r '.env | keys[]' "$CONFIG_FILE" 2>/dev/null || true)

# 验证必需的变量
if [ -z "$ANTHROPIC_BASE_URL" ] || [ -z "$ANTHROPIC_AUTH_TOKEN" ]; then
    echo "⚠️  警告: 缺少必需的环境变量"
    echo ""
    if [ -z "$ANTHROPIC_BASE_URL" ]; then
        echo "  ❌ ANTHROPIC_BASE_URL 未设置"
    fi
    if [ -z "$ANTHROPIC_AUTH_TOKEN" ]; then
        echo "  ❌ ANTHROPIC_AUTH_TOKEN 未设置"
    fi
    echo ""
    echo "请检查配置文件中的 env 字段"
    exit 1
fi

echo "✅ 环境变量已加载:"
echo "  ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
echo "  ANTHROPIC_AUTH_TOKEN: ${ANTHROPIC_AUTH_TOKEN:0:20}..."
if [ -n "$ANTHROPIC_DEFAULT_SONNET_MODEL" ]; then
    echo "  ANTHROPIC_DEFAULT_SONNET_MODEL: $ANTHROPIC_DEFAULT_SONNET_MODEL"
fi
if [ -n "$ANTHROPIC_DEFAULT_OPUS_MODEL" ]; then
    echo "  ANTHROPIC_DEFAULT_OPUS_MODEL: $ANTHROPIC_DEFAULT_OPUS_MODEL"
fi
if [ -n "$ANTHROPIC_DEFAULT_HAIKU_MODEL" ]; then
    echo "  ANTHROPIC_DEFAULT_HAIKU_MODEL: $ANTHROPIC_DEFAULT_HAIKU_MODEL"
fi
echo ""
echo "现在可以运行测试:"
echo "  uv run ./scripts/main.py test \"测试提示词\""
echo "  uv run ./scripts/main.py test \"/task:explore 了解项目结构\" -v"
