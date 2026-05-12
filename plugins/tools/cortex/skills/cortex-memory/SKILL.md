---
name: cortex-memory
description: 记忆 CRUD — URI 寻址 (L0-L4) + frontmatter 版本控制。触发: "记忆写入" / "memory write" / "memory read" / "记忆更新" / "记忆删除"。
disable-model-invocation: false
allowed-tools: Bash Read Write Edit Glob mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_append_content
---

# cortex-memory

通过 URI 对 `记忆/L0-L4` 下的记忆条目执行 CRUD; 维护 frontmatter (weight/recall_count/last_recalled/parents/children/uri/level)。

## 触发场景
- 用户/AI 显式要求写入/读取/更新/删除一条记忆 (含 URI 或描述)
- 其他 skill (cortex-recall, cortex-consolidate, cortex-promote) 内部调用做读写

## 输入
- verb: `read` / `write` / `update` / `delete`
- uri: `L<N>://<path>` (e.g. `L2://semantic/go/goroutine`)
- 仅 write/update 需: content (markdown body), --level, --weight (0.0-1.0), --recall_when (string), --ref (知识库路径), --parents, --children
- 可选: --full (read 时返回完整 full: 字段, 默认仅 brief)

## URI 解析
URI scheme: `L<N>://<sub>/<path>` → 文件系统映射:
```
L0://<key>                    → 记忆/L0-核心/<key>.md
L1://procedural/<skill>       → 记忆/L1-长期/procedural/<skill>.md
L1://semantic-stable/<topic>  → 记忆/L1-长期/semantic-stable/<topic>.md
L2://semantic/<topic>         → 记忆/L2-中期/semantic/<topic>.md
L3://episodic/<date>/<slot>   → 记忆/L3-短期/episodic/<date>/<slot>.md
L4://ledger/<date>            → 记忆/L4-流水账/ledger/<date>.jsonl
L4://session/<cli>/<sid>      → 记忆/L4-流水账/sessions/<cli>/<YYYY-MM>/<sid>.md
```
- 解析失败 (uri 非法 / 路径含 `..` `/` `\` NUL) → 立即拒绝, 输出 `unsafe segment`
- 最终路径 `resolve().relative_to(vault)` 校验, 防 path escape

## 流程

### read
1. 解析 URI → 文件路径
2. 不存在 → 输出 `not found` + 候选 (Glob 同 level 目录 fuzzy match)
3. 读 frontmatter + brief; --full 时附 full
4. **不**更新 recall_count (该字段由 cortex-recall 维护, read 是直接寻址)

### write
1. 解析 URI → 路径
2. 已存在 → 拒绝 (write 仅创建新条目, 改用 update)
3. 读 `_meta/memory-policy.yaml` 校验 level write 策略:
   - L0: 必须 `needs_user_confirm=true` → 强制走 cortex-promote 流程, 拒绝直接 write (AUTO_MODE 也拒)
   - L1: `min_weight >= 0.8` 否则拒
   - L2: `min_weight >= 0.5` + dedupe (Glob 同 semantic/ 模糊查重)
   - L3/L4: auto / append_only
4. 写 frontmatter: `uri, level, weight, recall_when, ref, parents, children, created=now, last_recalled=null, recall_count=0, expires (按 policy)`
5. 写 brief + full 双段
6. 更新 `_meta/uri-index.json` (append 新 URI)

### update
1. 解析 URI → 读现有 frontmatter
2. 不存在 → 拒绝
3. L0/L1 的 immutable_after_confirm 字段拒改 (uri/level/created)
4. 允许改: weight, recall_when, brief, full, parents, children
5. recall_count++, last_recalled=now (仅 cortex-recall 调用时)
6. 写回, 保留 `created` 不变

### delete
1. 解析 URI
2. L0: 拒绝 (forget.never=true)
3. L1: 拒绝自动删, 输出 "L1 仅用户显式删, 请加 --force-user" (AUTO_MODE 一律拒)
4. L2/L3/L4: 设 `archive_pending=true` (不真删), 交 memory-archive cron 月度执行
5. 更新 `_meta/uri-index.json` 移除条目

## 输出
```
[memory:read] L2://semantic/go/goroutine
  level: L2  weight: 0.7  recall_count: 12  last_recalled: 2026-05-12T10:30:00Z
  ref: 知识库/领域/技术/编程语言/Go/goroutine.md
  brief: Go 并发用 goroutine + channel, GMP 调度模型
  (use --full for body)
```
write/update/delete 类似, 单行结果 + 落盘路径。

## 错误处理
- URI 非法 → 拒绝, 不写盘
- 路径越界 (resolve().relative_to(vault) 抛) → 拒绝
- policy 校验失败 → 输出 policy 规则 + 拒绝原因
- frontmatter 解析失败 → 输出 corrupted, 不写

## 记忆级别速查 (详见 `_meta/memory-policy.yaml`)

| level | 边界 | 审批 | review |
|-------|------|------|--------|
| L0 | 性格/价值观/硬约束, ≤1500c, 不可逆 | user 必审 + git tag | monthly hash 检测 |
| L1 | 技能/稳定语义, ≤5000c, recall≥20+90 天稳定 | AI 自动 w≥0.8 | monthly 矛盾告警 |
| L2 | 语义, ≤3000c, 365 天时效 | AI dedupe | monthly 365 天衰减 |
| L3 | 情节, ≤2000c, 90 天时效 | AI 自动 | weekly 同事件 ≥5 抽象 L2 |
| L4 | ledger/sessions, append-only | 系统自动 | weekly 30 天 gzip 60 天归档 |

写入前按 level 校验: L0 拒自动写; L1 weight 须 ≥0.8; L2 必 dedupe; L3 无 dedupe; L4 仅 append。

## 写入时 Frontmatter 自动填

write level=L<N> 时, 调 cortex-schema `read 记忆/L<N>-<name>/` 取 schema, 自动填 uri/level/weight/recall_when/created, tags 含 memory/L<N> + memory/<type>。例:

- write `L1://procedural/git-flow` → frontmatter: uri / level:L1 / weight / recall_when / created, tags: [memory/L1, memory/procedural]
- write `L2://semantic/go/goroutine` → frontmatter: 上述 + expires, tags: [memory/L2, memory/semantic]

schema 源: `<vault>/_meta/frontmatter-schema.yaml` `namespaces.记忆.*`。缺字段时 policy validator 拒写, lint 后续报 frontmatter-schema-violation。

## AUTO_MODE 兼容
若上下文标 `[AUTO_MODE: ...]`, 跳过所有交互, 用 policy 默认值决策。L0 write/delete 与 L1 delete 在 AUTO_MODE 下一律拒绝, 输出候选清单提示用户跑 `~/.cortex/scripts/memory.sh <verb> <uri> --interactive`。

## AUTO_MODE 行为 (wrapper 调用)

当 prompt 含 `[AUTO_MODE]` (来自 `~/.cortex/scripts/memory.sh`):

1. **不调** AskUserQuestion (wrapper allowed-tools 已禁此工具, 强行调用必失败)
2. 任何需用户决策处 → 走 policy 默认值跳过
3. fail-fast: 任何 error 立即返回错误码 + 简短消息
4. 特殊拒绝: L0 write/delete 与 L1 delete 在 AUTO_MODE 下一律拒绝, 输出候选清单, 提示用户跑 `~/.cortex/scripts/memory.sh <verb> <uri> --interactive`
