# io — 增量游标 + dry-run JSON + apply 行为

## 增量游标

`<target>/state/extract-cursor.json`:

```json
{
  "last_processed_mtime": 1717900000.0,
  "processed": ["<sha256>", ...]
}
```

- 每次 `--apply` 后写入
- `--no-cursor` 忽略游标 (强制全量)
- 下次扫: 仅处理 (mtime > last_processed_mtime) 且 (sha256 ∉ processed) 的条目
- 项目级游标走 `<repo>/.wiki/state/`, 与用户级游标 (`~/.cortex/state/`) 互不干扰

## dry-run 输出格式

```json
{
  "mode": "dry-run",
  "target": "/abs/path",
  "plan": [
    {
      "source": "/abs/.../L4-inbox/foo.md",
      "sha256": "abc...",
      "mtime": 1717900000.0,
      "weight": 0.5,
      "reuse_count": 1,
      "kw_hits": {"L3": ["暂时"]},
      "target": {
        "module": "memory",
        "level": "L3",
        "path": "<由 schema-* 决定>",
        "filename": "foo.md"
      },
      "reason": "L3 关键词命中: ['暂时']",
      "ask": false,
      "promote_hint": null
    }
  ],
  "skipped": [{"rel": "...", "sha256": "...", "reason": "cursor skip"}]
}
```

## apply 行为

1. 目标目录不存在则创建 (mkdir -p)
2. 同名冲突: 追加 `.1 / .2 / ...` 后缀, **不覆盖**
3. 原 inbox 文件移到 `<target>/.wiki/memory/L4-inbox/_archived/`, **不 delete** (用户可手动从 `_archived/` 恢复)
4. L0 候选: 走 `CORTEX_EXTRACT_L0_AUTO` env (accept/reject/ask). reject 时保留在 inbox, 不归档.
5. 游标更新: 写入 `last_processed_mtime` (max) + `processed` (sha256 list)

## 与其它 skill 的关系

- 路径目标定义 (单一真相): `cortex-schema-knowledge` (项目/领域/脚本 三模块) + `cortex-schema-memory` (L0-L4)
- 路径名与 level 一致性: `cortex-lint` R6 二次校验 (extract 写完跑 lint 验收)
- `target.path` 字段的取值范围由 schema-* 定义, 本文件不再硬列具体路径段
