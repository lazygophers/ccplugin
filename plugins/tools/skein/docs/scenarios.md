# 场景用法

不同类型的活儿, 怎么用 SKEIN 最省事。每个场景给「怎么触发 + 会发生什么 + 注意点」。

## 场景 1: 单个功能开发 (最常见)

**例**: 给用户模块加手机号登录。

```
/skein-exec 给用户模块加手机号登录, 含短信验证码下发与校验
```

- **plan**: 和你 brainstorm 短信服务选型、验证码存储 (Redis? DB?)、限流策略, grill 挑漏洞, 产出 PRD + 实现清单。
- **exec**: 拆成 subtask (下发接口 / 校验接口 / 存储层 / 前端表单), 无冲突的并行派, 有依赖的串行。
- **check**: 跑测试 + 契约校验。
- **finish**: 合并回主分支, 若「短信服务必须走异步队列」这类契约值得复用 → sediment 到 core。
- **契约锁定** (可选): planning 时把「验证码必须限流」这类不变量 `skein contract <id> --add` 锁进 task, check 阶段 checker 逐条验证守住没。

**注意点**: plan 阶段多花点时间和 Claude 对齐需求, exec 才不会跑偏。

## 场景 2: 跨多文件重构 (破坏式)

**例**: 把全站 `getUserById` 的返回结构从 `User` 改成 `UserDTO`, 不保兼容。

```
/skein-exec 把 getUserById 返回类型从 User 改为 UserDTO, 所有调用点一次改齐, 不留兼容层
```

- 这类活儿走 **`skein-plan` heavy 档的破坏式重构注解** (`references/breaking-refactor.md`): 不保兼容、全站点一次改齐。
- exec 会先 grep 所有调用点, 一次性全改, 避免留半新半旧的中间态。
- worktree 隔离在这里尤其关键: 改到一半发现方案不对, 直接丢弃整条 task, 主分支毫发无损。

**注意点**: 破坏式重构必须**一个 session 内改完**, 别拆成多次 — 否则调用点新旧不一致会编译失败。

## 场景 3: 需要调研 / 选型

**例**: 给项目选一个后台任务队列方案。

```
/skein-exec 调研并选定后台任务队列方案 (对比 Celery / RQ / Dramatiq), 产出选型文档
```

- plan 阶段可派 `skein-researcher` 并行做纯信息调研 (它只读, 不改代码)。
- **结论持久化**: researcher 除回传摘要外, 把完整结论落盘到 `.skein/task/<id>/research/<topic>.md` — 跨 compaction 存活, 后续 brainstorm/PRD 可复读原始调研, 随 task finish 一并归档。
- 设计决策由 main 汇总后和你拍板 (subagent 不能与你对话)。
- 产出可以是纯文档交付 (选型报告), 也可以选型 + 落地一起。

**注意点**: 调研结论若形成「本项目统一用 X」的约定, finish 时 sediment 到 recall (选型类, 长尾)。

## 场景 4: 同时推进多个 task (多 task 并行)

同一个 session 里, SKEIN 允许**最多 2 个** active task 并行 (`max_active=2`)。

```
/skein-exec 加订单导出功能
# ... 该 task 进行中, 再来一个不冲突的:
/skein-exec 修复登录页样式错位
```

- 各 active task 各占各的 worktree → 默认可并行派 subagent (无写文件冲突自算)。
- 想串行 → 建 task 时用 `--deps` 显式声明依赖; 并行与否只看 task.json 的 `deps` DAG。
- 想显式声明「B 必须等 A」→ 建 task 时 `--deps`:
  ```bash
  skein create order-export --name "订单导出" --desc "加订单导出功能" --deps "order-query"
  ```
- 超过 2 个: `start` 第三个会报错「先 finish 一个」。

**看多 task 状态**:

```bash
skein current
# order-export   进行中  加订单导出功能  .worktrees/skein-order-export
# login-style-fix 进行中  修复登录页样式  .worktrees/skein-login-style-fix
```

无 task 级 focus — 两个 task 无未完成前置, 就绪即可并行。

## 场景 5: 修 bug

**小 bug** (单文件 ≤20 行, 位置已知) → **豁免, 不建 task**, Claude 直接改。

**根因型 bug** (症状在一处, 根因在共享函数, 多调用点受影响) → 建 task:

```
/skein-exec 修复金额计算偶发差 1 分的 bug, 定位根因并覆盖所有调用点
```

- exec 会 grep 所有调用点, 在**共享函数**处一次修好 (而非每个调用点打补丁)。
- check 阶段补一个能复现该 bug 的测试, 防回归。

**注意点**: 若这个 bug 是踩了 ≥2 轮才定位、根因可写成可验证契约 → finish 时 sediment (踩坑留痕)。

## 场景 6: 请求太简单, 不确定要不要建 task

不用你判断 — 直接说需求, Claude 会按作用域边界表自动决定:

- 够简单 (纯查询 / 单文件小改) → 直接做, 不建 task。
- 够复杂 (跨文件 / 多步) → 自动加载 `skein-flow` 建 task。
- 模糊 → Claude 用 AskUserQuestion 问你 (禁自行 inline 蒙混)。

想**强制**当 task 处理 (即使看着简单) → 显式 `/skein-exec`, 调用即「建 task 同意」信号。

