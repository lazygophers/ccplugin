# trellisx 批量收尾 skill 方案（trellisx-reap）

> 状态：调研完成 + 方案待审批。**未执行**。

## 1. 调研结论（脚本真实性核实）

用户曾担心 sub-agent 写入的脚本是"渲染过、实际为空"。**核实为假象**：

- 5 个脚本均有真实字节与可用逻辑（finish 12KB/214 非空行，worktree 3.8KB/64，taskmd 14KB/351，_wt 3.7KB/80，packages 7.3KB/155）。
- 非 ASCII 行（18–82/文件）是**中文注释**，非 box-drawing 污染。
- 之前 AST 把 worktree.py 判为"1 真实语句"是误判——其逻辑在**模块级顶层**而非函数内。
- "读取为空"是 Read 工具对**大文件 + 大量非 ASCII** 的显示假象，非文件真空。

## 2. 现有能力盘点（复用基础）

| 脚本 | 能力 | 与三需求关系 |
| --- | --- | --- |
| `task.py archive <name> [--no-commit]` | 单任务归档，触发 `after_archive` hook 级联 | 需求②核心 |
| `after_archive` hook → `trellisx-worktree.py archive` | 仅当 worktree **干净 + 分支已合并**(`merge-base --is-ancestor`)才销毁 worktree+删分支，否则保留 | 需求①（安全） |
| `trellisx-taskmd.py sync archive`（hook 内） | 置"已完成/收尾/100%"，跑 `cleanup(7)`，删 worktree↔task 映射 | 需求③（部分） |
| `trellisx-taskmd.py cleanup --days N` | 删除超 N 天的"已完成"看板行 | 需求③核心 |
| `trellisx-finish.py --task <tid> --dry-run` | 单任务 commit→merge --no-ff→archive→销 worktree。**无批量 flag** | 参考（非直接复用） |
| `task.py list --status completed` | 按状态筛选任务 | 枚举来源 |

**关键发现**：`task.py archive` 已通过 hook 级联完成"销已合并 worktree + 删 board 行 + 清映射"。批量 skill 主要是**枚举 + 逐个 archive + 兜底清扫**，无需重写 git 逻辑。

## 3. 完成判定（用户已确认：completed ∪ merged）

- **completed**：`.trellis/tasks/*/task.json` status == `completed`。
- **merged**：worktree 干净且分支已 merge 回主分支（即使 task.json 未置 completed）。复用 worktree.py 的 `merge-base --is-ancestor` 判据。
- 取**并集**：两类都纳入批量收尾。

## 4. 方案：薄编排 skill（不重写 git 逻辑）

新 skill `trellisx-reap`（建议名，"收割"=批量收尾），SKILL.md 驱动 + 一个薄脚本 `trellisx-reap.py`。

### 流程（三段，强制 dry-run → 确认 → 执行）

```
阶段0 枚举：
  - task.py list --status completed → completed 集
  - 扫 map-list 的 worktree，对每个跑 merge-base --is-ancestor 判 merged → merged 集
  - 并集去重，排除当前 active task（防销正在用的）

阶段1 dry-run（默认，只读）：
  - 打印将 archive 的任务、将销的 worktree、将删的 board 行
  - 不改任何状态

阶段2 确认：AskUserQuestion 列清单，用户批准才进阶段3

阶段3 执行：
  - 逐个 task.py archive <tid>（hook 级联销 merged worktree + 删 board 行 + 清映射）
  - 兜底：taskmd.py cleanup --days 0（清掉 hook 未覆盖的旧"已完成"行）
  - 孤儿 worktree 清扫：map 中存在但 task 已不存在 / 已合并未销的，逐个走 worktree.py archive 逻辑
  - 末尾 taskmd.py lint 校验看板合规
```

### 安全护栏（硬约束）

- 默认 **dry-run**，执行需显式确认（AskUserQuestion，非纯文本）。
- worktree 销毁**完全沿用** worktree.py 既有判据（脏树/未合并→保留），**不新增**强删路径。
- 当前 active task 永不纳入。
- archive 默认走 `task.py archive`（带 auto-commit）；如不想逐个 commit，用 `--no-commit` 由 skill 末尾统一提交。

## 5. 需落地的产物

1. `skills/trellisx-reap/SKILL.md` — 描述前置关键词"批量/清理/归档/收尾"，驱动三段流程。
2. `scripts/trellisx-reap.py` — 薄编排：枚举 completed∪merged、dry-run 报告、逐个 archive、兜底 cleanup --days 0、孤儿清扫、lint。
3. `.claude-plugin/plugin.json` — 注册新 skill 到 skills 列表。
4. 质检：`claude -p "<SKILL.md 内容>" --output-format stream-json | jq ...` 验证 AI 正确识别触发场景。

## 6. 已确认决策（用户拍板）

- **skill 名**：`trellisx-cleanup`（覆盖前文 trellisx-reap，全文以此为准）。
- **board 清理**：`cleanup --days 0`，全删"已完成"行。
- **提交方式**：逐个提交（`task.py archive` 默认行为，每任务一 commit）。
