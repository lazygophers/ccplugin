---
name: cortex-ingest-bulk
description: 批量摄取 urls.txt 到 cortex vault, 循环调 mcp__cortex__cortex_ingest_url。Triggers on "批量摄取", "bulk ingest".
allowed-tools: Read Bash mcp__cortex__cortex_ingest_url
---

# cortex-ingest-bulk

读 urls.txt 后逐行调用 `mcp__cortex__cortex_ingest_url`, 失败行写 `urls.txt.failed`。

## 触发场景

- 用户给 `urls.txt` 路径并说 "批量摄取" / "bulk ingest"
- `/cortex:ingest-bulk <path/to/urls.txt>` 显式调用

## 输入信号

- 必填: `urls.txt` 文件路径 (绝对或相对)
- 可选 `--kind concept|domain|log` (默认 `log`)
- 可选 `--tags tag1,tag2` 应用到全部条目

## 工作流

1. `Read` urls.txt
2. 解析: 去空行, 去 `#` 开头注释, 去前后空白
3. 串行 (并发 ≤ 1, 避免 hot/index 写竞争) 逐行调:

   ```
   mcp__cortex__cortex_ingest_url({"url": "<line>", "kind": "log"})
   ```

4. 任一行抛 ValueError/RuntimeError 即记入失败列表 (不中断后续行)
5. 写 `<urls.txt>.failed` (每行 `<url>\t<reason>`)
6. 汇总输出: 成功数 / 失败数 / 失败文件路径

## 失败分类

- `url_security rejected` → SSRF 拒, 不重试
- `http error 4xx/5xx` → 不重试 (用户判断)
- `url error` (DNS / 超时) → 重试 1 次
- `unsupported Content-Type` / `extracted body is empty` → 记 failed

## 与 cortex-ingest 关系

- 单条 URL/文件 → 用 `cortex-ingest` (调 `mcp__cortex__cortex_ingest_url` / `cortex_ingest_file`)
- 批量 URL → 本 skill
- 批量本地文件 → 用 `cortex-ingest` 配 Glob

## 注意

- 不并发: cortex_save 内部有 flock 但 hot.md/index.md patch 仍可能 race
- MCP 未装时, 退回到 cortex-ingest skill 单条循环 (用 WebFetch + defuddle)
