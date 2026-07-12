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
| `init` | — | 初始化 `.skein/` 工作区 (幂等, 已存在则跳过建文件)。生成 `.skein/.gitignore` (忽略 `task.md`/`task.html`/`board/` 自动渲染) + 把 worktree_root 补到仓库根 `.gitignore` |
| `setup` | `--full` | 幂等初始化 + trellis 迁移。无 trellis → scaffold + 本地 spec 库。有 `.trellis/` (两模式)：<br>**兼容 (默认)** — `copytree` 独立拷 `.trellis/spec`→`.skein/spec` (trellis 零改动) + **物理迁移 task.json 与各 task 文件夹** (整体搬迁, **跳过已归档 task**) + **无条件删 trellis 接线** (`.trellis/{scripts,hooks,settings*}` + `.claude/*trellis*`, 避免 skein/trellis 双注入) + **留 `.trellis/` 数据** (spec/task 给其它工具)。<br>**`--full`** — 兼容全套 + 整删 `.trellis/` (spec/task 已拷入 `.skein`)。<br>输出 manifest JSON (纯 stdout, scaffold 噪声走 stderr): `{mode, trellis_present, spec_copied, spec_needs_reorg, trellis_tasks, wiring_removed, trellis_removed, settings_need_manual_edit}`。语义迁移 (spec 重组 + settings hook 剔除) 由 `skein-setup` agent 做 |
| `create <id>` | `--name <标题>` `--desc <文本>` `--deps "a,b"` `--estimate <分钟>` | 登记新 task (状态 pending), 打印 `<id>\t<路径>`。`id` 必填, 人工传入的可读 slug (见下 id 规则); `--name` 省略则用 id; `--estimate` = AI 执行预期耗时 (分钟), 供看板 html 显示预期 vs 实际 |
| `start <id>` | — | 建 worktree + 分支, 状态 → in_progress。前置未完成 / active 超上限 2 会报错。无 focus, 就绪即可并行 |
| `finish <id>` | — | commit → merge → 销 worktree, 状态 → completed。**完成 task 不立即归档**, 留看板 `retain_days` 天 (config, 默认 7); 超期由 `_autoclean` 在下次生命周期变更时自动归档。`retain_days=0` 时 finish 即归档 (旧行为)。冲突自动 abort。多 active 并行, id 必填 |
| `archive <id>` | — | 丢弃 task (销 worktree/分支, **不 merge**), 归档 |
| `clean` | `--days <保留天数>` | **[用户主动]** 归档完成超保留期的 task (`skein-clean` skill 入口)。`--days` 省略用 config `retain_days`; `0` = 全部完成 task 立即归档。只能比 config 更激进 (更小值), 更大值被 `_sync` 自动 ceiling 抵消 |
| `current` | — | 列全部 active task (id/状态/名称/worktree)。无 focus, 就绪皆可并行 |
| `ready` | — | **脚本算**就绪 task 批 (pending + 前置全 done + 有空闲 active 槽), 只读预览。谁可执行由脚本判 (非 AI), 与 `subtask ready` 同构; task 无写集字段故不算写集冲突 |
| `list` | — | 列全部 task (含已归档) |
| `board` | — | 渲染并打印 `.skein/task.md` 看板 |
| `view` | — | 生成 (缺则建) 并用系统默认程序打开 `.skein/task.html` 静态可视化看板 (title/标题带项目名, 多主题多配色深浅色, 页内切换器, 不自动打开) |
| `session-context` | — | (SessionStart hook 调) 有 active task → 输出摘要 JSON 注入; git 仓无 `.skein/` → 注入 setup 建议 (nudge); 非 git 仓静默 exit 0。compaction 后恢复活跃 task 状态 |
| `user-prompt` | — | (UserPromptSubmit hook 调) 每次用户 prompt 注入 task 判定提醒 (是任务则走 skein-flow 闭环); 非 git 仓静默 exit 0 |
| `contract <id>` | `--add <文本>` | `--add` 追加一条契约到 task.json `contracts` 数组; 省略 `--add` 则逐条列出。planning/grill 锁契约, check 阶段 checker 读出逐条验证 |
| `journal --id <id>` | `--add <文本>` | per-task finish 追加日志: `--add` 往 `.skein/task/<id>/journal.md` 追加一行 (append-only, 无审批门, 区别 contract/sediment); 省略 `--add` 则列出。随 task finish 一并归档 |
| `subtask <action> <tid> [sid]` | `--name` `--deps "s1,s2"` `--check "断言;断言"` `--passed "1,2"` `--note <文本>` `--estimate <分钟>` `--agent <名>` `--skills "a,b"` | 单 task 内 subtask DAG 调度 (存 per-task task.json 的 `subtasks[]`)。`action`: `add` 登记 / `claim` **一次性认领就绪批 (整批标 running)** / `ready` 只读预览 / `start` 单个占槽 / `check` 勾验收(算完成百分比) / `done` 完成 / `fail` 失败 / `list` 列态。add/start/check/done/fail 必带 `sid`。`--check` = 验收标准 checklist (分号分隔, 每条一个可验断言), `--passed` = `check` 时已通过验收序号 (1-based 逗号分隔; `all`=全过, `none`=清空), `--note` = `fail` 时的失败备注。`--agent` = 执行 agent (省略默认 `general-purpose`), `--skills` = 关联 skills 逗号分隔 (0-n) |

