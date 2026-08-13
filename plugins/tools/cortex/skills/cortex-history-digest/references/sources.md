# sources — Claude Code transcripts 数据源

> 描述 `~/.claude/projects/**/*.jsonl` 目录结构 + 单条 jsonl 消息 schema. parser 据此抽取学习增量.

## 目录结构

```
~/.claude/projects/
├── -Users-luoxin-persons-lyxamour-ccplugin/        项目 1 (路径转 slug: / → -)
│   ├── <session-uuid-1>.jsonl                       一次 session 全部消息
│   ├── <session-uuid-2>.jsonl
│   └── memory/                                       (非 transcripts, skip)
├── -Users-luoxin-other-project/                     项目 2
│   └── <session-uuid>.jsonl
└── ...
```

每 `.jsonl` 文件 = 一次 Claude Code session, 每行一条 JSON 消息. scanner 按文件 mtime 排序, parser 行级解析.

## jsonl 消息 schema (已知字段)

每行一个 JSON 对象, 关键字段:

| 字段 | 类型 | 含义 | 处理 |
| --- | --- | --- | --- |
| `type` | string | `user` / `assistant` / `tool_use` / `tool_result` / `system` | 路由解析分支 |
| `role` | string | 同 type (部分版本冗余) | 兜底 |
| `content` | string \| array | 文本 (string) 或多段 (array of `{type, text}` / `{type, tool_use_id, ...}`) | 提取 text 段 |
| `timestamp` | string (ISO 8601) | 消息时间 | 增量游标 + 抗遗忘度 |
| `uuid` | string | 消息唯一 ID | 去重 |
| `parentUuid` | string \| null | 父消息 ID (对话树) | 重建上下文 (可选) |
| `sessionId` | string | session UUID | 关联文件名 |
| `cwd` | string | session 工作目录 | 项目识别 (路径反向 slug) |
| `gitBranch` | string | session 起始分支 | 元数据 |
| `model` | string | assistant 模型名 | 元数据 (可选) |

## content 形态

**string 形态** (老版本 / 简单消息):
```json
{"type":"user","content":"修改后请跑测试","timestamp":"2025-06-09T10:00:00Z"}
```

**array 形态** (新版本 / 含工具调用):
```json
{"type":"assistant","content":[
  {"type":"text","text":"我会先读文件"},
  {"type":"tool_use","id":"toolu_01","name":"Read","input":{"file_path":"..."}}
],"timestamp":"..."}
```

parser 必须两种都支持: string 直用; array 遍历 `{type:"text"}` 段拼接, 其他 type 段跳过.

## 反例 (skip)

| 情况 | 处理 |
| --- | --- |
| 非 `.jsonl` 后缀 (e.g. `.json` / `.log`) | skip |
| 行非合法 JSON (parse error) | skip + warn (log 行号) |
| 缺 `type` 字段 | skip + warn |
| `type` 不在已知集合 | skip (但不 warn, 容忍未来扩展) |
| content 既非 string 也非 array | skip + warn |
| 空 session (0 user 消息) | skip |
| `memory/` / `todos/` / `shell-snapshots/` 等子目录 | skip (非 transcripts) |

## 增量游标

`--since YYYY-MM-DD` 过滤 `timestamp >= since` 的消息. 默认全量 (无游标).

后续 task 可引入 `~/.cortex/.wiki/.cursors/history-digest.json` 存上次扫描的 `(file, last_mtime, last_uuid)` 三元组实现真增量, 本 task 不实现.

## 注意

- 路径 slug 反推: `-Users-luoxin-x-y` → `/Users/luoxin/x/y`, 用于识别 transcripts 所属项目 (用于 metadata, 不影响路由 — history-digest 落点恒为全局)
- jsonl 文件可能很大 (单 session 上万行), parser 流式读取 (逐行 yield), 不一次 load 全文
