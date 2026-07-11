# 速查手册

CLI、skill、agent、command、配置、hook 一览。

## 短命令 (bin/ PATH 封装)

plugin 启用后 `bin/` 自动进 Bash tool 的 PATH (官方约定目录, 无需 plugin.json 声明), 长调用可缩为裸命令:

| 短命令 | 等价长形式 |
| --- | --- |
| `skein <cmd>` | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py <cmd>` |
| `skein-memory <cmd>` | `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory.py <cmd>` |

省 token、抗路径漂移。**仅** skill/agent 正文里的 Bash 调用可用短命令; hook 里的 `python3 ${CLAUDE_PLUGIN_ROOT}/...` 走 hook 环境 (非 Bash PATH), 保持长形式不变。下文命令表沿用长形式书写, 实操可替换为短命令。

## skein.py — 任务引擎 (main 同步跑)

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py <cmd>   # 或短命令 skein <cmd>
```

| 命令 | 参数 | 作用 |
| --- | --- | --- |
| `init` | — | 初始化 `.skein/` 工作区 (幂等, 已存在则跳过建文件)。生成 `.skein/.gitignore` (忽略 `task.md` 自动渲染) + 把 worktree_root 补到仓库根 `.gitignore` |
| `create <id>` | `--name <标题>` `--desc <文本>` `--deps "a,b"` | 登记新 task (状态 pending), 打印 `<id>\t<路径>`。`id` 必填, 人工传入的可读 slug (见下 id 规则); `--name` 省略则用 id |
| `start <id>` | — | 建 worktree + 分支, 状态 → in_progress。前置未完成 / active 超上限 2 会报错。无 focus, 就绪即可并行 |
| `finish <id>` | — | commit → merge → 销 worktree → 归档。冲突自动 abort。多 active 并行, id 必填 |
| `archive <id>` | — | 丢弃 task (销 worktree/分支, **不 merge**), 归档 |
| `current` | — | 列全部 active task (id/状态/名称/worktree)。无 focus, 就绪皆可并行 |
| `list` | — | 列全部 task (含已归档) |
| `board` | — | 渲染并打印 `.skein/task.md` 看板 |
| `session-context` | — | (SessionStart hook 调) 有 active task 时输出摘要 JSON (各 active id/status/name/worktree + 恢复提示) 注入上下文; 无 active / 非 skein 仓静默 exit 0。compaction 后恢复活跃 task 状态 |
| `contract <id>` | `--add <文本>` | `--add` 追加一条契约到 task.json `contracts` 数组; 省略 `--add` 则逐条列出。planning/grill 锁契约, check 阶段 checker 读出逐条验证 |
| `journal --id <id>` | `--add <文本>` | per-task finish 追加日志: `--add` 往 `.skein/task/<id>/journal.md` 追加一行 (append-only, 无审批门, 区别 contract/sediment); 省略 `--add` 则列出。随 task finish 一并归档 |
| `subtask <action> <tid> [sid]` | `--name` `--deps "s1,s2"` `--write "glob,glob"` `--reason` | 单 task 内 subtask DAG 调度 (存 per-task task.json 的 `subtasks[]`)。`action`: `add` 登记 / `claim` **一次性认领就绪批 (整批标 running)** / `ready` 只读预览 / `start` 单个占槽 / `done` 完成 / `fail` 失败 / `list` 列态。add/start/done/fail 必带 `sid` |

**task.json 字段**: `id / name / desc / status / deps / worktree / branch / created / updated / contracts / subtasks`。
**subtask 字段** (`subtasks[]` 内): `sid / name / depends_on / write / reason / status` (pending→running→done/failed)。
**subtask 调度环** (main 驱动): `subtask claim <tid>` 一次性认领就绪批 (整批标 running, 免逐个 start) → 逐个派 `skein-implementer` → 完成即 `subtask done/fail` → 再 `claim`。就绪 = pending + 依赖全 done + 写集与 running 无冲突, 截到空闲槽 (`max_parallel`)。**脚本算+改态一步到位, main 只派 agent** (脚本不能 spawn)。`ready` 是只读预览版 (不改态), `start` 是单个手动补派 (retry 用)。
**状态流转**: `pending → in_progress → completed` (archived 移出 `task/`)。
**id 规则**: **人工传入的可读 slug** (create 必填首参), 从 id 即可知含义 (如 `order-create-api`), 非随机生成。格式 = kebab-case (`^[a-z0-9][a-z0-9-]*$`, 小写字母/数字/连字符, 字母数字开头), 兼作 git 分支名 (`skein/<id>`) + 目录名。全局唯一, 含已归档的不可复用, 非法/重复即报错。