**task.json 字段**: `id / name / desc / status / deps / worktree / branch / created / started / finished / updated / contracts / subtasks`。
**subtask 字段** (`subtasks[]` 内): `sid / name / depends_on / 验收 / 验收done / estimate / agent / skills / created / started / finished / status` (pending→running→done/failed; 运行时失败才追加 `note`)。`验收` = 验收标准 checklist (字符串数组), `验收done` = 已通过验收序号 (1-based 数组; `check` 更新, `done` 自动填满)。`agent` 缺省 `general-purpose`, `skills` 缺省空数组。
**时间戳字段** (task 顶层 + 每个 subtask, 值均为 Unix epoch 秒整数): `created` = 创建时刻; `started` = exec 首次激活/start 时置, **幂等** (重认领/重启不覆盖首次 exec 时刻); `finished` = done/finish 时置。task.html 用这三个配合 `estimate` 显示「预期 vs 实际」耗时。
**subtask 完成百分比**: `_sub_pct` = `done` 强制 100%; 否则 = `len(验收done)/len(验收)`; 无验收标准则未完成即 0%。执行 agent 逐条自检后用 `subtask check <tid> <sid> --passed "1,3"` 回报已过条目, 看板 (task.md/task.html) 按此渲染每 subtask 进度条; task 综合完成率 = 各 subtask 百分比均值。
**subtask 调度环** (main 驱动): `subtask claim <tid>` 一次性认领就绪批 (整批标 running, 免逐个 start) → 按各 subtask 关联的 `agent` (省略即 `general-purpose`) + `skills` dispatch 执行 → agent 完成前逐条自检可 `subtask check` 回报进度 → 完成即 `subtask done/fail` → 再 `claim`。就绪 = pending + 依赖 (`depends_on`) 全 done, 截到空闲槽 (`max_parallel`)。**脚本算+改态一步到位, main 只派 agent** (脚本不能 spawn)。`ready` 是只读预览版 (不改态), `start` 是单个手动补派 (retry 用)。
**状态流转**: `pending → in_progress → completed` (archived 移出 `task/`)。
**id 规则**: **人工传入的可读 slug** (create 必填首参), 从 id 即可知含义 (如 `order-create-api`), 非随机生成。格式 = kebab-case (`^[a-z0-9][a-z0-9-]*$`, 小写字母/数字/连字符, 字母数字开头), 兼作 git 分支名 (`skein/<id>`) + 目录名。全局唯一, 含已归档的不可复用, 非法/重复即报错。

**文件锁 (并发写保护)**: task/subtask 的更新经工作区级排他锁 `.skein/.lock` (`fcntl.flock`) 串行化, 包裹所有变更类命令 (`init/setup/create/start/finish/archive/clean/contract/journal/subtask`); 只读命令 (`current/ready/list/board/view`) 豁免。未拿到锁时**代码轮询等待** (非报错退出), 默认超时 10s, 超时抛错「获取 .skein 写锁超时」。作用: 多 skein 进程 / 并发 subtask 写同一 task.json 不丢更新。`.lock` 已加入 `.skein/.gitignore` (运行期锁文件, 不入库)。

