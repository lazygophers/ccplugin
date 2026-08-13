# jsonl 上下文清单 Curate

`implement.jsonl` / `check.jsonl` = sub-agent dispatch 时的 spec + research 上下文清单。每行一个 entry。

## 时机

planning 阶段最后一步, `task.py start` 前。dispatch sub-agent 时这两个文件直接被消费。

## Entry 格式

每行严格 JSON, 一行一 entry:

```json
{"path": "<相对路径>", "purpose": "<为何需要>", "phase": "implement | check"}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `path` | ✓ | 相对项目根的路径; 必须真实存在 |
| `purpose` | ✓ | sub-agent 读它做什么; ≤ 60 字 |
| `phase` | ✓ | implement / check (与文件名对应) |

## 该登记什么

| 类型 | implement.jsonl | check.jsonl |
| --- | --- | --- |
| `.trellis/spec/**` 内的硬规 / 契约 / 命令式条款 | ✓ 与本任务相关的 | ✓ 同 |
| `.trellis/tasks/<active>/research/**` 调研报告 | ✓ 实施时要参考的 | 通常 ✗ |
| 项目级 lint / test / build 约定文档 | ✓ | ✓ |
| 跨包接口契约文档 | ✓ | ✓ |

## 不该登记

- 代码文件 (`src/**` / `packages/**`) — sub-agent 自己 grep / read
- `prd.md` / `design.md` / `implement.md` — dispatch 时自动按顺序读入, 不必重登记
- 整个 spec 目录 — 选与本任务相关的, 不要全塞
- README / CHANGELOG / docs/ 大目录 — 选具体文件

## 验证

curate 完跑:

```bash
# 所有 path 必须存在
while IFS= read -r line; do
  p=$(echo "$line" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['path'])")
  [ -f "$p" ] || echo "MISSING: $p"
done < .trellis/tasks/<active>/implement.jsonl
```

无 MISSING 输出 → OK。

## 双文件差异

`check.jsonl` 通常少于 `implement.jsonl`, 因为 check 阶段只需 quality spec + 验收方法, 不需要全部 implement 时参考的资料。常见 check entries:

- lint / test 约定
- code review 清单
- 跨层一致性检查方法
- 验收命令文档