## memory.py — 规则记忆引擎

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory.py <cmd>   # 或短命令 skein-memory <cmd>
```

| 命令 | 参数 | 作用 |
| --- | --- | --- |
| `init` | — | 初始化 `.skein/spec/` 两层目录 |
| `session-start` | — | (SessionStart hook 调) 产出 core 规则注入 JSON |
| `inject-core` | — | 打印 core 规则正文 (供手动查看) |
| `recall <query>` | — | 按词粗筛 recall 索引, 打印命中行 (model 再读全文定用否) |
| `sediment` | `--layer core\|recall` (必) `--title` (必) `--category` `--keywords` `--source` `--body-file` | 写盘一条规则 + 自动 reindex |
| `reindex` | — | 重建三份索引 (两层 + 顶层聚合) |
| `list` | `--layer core\|recall` | 列规则文件 |

**规则文件 frontmatter**: `title / layer / category / keywords / source / authored-by / created`。
**类目 (category)**: 物理事实 = 所在子目录名 (git/test/arch/build/style/domain/ops/misc...), 自由建。
**core 预算**: 常驻注入有字符上限, 超了 sediment 会警告降级到 recall。

## Skills (6 个)

| skill | 何时用 | references |
| --- | --- | --- |
| `skein-flow` | 复杂/多步/跨文件请求, 强制 task 闭环 (自动或显式触发) + exec 双层 DAG 编排调度 | mandatory-flow-steps · scheduling-algorithm · progress-reporting |
| `skein-planning` | plan 入口: 判新旧 + 登记 + brainstorm + grill 硬门; heavy 档含破坏式重构注解 | dispatch-graph · breaking-refactor |
| `skein-memory` | recall 召回 + sediment 沉淀; 空仓冷启动播种 (一次性) | sediment-workflow · bootstrap-seeding |
| `skein-grill` | 对抗式审查需求 / 工件 (planning 硬门) | review-axes-and-output |
| `skein-check` | 质量门 (lint/type/test/契约), 未过派修; 第 3 轮 FAIL 做 5 维根因复盘 | root-cause-protocol |
| `skein-clean` | 清孤儿 worktree / 悬挂分支 / 漏归档 | anti-examples |

每个 skill 是**多文件组织**: 精简 SKILL.md 入口 + `references/*.md` 明细 (渐进式披露)。原 orchestrate / refactor / bootstrap / break-loop 4 个 skill 无独立运行时调用边, 已分别并入 flow / planning / memory / check 的 references (省常驻 description token)。

## Agents (3 个, 均无 Agent/Task 工具 = 递归护栏)

| agent | 职责 | 工具面 | 模型分层 |
| --- | --- | --- | --- |
| `skein-implementer` | worktree 内执行 1 个 subtask, 写代码 (每文件过 写前 CHECKPOINT) | 读写 + Bash, 无 Agent/Task | `effort: high` (继承主模型, 不降级) |
| `skein-checker` | 只读验证 (lint/type/test/契约合规) | 只读 + Bash, 无 Agent/Task | `model: sonnet` + `effort: medium` |
| `skein-researcher` | planning 纯信息调研 (选型/对比) + bootstrap 扫描模式 (扫既有代码库约定), 结论落盘 `research/` | 读 + 检索, 无 Agent/Task | `model: sonnet` + `effort: medium` |

> 模型分层做 token 优化: 验证 / 调研走较轻档 (sonnet + medium), 执行保持高推理 (implementer 继承主模型 + high effort)。

## Command

| command | 作用 |
| --- | --- |
| `/skein-go <任务描述>` | 强制把请求作为 SKEIN task 处理, 走 plan→exec→check→finish。调用即「建 task 同意」 |

## 配置 (`.skein/config.yaml`)

| 键 | 默认 | 作用 |
| --- | --- | --- |
| `max_active` | `2` | 同 session active task 并发上限 (= subtask 级上限) |
| `auto_commit` | `true` | finish 时自动 commit worktree 改动。设 false 则有未提交改动会拒绝 finish (防强删丢失) |
| `worktree_root` | `.worktrees` | worktree 存放根目录 (相对 git 根) |

## Hooks (`.claude-plugin/plugin.json`)

| hook | 触发 | 作用 |
| --- | --- | --- |
| **SessionStart** | 每 session 开始 | `memory.py session-start` 注入 core 常驻规则 + `skein.py session-context` 注入活跃 task 状态 (compaction 后恢复) |
| **PreToolUse** | Edit/Write/Read | `guard-skein.py` 硬阻 AI 直接读写 .skein/ 的 task.json / task.md (顶层 + per-task, 读写全挡) |

## guard-skein.py 拦截规则

判定: 路径落在 `.skein/` 下且 basename ∈ {`task.json`, `task.md`} → 读写全挡 (含归档路径)。四个文件全由 skein.py 维护, AI 取态经命令 stdout 而非读文件。

| 目标文件 | Read | Edit/Write | 替代方式 |
| --- | --- | --- | --- |
| `.skein/task.json` (顶层 tasks 全表) | 挡 | 挡 | `skein.py current` 列 active; create/start/finish 改 |
| `.skein/task.md` (顶层看板) | 挡 | 挡 | `skein.py list` / `board` 取态 |
| `.skein/task/<id>/task.json` (记录+subtask) | 挡 | 挡 | `skein.py subtask list/ready <id>`; subtask add/start/done 改 |
| `.skein/task/<id>/task.md` (子任务看板) | 挡 | 挡 | `skein.py subtask list <id>` |
| `.skein/task/<id>/{prd,implement,journal}.md` | 放行 | 放行 | planning 工件, AI 直接读写 |

## 生命周期一图速记

```
init → create(pending) → start(in_progress, +worktree)
     → [plan → exec → check] → finish(commit→merge→archive, -worktree)
                                   ↘ archive (丢弃, 不 merge)
```
