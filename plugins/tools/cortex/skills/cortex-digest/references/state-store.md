# cortex-digest — state store (`vault/.cortex/state/*.json`)

增量游标 + processed_files hash 集 + 各阶段累计 stats。每阶段独立 state 文件, 互不依赖。

## 目录

```
<vault>/.cortex/state/
├── digest.json        # 阶段 1 读 + 整体 last_run
├── consolidate.json   # 阶段 5 项目→领域 提炼
├── enrich.json        # 阶段 6 md 图表/tags 优化
└── verify.json        # 阶段 7 search 多次验证
```

是否 commit: 用户自决。推荐**不 commit** state/ (runtime 状态, 每机器独立), commit config/ (用户可调)。

## Schema (统一)

```json
{
  "schema_version": 1,
  "last_run": "<UTC ISO>",
  "processed_files": {
    "<rel_path_from_vault_root>": {
      "hash": "<sha256 hex>",
      "mtime": "<UTC ISO>",
      "phase": "<stage_name>"
    }
  },
  "cursors": {
    "inbox_last_mtime": "<UTC ISO>",
    "log_last_date": "<YYYY-MM-DD>",
    "session_last_id": "<id>",
    "last_repo_path": "<rel path of last processed repo>"
  },
  "stats": {
    "<阶段名>": <int>
  }
}
```

字段说明:

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `schema_version` | int | 是 | 当前 1; migration 时 +1 |
| `last_run` | UTC ISO | 是 | null = 从未跑 |
| `processed_files` | dict | 是 | key=vault 相对路径, value={hash,mtime,phase} |
| `cursors` | dict | 是 | 各类 mtime/id 游标; null = 全量 |
| `stats` | dict | 是 | 累计计数 (跨多次跑) |

## 阶段 cursor 字段映射

| 阶段 | state 文件 | 主要 cursor 字段 |
|---|---|---|
| 1 读 | digest.json | `inbox_last_mtime` / `log_last_date` / `session_last_id` |
| 5 整合 | consolidate.json | `last_repo_path` (按 repo 顺序遍历) |
| 6 优化 | enrich.json | `processed_files` (hash-based, 无单独 cursor) |
| 7 验证 | verify.json | `processed_files` (hash-based) |

## 读写规约

**读 (阶段开头)**:
1. 文件不存在 → 初始化空骨架 (`schema_version: 1`, `last_run: null`, `processed_files: {}`, `cursors: {}`, `stats: {}`), 视为首次跑
2. JSON 损坏 → stderr 报 warn, 备份到 `<file>.corrupt.<timestamp>`, 重建空骨架
3. `schema_version` 高于代码已知 → stderr 报 warn, 继续按代码已知 schema 读 (forward compat)
4. `state.last_run` 距今 > `incremental_max_age_days` (config, 默认 30) → 视为首次跑, **清空 processed_files**, 全量重处理

**写 (阶段结尾)**:
1. 阶段成功 → 更新 `last_run`, append `processed_files`, 更新 `cursors`, `stats.<阶段> += <new>`
2. 阶段失败 (重试 1 次仍失败) → 不写 cursor, **不写 processed_files** (下次跑重处理), 仅累加 `stats.<阶段>_failures`
3. 原子写: 先写 `<file>.tmp`, fsync, mv 替换原文件
4. 并发: 配合 `cron run.sh` flock; skill 内多阶段并发用 file_lock per file

## migration (schema_version 升级)

当代码读到 `schema_version: 1` 而代码已知 v2:
- v1 → v2: 自动迁移 (添加新字段空值, 保留既有), 写回 v2
- 反向 (v2 → v1) 不支持; 用户需手动清 state/

migration 步骤记日志到 `<vault>/_meta/migrations/<date>-state-v<old>-to-v<new>.log`。

## 失效策略

| 触发 | 行为 |
|---|---|
| 文件不存在 | 空骨架 + 全量 |
| JSON 损坏 | 备份 + 空骨架 + 全量 |
| `last_run` > 30 天 | 清 processed_files, 全量重处理 (cursors 保留作为窗口下限) |
| `schema_version` 未知 | warn + 按已知 schema 读 |
| 单文件 hash 在 state 但实际文件已删 | 阶段结束扫一遍 `processed_files` keys, 删不存在的 entry (GC) |

## 与 config 的关系

`vault/.cortex/config/digest.yaml` 影响 state 行为:

| config 字段 | 影响 |
|---|---|
| `incremental_max_age_days` | 失效阈值 |
| `stages.{consolidate,enrich,verify}: false` | 跳过该阶段, 不读写其 state |
| `domain_aliases` | 阶段 5 域名归一 (不影响 state schema) |
