---
description: 更新 ccplugin-market + cortex plugin 到最新版 (无入参)
---

# /cortex:update

[AUTO_MODE strict: 禁询问, fail-fast]

更新 cortex plugin 到最新版本。

**必须**用 Bash 工具按序执行:

```bash
claude plugins marketplace update ccplugin-market
claude plugins update cortex@ccplugin-market
```

报告各命令 exit code + stdout 摘要。
