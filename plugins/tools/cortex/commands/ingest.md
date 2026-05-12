---
description: 摄取源 (url/file/git/dir) 到 cortex vault — 处理 inbox urls (无入参)
---

# /cortex:ingest

[AUTO_MODE strict: 禁询问, fail-fast]

摄取外部源到 cortex vault。

1. 从 `~/.cortex/config.json` 读 vault
2. **若 wrapper 无入参调用 (默认)**: 读 `inbox/urls.txt` (一行一 URL) 全部处理:
   - 按 cortex-ingest SKILL 流程: url_security → fetch → html_sanitize → masking → save (kind=log)
   - 处理完追加到 `inbox/.processed-urls.log`
3. 若有显式 args: auto-detect url/file/git/dir 直接摄取

输出: 摄取条数 + 失败条数 + 各源路径。