## 场景 7: task 中途出问题

| 情况 | 怎么办 |
| --- | --- |
| exec subtask 报错/验收不过 | main 读根因**自愈** (本 task scope 内): 定点小缺陷 → 原地重派 (≤2 轮); 根因是独立可修单元 → 加修复 subtask 定点修后重派失败 subtask。兜底 (修复也失败/累计超上限/根因超 scope) → 停手回传你 (走根因复盘协议) |
| check 反复不过 (≥2 轮) | 派 agent 定点修; 第 3 轮仍不过 → 走 `skein-check` 根因复盘协议 (`references/root-cause-protocol.md`) 做**跨维度根因复盘** (需求/设计/实现/环境/测试 5 维定位 + 预防措施), 出口: 带根因回 exec 定向重修, 或停手附根因报告转人工 (可复用教训回流 sediment) |
| finish 合并冲突 | 自动 abort + 报冲突文件; 手动解冲突后重跑 finish, **禁强解** |
| 方案跑歪想放弃 | `skein archive <id>` — 丢弃 task (销 worktree, 不合并), 主分支干净 |

## 场景 8: 首次接入空仓 (冷启动播种)

**例**: 一个已有代码但从没用过 SKEIN 的仓库, `.skein/spec` 还是空的, 规则库没历史经验可召回。

- main 会用 AskUserQuestion 征你同意后走 **`skein-spec` 冷启动播种** (`references/bootstrap-seeding.md`):
  - 派 `skein-researcher` (bootstrap 扫描模式) 扫既有代码库约定 (命名 / 错误处理 / 测试 / 架构边界 / 构建 5 维), 提炼候选规则。
  - 逐条判 `core` / `recall` / `drop`, 经现有 sediment 写盘流程落盘 (冷启动跑前已一次征同意, 内部候选自动写)。
- **一次性动作**: 只在冷启动跑一次, 给规则库播下基线; 后续增量经验仍走正常 finish sediment。

**注意点**: 静态扫描是**推断**不是踩坑实证 → 默认多归 recall, 仅「违反必炸」的硬约束进 core, 别让 bootstrap 撑爆 core 层。

## 场景 9: 清理残留

worktree 崩了、分支悬挂、task 漏归档 → 用 **`skein-clean`** skill 安全清扫孤儿 worktree / 悬挂分支 / 漏归档 task。

## 场景 10: 大需求冷启动 (模糊愿景 → supertask)

**例**: 用户开口就是「重构整个支付模块」「给产品加 AI 能力」「做个数据中台」 — 范围大、动词泛、无落点。

- **触发**: `skein-plan` 命中模糊信号判据任一即进 cold-start — ① 无动词或动词泛 (「重构/优化/加能力」无宾语); ② 无文件路径 / 无具体模块名; ③ 一句话 <15 字; ④ 愿景腔 (「我有个想法 / 想做个 / 感觉」)。清晰输入跳过本场景, 走常规 brainstorm。
- **愿景翻译 (≤3 轮, 零增量路径)**:
  - **Job Story 三段** — main 套原话填 `When [情境], I want [动机], so I can [预期成果]`, `AskUserQuestion` 让你确认 / 修正, 先锁 outcome (为谁 / 为何 / 价值) 再谈 solution。
  - **said / implied / missing 三分** — 明说、暗示入正文 (暗示回读确认); 缺失项列 prd.md「Open Questions」逐条问; main 的假设强制写「Assumptions」段, 禁埋正文 (防 Assumption Burial)。
  - **兜底**: ≤3 轮仍答不出 outcome → 停 planning, task 标「需求未定」, 不硬猜往下拆。
- **判大需求 → 建 supertask**: 收敛后若需拆多个**各自完整 plan/exec/check/finish** 的独立小需求 → 建聚合父层 + 各 child:
  ```bash
  skein create pay-rebuild --kind supertask --name "支付重构" --desc "支付模块全链路重构"
  skein create pay-facade --parent pay-rebuild --name "支付门面+契约"   # child 1
  skein create pay-core   --parent pay-rebuild --name "支付核心重写"     # child 2
  skein create pay-retire --parent pay-rebuild --name "旧支付退役"       # 末 child
  ```
- **各 child 独立闭环**: 每个 child 走自己的 plan → exec → check → finish, 无写冲突即可并行; 深度限 2 层 (supertask→task→subtask, child 不再生 child, 脚本硬拦)。
- **聚合归档**: 末 child finish 不直接合并 — supertask finish 前所有 child 须全 done, 才一次性聚合归档; 看板 `task.md` 按 supertask 分组, 每个 supertask 刷专属 `vision.md` 聚合 child 进度。
- **大需求必跑 grill 3 轴** — 验收 SMARC (可测) / drift (逐条 subtask 溯源原始 Job Story 愿景) / scope (每条溯回 said/implied, 脑补回 Out-of-Scope), 防大需求 scope 失控。

**注意点**: supertask 默认不建 — 单 task 可覆盖的中小需求走 single task 零增量。冷启动的关键是先翻译愿景锁 outcome, 别在动词泛的诉求上直接拆 subtask。

---

不确定某个活儿走哪条? 看 [best-practices.md](best-practices.md) 的决策流程图。
