# Spec 提案 (阶段 2)

按变更类型分类列变更, **不写盘**。每条变更含: 类型 / 文件 / 旧片段 / 新片段 / 影响面 / 风险。

## 变更类型表

| 标识 | 含义 | 示例 |
| --- | --- | --- |
| `NEW` | 新建文件 (init / sediment 常用) | `core-contracts.md` 首版 |
| `DELETE` | 整文件 / 整节删除 | `legacy-x.md` 全删 — 引用已迁移 |
| `REWRITE` | 同名文件破坏式重写 | `code-reuse-thinking-guide.md` 从思考流改为 5 条 MUST 清单 |
| `MERGE` | N → 1 合并 | `cross-layer-thinking-guide.md` + `code-reuse-thinking-guide.md` 合并为 `core-contracts.md` |
| `SPLIT` | 1 → N 拆分 | `index.md` 拆为 `index.md` + `triggers.md` |
| `EXTRACT` | 内联 → 引用 | spec 抄了外部规则, 本地仅留 `参见: <相对路径>#锚点` |
| `PATCH` | 非破坏式微调 (修死链 / 改个词) | 不需审批门, 可直接归一批走 |

## 每条变更必含

```markdown
### 变更 #<N> · <类型> · <目标文件>

**旧版关键片段** (≤ 5 行):
```
<原文>
```

**新版关键片段** (≤ 5 行):
```
<新文>
```

**影响面**:
- 被以下 task 引用 (grep `implement.jsonl` / `check.jsonl`):
  - `.trellis/tasks/<task1>/implement.jsonl` (path 字段命中)
  - `.trellis/tasks/<task2>/check.jsonl`
- 被以下 spec 文件交叉引用:
  - `.trellis/spec/guides/other.md#锚点`
- 与外部已加载文档关系:
  - 重复 / 引用 / 独立

**风险**:
- 已 dispatch 的 sub-agent prompt 缓存是否会读到旧引用
- 文件改名 / 删除是否需要同步 task manifest (列具体文件)
- 是否破坏现有 task in_progress 的预期 (列任务名)

**理由**:
<为何这样改, 一句话>
```

## 提案输入来源 (按模式)

| 模式 | 输入 |
| --- | --- |
| init | `references/init-mode.md` 首版模板 + 用户给的项目特定要求 |
| optimize | `references/diagnose.md` 输出的提案候选 |
| sediment | `references/sediment-mode.md` 描述的"本任务学习" + active task 的 prd/design/implement/journal |

## 命令式重写

REWRITE 提案的新版必须遵守 `rewrite-style.md` 的命令式范本。

## 影响面计算

```bash
# 给一个 spec 文件名, 列引用它的 task manifest
TARGET="guides/code-reuse-thinking-guide.md"
for f in .trellis/tasks/*/implement.jsonl .trellis/tasks/*/check.jsonl; do
    [ -f "$f" ] || continue
    grep -l "$TARGET" "$f" 2>/dev/null
done

# 列引用它的 spec 内交叉引用
grep -rn "$TARGET" .trellis/spec/ | grep -v "^${TARGET}:"
```

## 提案归一

完成全部变更列表后, 按文件聚合 (同文件多变更合一展示), 输出汇总表:

```
提案汇总
────────
共 N 项 (NEW: a, DELETE: b, REWRITE: c, MERGE: d 组, SPLIT: e, EXTRACT: f, PATCH: g)

涉及文件:
  + 新增 (NEW): <list>
  - 删除 (DELETE): <list>
  ~ 重写 (REWRITE): <list>
  ⊕ 合并 (MERGE): <list> → <target>
  ⊗ 拆分 (SPLIT): <source> → <list>
  → 抽引用 (EXTRACT): <list>
  · 微调 (PATCH): <count> 处

影响 task: <count> 个
  - <task-name>: <受影响文件列表>
```

进入阶段 3 审批。
