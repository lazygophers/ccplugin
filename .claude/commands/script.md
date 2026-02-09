---
name: script
description: 开发插件 Python CLI 脚本
argument-hint: <plugin-name>
---

# script

为插件开发 Python CLI 脚本。

## 使用方法

```bash
/script my-plugin
```

## 脚本结构

- `scripts/main.py` - CLI 入口
- `scripts/hooks.py` - 钩子处理
- 使用 Click 构建命令
