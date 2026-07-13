# 空仓冷启动播种 (一次性) — bootstrap seeding

**一次性动作**。两层记忆 (core/recall) 空仓时前几十轮 planning 无规则可召回。bootstrap 从**既有代码库**提炼约定作冷启动基线, 让第一个 task 就有规则可用。

> **不新造引擎**: 完全复用 `skein-researcher` (扫描) + sediment (审批写盘)。bootstrap 只是把二者串成一次性流程, 不改 `scripts/`, 不加机器/字段。

## 触发 (main 提议, 非自动强制)

满足**全部**才提议跑一次:

1. 仓库**首次**用 SKEIN (无 task 历史) 或明确要冷启动播种。
2. `.skein/spec` 为空/近空 — 验: `skein-memory list` 两层规则数近 0。
3. 代码库**已有一定体量** (空/脚手架仓库无约定可提, 跳过)。

**跑前硬停: 用 `AskUserQuestion` 征得同意再跑**, 禁自动强制。用户拒 → 跳过, 走正常 planning (规则随 finish sediment 增量积累)。

## 流程 (main 同步驱动)

### ① 派 skein-researcher (bootstrap 模式) 扫代码库

dispatch prompt「已知」段标 `mode=bootstrap` + `task-id=bootstrap`, 让 researcher 走其**bootstrap 扫描模式** (见 `agents/skein-researcher.md`): 扫命名/错误处理/测试/架构边界/构建五维, 提炼**既有约定**为候选规则。

- researcher 只读, 结论落盘 `.skein/task/bootstrap/research/conventions.md` (复用现有 research 落盘机制)。

#### 五维扫描明细 (供 main 校对 researcher 覆盖面)

researcher bootstrap 模式扫以下五维, 每维产 0..N 条候选 (无信号则 0 条, 禁硬凑)。每条 MUST 附证据 (file:line, ≥2 处一致才算约定, 单处前缀 `推测:` 或 drop)。候选落盘格式见 `agents/skein-researcher.md`。

| 维度 | 扫什么 |
|---|---|
| **命名** | 文件/目录/函数/变量/类型命名惯例, 大小写, 前后缀约定 |
| **错误处理** | 异常 vs 返回码, 错误包装/日志模式, 边界校验位置 |
| **测试** | 测试框架/目录/断言风格, mock 约定, 覆盖率门槛 |
| **架构边界** | 分层/模块依赖方向, 禁止的跨层访问, 目录职责 |
| **构建** | 构建/依赖/发布命令, lint/format 工具, CI 约定 |

### ② main 读回候选, 逐条判层

读 researcher 回传 + 落盘全量, 每条判 **core / recall / drop** (分层判据同 [sediment-workflow §2](sediment-workflow.md))。bootstrap 证据来自静态扫描 (非踩坑实证), **从严控 core**: 默认全归 recall, 仅"违反必炸"硬约束 (如 DB 层禁裸 SQL) 进 core; 弱信号/一次性/语言通识 drop。

### ③ 经 sediment 审批门写盘

保留下来的候选**逐条**走 sediment 审批门 (**复用** [sediment-workflow.md](sediment-workflow.md)):

- 提案 (层 + 类目 + 标题 + 正文 + 关键词) → `AskUserQuestion` 交用户批。
- **停手: 未过审批禁写盘**。用户可逐条批/驳/改层。
- 批准的写盘: `skein-memory sediment --layer core|recall --category <类目> --title T --keywords "a,b" --source bootstrap --body-file <正文.md>` (自动 reindex)。
- `--source bootstrap` 统一标来源, 便于日后审计冷启动规则。

## 一次性边界

- bootstrap **只播种冷启动基线**, 跑完即止, **不重复**。
- 后续规则增量走**正常 finish sediment** (踩坑实证驱动), 不再回 bootstrap。
- 想补播 → 手动再走本流程, 但通常 finish sediment 已够。

## 失败路径

| 情况 | 处理 |
|---|---|
| 代码库无明显约定 (脚手架/极小仓) | **播空或少量, 禁硬凑** — 无信号就 drop 全部, 老实告诉用户"无约定可提, 走正常积累" |
| researcher 缺信息 (读不到关键文件/范围不清) | researcher 回传标 `需要: <问题>`, main 补齐 dispatch 或转达用户 |
| `.skein/spec` 已非空 | 不满足触发条件, 不提议 (避免与已有规则冲突/重复) |
| 候选与已有规则重复 | sediment 判定门排除项拦截 (已有规则覆盖 → drop) |

## 反例

| 禁 | 改为 |
|---|---|
| 自动跑 bootstrap 不问用户 | `AskUserQuestion` 征同意 |
| 无约定硬凑规则填满两层 | 播空/少量, 老实说明 |
| 候选跳过 sediment 直接写盘 | 逐条走审批门 |
| 什么都塞 core 常驻 | 默认 recall, 仅硬约束进 core |
| 为 bootstrap 改 skein-memory / 加新脚本 | 复用现有 researcher + sediment |
| 跑完 bootstrap 又反复补播 | 一次性, 后续走 finish sediment |
