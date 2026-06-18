---
description: 查看当前 notify 通知插件的配置
allowed-tools: Bash(uv run *)
---

运行以下命令查看 notify 插件的当前通知配置, 并把输出原样展示给用户:

```bash
uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py config
```
