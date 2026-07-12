# Subtask 文件

每个 subtask = `.trellis/tasks/<task>/subtask/<id>-<slug>.md` 一个文件, 独立详细描述。PRD 只放概览, subtask 文件持完整五要素 + 执行细节。

## 路径约定

```
.trellis/tasks/<task-dir>/
├── prd.md
├── design.md
├── implement.md
└── subtask/
    ├── S1-init-skeleton.md
    ├── S2-implement-auth.md
    ├── S3-add-tests.md
    └── S4-integrate.md
```

文件名规则: `<ID>-<kebab-case-slug>.md`, ID 与 PRD subtask 表一致。

## 必备结构

```markdown
---
id: S1
slug: init-skeleton
deliverable: D1
parent-task: <task-dir>
status: ready | blocked | running | done | failed
execution-layer: main | sub-agent | agent-team
isolation: task   # 默认共享 task worktree (隔离单位 = task); 多 worktree 属 opt-in
depends-on: [S0]
blocks: [S2, S3]
write-files: [<glob 列表>]   # 写盘文件 glob, 冲突判定① (两 subtask 相交 = 有依赖边)
exec-scope: none | package:<pkg> | project   # 执行作用域, 冲突判定② (none/package:pkg/project)
estimated-tokens: <数字 / 范围>
---

# S1 · <一句话标题>

## 目标
<动词 + 对象 + 结果, 可证伪>

## 产出
- <具体文件 / 路径>
- <报告章节>
- <截图 / 命令输出>

## 验证

```bash
# 完成判定命令, 复制粘贴可跑
<command 1>
<command 2>
```

期望输出:
- <command 1>: 退出码 0; stdout 含 "X"
- <command 2>: 文件 `Y` 存在且大小 ≥ N

## 资源 (冲突判定输入, 见 scheduling.md)

- **write-files** (frontmatter 已填): 写盘文件 glob 列表 — 冲突判定①, 两 subtask 相交 = 有依赖边
- **exec-scope** (frontmatter 已填): `none` / `package:<pkg>` / `project` — 冲突判定②, 包级测试=package, 项目级=project, 只读探索=none
- 端口 / 服务: `<list>` (exec-sscope 外的额外互斥)
- 环境: `.env.test` / 共享配置 / 等
- 审批槽位: 是 / 否

## 依赖

| 上游 | 需要的产出 | 等待方式 |
| --- | --- | --- |
| S0 | `<file>` 存在 | 文件检测 |

## 执行细节

<具体步骤 + dispatch 要点 (实施类 subtask 必派 agent, main 不直接写源码)>

### Dispatch Prompt (若派 sub-agent)

> 写盘 sub-agent / agent-team 都在**本 task 的 worktree 内**执行 (共享, subtask 与 worktree 无绑定), 禁在主工作区写盘。dispatch prompt **不传** `isolation: worktree` (隔离已由 task.py start 的 after_start hook 完成)。

```
Active task: <task path>
# 隔离: 共享 task worktree (task.py start 已建, 不传 isolation:worktree)

## 目标
<同上>

## 已知
- 上游产出: <files>
- 关键约束: <list>

## 工作目录与范围
- cwd: <abs path>
- 可改文件: <glob>
- 禁改文件: `**/dist/**` `**/*.generated.*` `.trellis/**`

## 输出格式
- 类型: <diff / 报告 / 命令输出>
- 行数上限: <N>

## 验收标准
<copy 上面 验证 节>

## 失败处理
- 工具瞬时错误 → 重试 1 次
- 业务阻塞 → 输出 `需要: <问题>` 并停
- 资源不可用 → 报 Blocked, 不重试

## Sub-agent 自防护
你已是 trellis-implement, 直接做本 subtask。**禁调度、禁递归、禁并行派其他 subtask**:
- 你的工具集仅 Read/Write/Edit/Bash, **无 Agent/Task 工具** (Recursion Guard), 物理上不能派 subagent / 递归 trellis-implement / trellis-check。
- **调度归 main**: 冲突判定 / 建 DAG / 动态派 (并发≤2) / 收态 / 转 check 全是 main 职责 (见 `scheduling.md`)。
- 你只执行被派的**这 1 个 subtask**, 完成即返回产物 + 自验结果, 不碰其他 subtask。
```

## 回滚

- 触发条件: <何时回滚>
- 步骤:
  ```bash
  <rollback command 1>
  <rollback command 2>
  ```

## 风险

| 风险 | 影响 | 缓解 |
| --- | --- | --- |

## 历史

- <ISO date>: created
- <ISO date>: <事件>
```

## 状态字段 (5 态, 见 scheduling.md §3)

| status | 含义 | 转移条件 |
| --- | --- | --- |
| `ready` | 无未完成依赖, 可立即派 | 所有上游 done; 资源未占用 |
| `blocked` | 有上游未 done 或资源被占用 | 初始态 (原 planned 并入); 上游未完成; exec-scope 冲突的并行 subtask 仍在跑 |
| `running` | 已派 trellis-implement, 未返回 | main 派发后 |
| `done` | trellis-implement 返回 + 自验通过 | 返回且验收命令过 |
| `failed` | 失败 / 自验不过 | 转入 failure-recovery (`failure-recovery.md`) |

> 原 `planned` 态并入 `blocked` (已写文件但依赖/资源未就绪 = blocked); 新增 `failed`。调度循环 + 冲突判定详见 `scheduling.md`。

## 同步 PRD

subtask 文件创建 / 改名 / 删除时**同步**改 PRD Subtask 拆分表 + 调度图 mermaid。两侧 ID 必须一致。

## 自检

- [ ] 每个 PRD 列的 subtask 都有对应文件
- [ ] 每个 subtask 文件含完整五要素
- [ ] frontmatter 含 `write-files` + `exec-scope` (冲突判定输入, 见 scheduling.md)
- [ ] depends-on / blocks 与 PRD mermaid 图一致
- [ ] 执行层标注与 design 一致
- [ ] 验证命令复制可跑, 不含占位 `<...>`
- [ ] 若执行层 = sub-agent, dispatch prompt 6 字段填全
- [ ] 回滚步骤可执行
