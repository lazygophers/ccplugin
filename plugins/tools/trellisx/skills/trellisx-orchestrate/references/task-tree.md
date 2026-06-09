# Parent / Child Task Tree

1 task 含 ≥ 2 独立可验收 deliverable → 拆 parent + 多 child。Parent 持源需求集 + task map + 跨 child 验收 + 集成 review; child 持单 deliverable 完整生命周期 (plan / impl / check / archive)。

## 何时拆

| 信号 | 决策 |
| --- | --- |
| PRD 列 ≥ 2 deliverable 且各自可独立交付 | 必拆 |
| 单 deliverable 但内部模块 ≥ 5 个 | 不拆, 走 implement.md subtask |
| 不同 deliverable 共享 ≥ 80% 代码改动 | 不拆 (强行拆制造耦合) |
| 不同 deliverable 验收方式 / 时间窗 / owner 不同 | 必拆 |

## 不要把 parent 当依赖系统

Parent / child 是组织结构, 不是依赖关系。child 之间若有顺序: **在 child 的 prd.md / implement.md 内写依赖**, 不要靠目录树位置隐含。

## 操作 (trellis 命令)

```bash
# 新建 child (推荐)
python3 ./.trellis/scripts/task.py create "<child-title>" --slug <name> --parent <parent-dir>

# 关联已存在 task 为 child
python3 ./.trellis/scripts/task.py add-subtask <parent> <child>

# 解除 (错关时)
python3 ./.trellis/scripts/task.py remove-subtask <parent> <child>
```

## Parent task 内容

Parent 的 `prd.md` 必含:

```markdown
## Child Task Map

| Child | Slug | 交付物 | 验收 | 状态 |
| --- | --- | --- | --- | --- |
| C1 | <slug> | <D1 from parent PRD> | <如何独立验收> | planning / in_progress / done |

## 跨 Child 验收

- [ ] C1 + C2 集成场景 X
- [ ] C1 数据被 C2 正确消费
- [ ] 整体性能 / 兼容性指标

## 集成 Review

- 在所有 child 完成后, parent 跑一次端到端 review
- Review 命令: <列出>
```

Parent 通常**不直接**做 implementation 工作, 除非也有非 child 范围的直接交付 (e.g. 整体重构的脚手架)。

## Child task 内容

每个 child 独立的 prd / design / implement, 仿佛它是顶层 task。差别仅:
- `task.json` 含 parent 指针 (由 task.py 维护)
- child PRD 头部一句话引 parent 上下文: `Parent: <parent-slug> — <parent 目标摘要>`

## 拆分自检

- [ ] 每个 child 可独立 task.py start / complete
- [ ] 每个 child 验收不依赖其他 child 同步进度
- [ ] child 间依赖在 child 自己的 prd / implement 里写明 (不靠目录隐含)
- [ ] parent PRD 含 child map 表 + 跨 child 验收
- [ ] parent 知道自己是否要做直接工作 (默认不做)

