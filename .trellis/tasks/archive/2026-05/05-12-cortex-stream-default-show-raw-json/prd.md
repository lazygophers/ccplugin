# PRD — cortex_stream default 显原 JSON, 加全 type 处理

## User 要求

> 不同的类型只需要提取给用户看的告诉用户现在在做什么。**只有 default 的分支才输出原始的 json**。

意思:
- 适配 type → 提取关键信息显友好
- 未适配 → 显原 JSON (不 silent)

## 现状

cortex_stream.py default = `None` (silent) 除非 `CORTEX_STREAM_DEBUG=1`。不符合 user 要求 (default 应显示)。

## 目标

调整 default 分支:
- 已适配 type/subtype → 友好渲染
- 未适配 → 显原 JSON 1 行 (压缩, 非 silent)
- 不依赖 CORTEX_STREAM_DEBUG

加更多 type handler 减少 default fallback:

### system.* subtypes (Claude Code 文档 + 实测)
| subtype | 显示 |
|---------|------|
| init | ▸ claude 启动 (model · tools · mcp · plugins) |
| api_retry | ⟳ api retry N/M, in Xms (err) |
| plugin_install | ▸ plugin <name> <status> |
| hook_started | ▸ hook <name> (<event>) |
| hook_response | ✓/✗ hook <name> (exit/outcome) |
| task_started | ▸ task <desc> |
| task_notification | ✓ task <desc> (status) |

### assistant.* / user.* / result (已有)

### stream_event silent (主流 assistant.text 渲)

### default (未识别 type 或 subtype) → 显原 JSON 紧凑 1 行
```python
return Text(json.dumps(event, ensure_ascii=False)[:200] + "...", style="dim white")
```

## 实施
1. cortex_stream.py default 改 silent → raw JSON 紧凑
2. 移除 CORTEX_STREAM_DEBUG opt-in 逻辑 (default 直接显)
3. 真测看输出
4. marketplace 同步

## 验收
- [ ] 未适配 type 默认显原 JSON 紧凑 1 行
- [ ] 适配 type 显友好
- [ ] 286+ tests PASS
- [ ] marketplace 同步