## memory.py — 规则记忆引擎

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/memory.py <cmd>   # 或短命令 skein-memory <cmd>
```

| 命令 | 参数 | 作用 |
| --- | --- | --- |
| `init` | — | 初始化 `.skein/spec/` 两层目录 |
| `session-start` | — | (SessionStart hook 调) 只注入 core 规则**极简索引** (每条 `[类目] 标题` 一行, 不含正文), 受 token 硬预算守卫 (超则截断+告警)。全文按需 `inject-core` 拉 |
| `inject-core` | — | 按需打印 core 规则**全文正文** (session-start 索引命中后, model 拉全文定用否) |
| `recall <query>` | — | 按词粗筛 recall 索引, 打印命中行 (model 再读全文定用否) |
| `sediment` | `--layer core\|recall` (必) `--title` (必) `--category` `--keywords` `--source` `--body-file` | 写盘一条规则 + 自动 reindex |
| `reindex` | — | 重建三份索引 (两层 + 顶层聚合) |
| `list` | `--layer core\|recall` | 列规则文件 |

**规则文件 frontmatter**: `title / layer / category / keywords / source / authored-by / created`。
**类目 (category)**: 物理事实 = 所在子目录名 (git/test/arch/build/style/domain/ops/misc...), 自由建。
**core 预算**: 全文有字符上限 (`inject-core` 软告警), 超了 sediment 会提示降级到 recall。SessionStart **只注入极简索引** (每条一行标题), 另有独立 token 硬预算 (`hooklib`, 超则截断) — 常驻上下文恒定小, 全文按需拉。

## Skills (8 个)

| skill | 何时用 | references |
| --- | --- | --- |
| `skein-add` | **[仅用户显式 `/skein-add <任务描述>`, disable-model-invocation]** 只规划不执行入口: 委托 `skein-planning` (planning 真值源) 无参跑完 planning (判新旧 + 登记 + brainstorm + grill 硬门 + 产出 `prd.md`[+`design.md`]+`implement.md`), 然后**停在 `skein.py start` 之前**, task 留 planning 态, 禁 exec/check/finish。产出的 planning 态 task 留待用户再走 `/skein-go` 或 `skein-flow` 消费。与 flow/`/skein-go` 边界: 后者=强制全闭环 plan→exec→check→finish, add=只到 planning 停 | — |
| `skein-setup` | ① 未初始化 (SessionStart 提示「无 .skein/」): 新仓 main 直跑 `skein.py setup`; 有 trellis 派 `skein-setup` agent 语义迁移。② 已初始化: 手动优化 `.skein/` 结构 (spec 类目重组 / core↔recall 层调 / config 调参, 改盘后 `memory.py reindex`) | trellis-migration |
| `skein-flow` | 复杂/多步/跨文件请求, 强制 task 闭环 (自动或显式触发) + exec 双层 DAG 编排调度 | mandatory-flow-steps · scheduling-algorithm · progress-reporting |
| `skein-planning` | plan 入口: 判新旧 + 登记 + brainstorm + grill 硬门; heavy 档含破坏式重构注解 | dispatch-graph · breaking-refactor |
| `skein-memory` | recall 召回 + sediment 沉淀; 空仓冷启动播种 (一次性) | sediment-workflow · bootstrap-seeding |
| `skein-grill` | 对抗式审查需求 / 工件 (planning 硬门) | review-axes-and-output |
| `skein-check` | 质量门 (lint/type/test/契约), 未过派修; 第 3 轮 FAIL 做 5 维根因复盘 | root-cause-protocol |
| `skein-clean` | **[仅用户主动]** 主动归档完成 task (保留期外) + 清孤儿 worktree / 悬挂分支; 入参 = 保留天数 | anti-examples |

每个 skill 是**多文件组织**: 精简 SKILL.md 入口 + `references/*.md` 明细 (渐进式披露)。原 orchestrate / refactor / bootstrap / break-loop 4 个 skill 无独立运行时调用边, 已分别并入 flow / planning / memory / check 的 references (省常驻 description token)。

## Agents (3 个具名 + 执行选现有 agent)

**执行 subtask 不用具名 agent** — main 为每个 subtask 选一个合适的现有 agent (按任务性质挑, 无合适的用 `general-purpose`) 执行 1 subtask (每文件过写前 CHECKPOINT)。执行纪律 (递归护栏 + 读后写硬门 + 验收标准逐条自检 + 输出格式) 经 **dispatch prompt 硬性注入** (见 `skein-flow/references/scheduling-algorithm.md`) — 通用 agent 有 Agent/Task 工具, 故递归护栏靠 prompt 硬性禁止再派 subagent。以下 2 个是工具受限的具名验证/调研 agent (无 Agent/Task = 递归护栏):

| agent | 职责 | 工具面 | 模型分层 |
| --- | --- | --- | --- |
| `skein-checker` | 只读验证 (lint/type/test/契约合规) | 只读 + Bash, 无 Agent/Task | `model: sonnet` + `effort: medium` |
| `skein-researcher` | planning 纯信息调研 (选型/对比) + bootstrap 扫描模式 (扫既有代码库约定), 结论落盘 `research/` | 读 + 检索, 无 Agent/Task | `model: sonnet` + `effort: medium` |
| `skein-setup` | trellis→skein 语义迁移 (spec 重组为 core/recall×类目 + task 重建 + settings hook 剔除); 机械部分交 `skein.py setup [--full]` (兼容/完全两模式) | 读写 + Bash + 检索, 无 Agent/Task | `model: sonnet` + `effort: medium` |

> 模型分层做 token 优化: 验证 / 调研走较轻档 (sonnet + medium); 执行 agent 由 main 按 subtask 性质选 (默认继承主模型高推理)。

## Command

| command | 作用 |
| --- | --- |
| `/skein-go <任务描述>` | 强制把请求作为 SKEIN task 处理, 走 plan→exec→check→finish。调用即「建 task 同意」 |

## 配置 (`.skein/config.yaml`)

| 键 | 默认 | 作用 |
| --- | --- | --- |
| `max_active` | `2` | 同 session active task 并发上限 (= subtask 级上限) |
| `retain_days` | `7` | 完成 task 保留天数 (留看板), 超则 `_autoclean` 自动归档。`0` = finish 即归档 (旧行为); 负数 = 永不自动归档 (仅 `clean` 主动清) |
| `auto_commit` | `true` | finish 时自动 commit worktree 改动。设 false 则有未提交改动会拒绝 finish (防强删丢失) |
| `worktree_root` | `.worktrees` | worktree 存放根目录 (相对 git 根) |
| `board_theme` | `morandi` | 看板默认主题: `morandi` 莫兰迪 / `glassmorphism` 玻璃拟态 / `liquid` 液态玻璃 / `handdrawn` 手绘 (页内切换器可实时改, 存 localStorage) |
| `board_palette` | `stone` | 看板默认配色: `stone` 石灰 / `ocean` 海洋 / `warm` 暖橙 / `forest` 森林 / `dusk` 暮紫 / `mono` 单色 |
| `board_mode` | `light` | 看板默认明暗: `light` 浅色 / `dark` 深色 |

> 主题/配色以**独立 CSS 文件**存在于插件 `assets/board/` (base + themes/ + palettes/), 渲染时拷到 `.skein/board/`, 看板 html 用相对路径 `<link>` 引入。改主题不需重渲染 — 页面右上角切换器即时切换。

## Hooks (`.claude-plugin/plugin.json`)

| hook | 触发 | 作用 |
| --- | --- | --- |
| **SessionStart** | 每 session 开始 | `memory.py session-start` 注入 core 规则**极简索引** (仅标题, 全文按需 `inject-core`) + `skein.py session-context` 注入活跃 task 状态 (compaction 后恢复)。两处注入均过 `hooklib.budget_guard` token 硬预算守卫 (超则截断+stderr 告警要求简化), 保证 hook 注入 token 可控 |
| **UserPromptSubmit** | 每次用户提交 prompt | `skein.py user-prompt` 注入 **task 判定提醒**: 请求是任务 (跨 ≥2 文件 / 多步骤 / 需调研 / 产出文档) → 让 model 加载 `skein-flow` 走强制闭环, 禁 inline; 纯查询/问答/单文件 ≤20 行豁免。判定为 model 语义活, hook 只注入决策标准 (过 budget_guard); 非 git 仓静默 exit 0 |
| **PreToolUse** | Edit/Write/MultiEdit/Read | `guard-skein.py` 两类硬阻: ① 直接读写 .skein/ 的 task.json / task.md (顶层 + per-task, 读写全挡); ② **迁移门** — 有 `.trellis/` 但无 `.skein/config.yaml` 时挡源码 Read/Edit/Write/MultiEdit (含只读诊断), 逼先 skein-setup 初始化 (纯文本注入压不过 trellisx 的 active-task 注入, 故硬阻; 仅 Bash 跑 `skein.py setup` 放行, `.skein/`·`.trellis/` 内部路径放行不自锁) |
| **PermissionRequest** | Bash/Edit/Write/Read | `allow-skein.py` 对 .skein/ 自有内容操作**默认同意** (Bash 调 skein.py/memory.py 引擎; Edit/Write/Read .skein/ 非脚本文件如 prd/implement)。免逐次授权打断; task.json/task.md 仍归 guard 硬阻, 不放行 |
| **PostToolBatch** | 并行工具批 | `batch-skein.py` 拦同批 ≥2 个 .skein 状态**写命令** (create/start/finish/archive/subtask/sediment...) → block (同写 task.json/spec 有竞态), 引导串行或 `subtask claim` 整批认领 |
| **PostToolUseFailure** | Bash 失败 | `report-skein.py` 仅当失败命令属本插件脚本 (含 skein.py/memory.py/CLAUDE_PLUGIN_ROOT) 时, 注入错误上下文 + `systemMessage` 引导用户**手动**开 issue (不自动建, 免误报刷屏) |

## guard-skein.py 拦截规则

判定: 路径落在 `.skein/` 下且 basename ∈ {`task.json`, `task.md`} → 读写全挡 (含归档路径)。四个文件全由 skein.py 维护, AI 取态经命令 stdout 而非读文件。

| 目标文件 | Read | Edit/Write | 替代方式 |
| --- | --- | --- | --- |
| `.skein/task.json` (顶层 tasks 全表) | 挡 | 挡 | `skein.py current` 列 active; create/start/finish 改 |
| `.skein/task.md` (顶层看板) | 挡 | 挡 | `skein.py list` / `board` 取态 |
| `.skein/task/<id>/task.json` (记录+subtask) | 挡 | 挡 | `skein.py subtask list/ready <id>`; subtask add/start/done 改 |
| `.skein/task/<id>/task.md` (子任务看板) | 挡 | 挡 | `skein.py subtask list <id>` |
| `.skein/task/<id>/{prd,implement,journal}.md` | 放行 | 放行 | planning 工件, AI 直接读写 |

### 迁移门 (trellis 共存强制初始化)

trellisx 与 skein 同装时, 两者都在 SessionStart+UserPromptSubmit 注入; trellisx 注入具体 active-task 状态, model 会跟 trellis 而无视 skein 的文本提示 (实测纯文本注入连输 3 次)。故加 PreToolUse 硬门:

| 条件 | 动作 |
| --- | --- |
| 有 `.trellis/` + 无 `.skein/config.yaml` + tool ∈ {Read,Edit,Write,MultiEdit} + 目标非 `.skein/`·`.trellis/` 内部 | **exit 2 block**, stderr 引导先调 skein-setup (读写源码全挡, 含只读诊断) |
| Bash (`skein.py setup` init 本身) | 放行 (初始化不被自锁) |
| `.skein/`·`.trellis/` 内部路径 | 放行 (迁移读写 spec 不自锁) |
| 无 `.trellis/` 的普通仓 | 不硬阻 (仅靠 hook 文本软提示) |

初始化无条件, 诊断也不例外 (决策: 初始化优先, 只读排查也须先 init); 查询/小改只豁免『建 task / 走 flow』, 不豁免初始化。init 经 Bash 跑 `skein.py setup` 创 config.yaml, 门随即打开。

## 生命周期一图速记

```
init → create(pending) → start(in_progress, +worktree)
     → [plan → exec → check] → finish(commit→merge→archive, -worktree)
                                   ↘ archive (丢弃, 不 merge)
```
