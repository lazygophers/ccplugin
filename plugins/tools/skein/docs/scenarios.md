# 场景用法

不同类型的活儿, 怎么用 SKEIN 最省事。每个场景给「怎么触发 + 会发生什么 + 注意点」。

## 场景 1: 单个功能开发 (最常见)

**例**: 给用户模块加手机号登录。

```
/skein-go 给用户模块加手机号登录, 含短信验证码下发与校验
```

- **plan**: 和你 brainstorm 短信服务选型、验证码存储 (Redis? DB?)、限流策略, grill 挑漏洞, 产出 PRD + 实现清单。
- **exec**: 拆成 subtask (下发接口 / 校验接口 / 存储层 / 前端表单), 无冲突的并行派, 有依赖的串行。
- **check**: 跑测试 + 契约校验。
- **finish**: 合并回主分支, 若「短信服务必须走异步队列」这类契约值得复用 → sediment 到 core。
- **契约锁定** (可选): planning 时把「验证码必须限流」这类不变量 `skein.py contract <id> --add` 锁进 task, check 阶段 checker 逐条验证守住没。

**注意点**: plan 阶段多花点时间和 Claude 对齐需求, exec 才不会跑偏。

## 场景 2: 跨多文件重构 (破坏式)

**例**: 把全站 `getUserById` 的返回结构从 `User` 改成 `UserDTO`, 不保兼容。

```
/skein-go 把 getUserById 返回类型从 User 改为 UserDTO, 所有调用点一次改齐, 不留兼容层
```

- 这类活儿走 **`skein-planning` heavy 档的破坏式重构注解** (`references/breaking-refactor.md`): 不保兼容、全站点一次改齐。
- exec 会先 grep 所有调用点, 一次性全改, 避免留半新半旧的中间态。
- worktree 隔离在这里尤其关键: 改到一半发现方案不对, 直接丢弃整条 task, 主分支毫发无损。

**注意点**: 破坏式重构必须**一个 session 内改完**, 别拆成多次 — 否则调用点新旧不一致会编译失败。

## 场景 3: 需要调研 / 选型

**例**: 给项目选一个后台任务队列方案。

```
/skein-go 调研并选定后台任务队列方案 (对比 Celery / RQ / Dramatiq), 产出选型文档
```

- plan 阶段可派 `skein-researcher` 并行做纯信息调研 (它只读, 不改代码)。
- **结论持久化**: researcher 除回传摘要外, 把完整结论落盘到 `.skein/task/<id>/research/<topic>.md` — 跨 compaction 存活, 后续 brainstorm/PRD 可复读原始调研, 随 task finish 一并归档。
- 设计决策由 main 汇总后和你拍板 (subagent 不能与你对话)。
- 产出可以是纯文档交付 (选型报告), 也可以选型 + 落地一起。

**注意点**: 调研结论若形成「本项目统一用 X」的约定, finish 时 sediment 到 recall (选型类, 长尾)。

## 场景 4: 同时推进多个 task (多 task 并行)

同一个 session 里, SKEIN 允许**最多 2 个** active task 并行 (`max_active=2`)。

```
/skein-go 加订单导出功能
# ... 该 task 进行中, 再来一个不冲突的:
/skein-go 修复登录页样式错位
```

- 两个 task 的写文件范围**不相交** → 各占各的 worktree, 可并行派 subagent。
- 相交 → 自动串行 (冲突自算边)。
- 想显式声明「B 必须等 A」→ 建 task 时 `--deps`:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py create "任务B" --deps "t01"
  ```
- 超过 2 个: `start` 第三个会报错「先 finish 一个」。

**看多 task 状态**:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py current --all
# t01  in_progress  加订单导出功能   <- current
# t02  in_progress  修复登录页样式    <- active
```

`focus` (⭐, 默认操作对象) 是最近 start 的那个。

## 场景 5: 修 bug

**小 bug** (单文件 ≤20 行, 位置已知) → **豁免, 不建 task**, Claude 直接改。

**根因型 bug** (症状在一处, 根因在共享函数, 多调用点受影响) → 建 task:

```
/skein-go 修复金额计算偶发差 1 分的 bug, 定位根因并覆盖所有调用点
```

- exec 会 grep 所有调用点, 在**共享函数**处一次修好 (而非每个调用点打补丁)。
- check 阶段补一个能复现该 bug 的测试, 防回归。

**注意点**: 若这个 bug 是踩了 ≥2 轮才定位、根因可写成可验证契约 → finish 时 sediment (踩坑留痕)。

## 场景 6: 请求太简单, 不确定要不要建 task

不用你判断 — 直接说需求, Claude 会按作用域边界表自动决定:

- 够简单 (纯查询 / 单文件小改) → 直接做, 不建 task。
- 够复杂 (跨文件 / 多步) → 自动加载 `skein-flow` 建 task。
- 模糊 → 用 AskUserQuestion 问你。

想**强制**当 task 处理 (即使看着简单) → 显式 `/skein-go`, 调用即「建 task 同意」信号。

## 场景 7: task 中途出问题

| 情况 | 怎么办 |
| --- | --- |
| exec agent 报错返回 | main 读原因、缩范围、重派; 连续 2 次失败 → STOP 回传你 |
| check 反复不过 (≥2 轮) | 派 agent 定点修; 第 3 轮仍不过 → 走 `skein-check` 根因复盘协议 (`references/root-cause-protocol.md`) 做**跨维度根因复盘** (需求/设计/实现/环境/测试 5 维定位 + 预防措施), 出口: 带根因回 exec 定向重修, 或 STOP 附根因报告转人工 (可复用教训回流 sediment) |
| finish 合并冲突 | 自动 abort + 报冲突文件; 手动解冲突后重跑 finish, **禁强解** |
| 方案跑歪想放弃 | `skein.py archive <id>` — 丢弃 task (销 worktree, 不合并), 主分支干净 |

## 场景 8: 首次接入空仓 (冷启动播种)

**例**: 一个已有代码但从没用过 SKEIN 的仓库, `.claude/rules` 还是空的, 规则库没历史经验可召回。

- main 会用 AskUserQuestion 征你同意后走 **`skein-memory` 冷启动播种** (`references/bootstrap-seeding.md`):
  - 派 `skein-researcher` (bootstrap 扫描模式) 扫既有代码库约定 (命名 / 错误处理 / 测试 / 架构边界 / 构建 5 维), 提炼候选规则。
  - 逐条判 `core` / `recall` / `drop`, 经现有 sediment 审批门落盘。
- **一次性动作**: 只在冷启动跑一次, 给规则库播下基线; 后续增量经验仍走正常 finish sediment。

**注意点**: 静态扫描是**推断**不是踩坑实证 → 默认多归 recall, 仅「违反必炸」的硬约束进 core, 别让 bootstrap 撑爆 core 层。

## 场景 9: 清理残留

worktree 崩了、分支悬挂、task 漏归档 → 用 **`skein-clean`** skill 安全清扫孤儿 worktree / 悬挂分支 / 漏归档 task。

---

不确定某个活儿走哪条? 看 [best-practices.md](best-practices.md) 的决策流程图。
