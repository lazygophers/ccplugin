# Loop Prompt Caching 使用指南

## 核心原理

Claude API Prompt Caching 将静态提示词缓存，实现 **90% 成本节省**和 **85% 延迟降低**。

| 操作 | 成本倍数 | 说明 |
|------|---------|------|
| 写入缓存 | 1.25x | 首次缓存 |
| 缓存命中 | 0.1x | 90%节省 |
| 未缓存 | 1.0x | 基准 |

最小缓存块：Haiku=4096 tokens, Sonnet/Opus=1024 tokens。TTL：标准5分钟，扩展1小时。

## 缓存友好设计

loop/SKILL.md 和 planner/SKILL.md 已标记 `<!-- STATIC_CONTENT -->` / `<!-- /STATIC_CONTENT -->` + `<!-- DYNAMIC_CONTENT -->` 区域。

## 最佳实践

**必须**：
- 静态内容保持不变（不加时间戳/随机数）
- 确保缓存块≥最小token要求
- 静态/动态内容分离(system=静态, user=动态)

**禁止**：
- 在静态区域嵌入动态变量
- 频繁修改静态内容
- 添加/删除MCP工具(破坏缓存)

## 监控

从API response的usage字段提取：cache_creation_input_tokens(写入) + cache_read_input_tokens(命中) + input_tokens(未缓存)。命中率=cache_read/(cache_read+input)。

## 注意事项

1. Claude Code skills框架可能不直接支持cache_control API，当前通过文档结构优化准备
2. 清晰的静态/动态分离本身提升可维护性
3. 需要Claude API 2024-07-15+
