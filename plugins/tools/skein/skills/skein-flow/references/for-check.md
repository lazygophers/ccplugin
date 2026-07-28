# for-check — check 阶段作业手册

exec 完成后、finish 前的**质量门**。**验证与修复分离**: `skein-checker` 只验证 (无写权), 失败交合适 agent 修。未过禁 finish。

## 触发与前置硬门

- **触发**: SKILL.md 参数路由 `$1=check` (exec 产物完成后、finish 前, 派 skein-checker 跑验证), 或 flow 全闭环内 exec 全 subtask done 自动进入。
- **🛑 check 状态先行 (硬前置)** — 必须先 `skein check <id>` 进检查中态才派 skein-checker 跑验证, 禁 main 在 task 仍「进行中」态自跑验证当 check 结果。三环节硬门统一规则详见 [state-before-action.md](state-before-action.md) 硬门 3。
- **禁动 design.md** — design.md 写入归 planning (仅 planning 阶段 + check 失败回 planning 二次进入可写); **exec / check / finish 阶段均禁动**。check 检出方案性冲突 → 回 planning 改 design 后重派。

## 流程步骤

1. **验证** — 派 `skein-checker`: 传 Active task id + 工作目录 (task 的 `worktree` 字段; null=原地仓库根)。checker 分两步: **① checkpoint 核对 → ② 场景自适应内置 check**, 回传报告。
   - **① checkpoint 核对 (task + subtask 双层)** — checker 核对本 task 全部 checkpoint:
     - **task 级** — 自跑 `skein prd read <id> --type=acceptance` 取 prd `## 验收标准`, **只验未勾 (`- [ ]`) 项**; 已 `- [x]` 项跳过。
     - **subtask 级** — 逐个 subtask 核对其 planning 登记的 `--check` 验收 checklist (`skein subtask list <id>`)。
   - **② 场景自适应内置 check** — checker 按项目场景自判跑对应内置检查 (多特征并存跑命中的多类):
     - **编程类** — build / test / lint / type-check / **架构一致性** + 契约合规。
     - **小说 / 内容类** — **逻辑一致性** + 设定一致性 + 伏笔呼应。
     - **数据 / ETL 类** — schema 校验 / 数据管道跑通 / 字段一致性 / 样本抽检。
     - **文档 / 知识类** — 链接有效性 / 结构完整 / 术语一致 / 交叉引用不断裂。
     - **配置 / 基建类** — 配置语法校验 / 幂等性 / dry-run / 依赖版本锁一致。
     - **设计 / 前端类** — 组件渲染 / 可访问性 / 视觉回归 / 响应式断点。
     - 无识别场景 → 该项标 `[工具失败: 未识别项目场景]`。
   - **契约逐条验证** — checker MUST 先读出本 task 全部契约, **逐条核对是否被满足**, 报告每条 pass/fail: `skein contract <id>`。任一条 fail → 进修复循环。
   - **一致性核查** — checker MUST 检 subtask 产物间 + 与 prd 契约有无冲突: 接口签名对不上 / 重复实现同一职责 / 命名与约定相斥 / 数据流断裂 / 契约互相矛盾。逐条报冲突对 (哪两处 file:line + 冲突点)。
2. **判定** — 全绿 (含零冲突) → 放行 finish。FAIL 或**检出冲突** → 进修复循环。**本轮验证通过的验收项**, main 经 `skein prd check <id> --type=acceptance --list "<验收项文本>"` 回写勾选态持久化 (脚本写盘, 禁裸 Edit prd.md), 未过项保持 `- [ ]` 留待修复后重验。需反勾用 `skein prd uncheck`。
3. **回 planning 重确认 (复用现有 `进行中` 态)** — 通用回退流程详见 [rollback-protocol.md](rollback-protocol.md); check 修复 subtask 操作规范详见 [subtask-operations.md](subtask-operations.md) 第 4 节。check FAIL 或检出冲突, **禁改 task 状态** (依旧 `进行中`)。main 先回 planning 思维重审失败, 用 `AskUserQuestion` 或 grill 与用户确认修复方向, **禁跳过确认直接补 subtask 回 exec**。check 阶段特有分档:
   - **孤立失败** (单点 lint/type/test/契约 fail) → 确认后加 1 个定点修复 subtask (--deps 挂失败源)。
   - **一致性冲突 / 根因跨 subtask** → 确认后按冲突根因加**多个**修复 subtask (一冲突一 subtask)。**直到全绿且零冲突才放行**。
   - **方案性 / 设计缺陷** (架构选型不对 / 契约定义有误 / 需求边界漏了) → 回 planning **补充或重设计 design.md** (二次进入才可写), 同步修 prd + 改契约, 再据新设计重拆或补子任务。**新方案经 grill/AskUserQuestion 确认无误, 才回 exec**。
   - 方向确认=必经门: main 不得凭报原文擅自加 subtask, 必先 grill/AskUserQuestion 让用户对修复方向拍板。
4. **重验** — 修复 subtask 全 done 后重派 `skein-checker` 复跑 (含一致性)。未过回 planning 重确认循环。
5. **放行** — 全绿且零冲突 → 进 finish 阶段。

## 完成判据

- [ ] checkpoint 核对: task 验收标准 + 各 subtask `--check` 项全完成
- [ ] 场景内置 check 全绿
- [ ] 契约逐条 pass (`skein contract` 全覆盖)
- [ ] 一致性核查零冲突
- [ ] 本轮通过的验收项已回写 `- [x]`

## 失败模式

| 触发 | 一线修复 | 仍失败兜底 |
|---|---|---|
| 孤立失败 (单点 lint/type/test/契约 fail) | 回 planning 重确认: grill/AskUserQuestion 敲定修复方向, 同 task `subtask add` 1 个定点修复子任务 (--deps 失败源), task 保持 `进行中` | 反复不过 → 见下「≥3 轮」路径 |
| 一致性冲突 / 根因跨 subtask | 同 task `subtask add` 多个修复子任务 (一冲突一 subtask), 逐条覆盖 | 冲突未全覆盖禁 finish |
| 修复子任务 ≥2 轮仍 FAIL (第 3 轮) | 停加子任务循环 → 按 [root-cause-protocol.md](root-cause-protocol.md) 5 维根因复盘 | 带根因回 planning 重确认定向重修; 根因超 exec (需求/设计缺陷) → 停手附根因报告转人工 |

## 延伸引用

- [state-before-action.md](state-before-action.md) — 状态先行三环节硬门 (硬门 3 = check 级)
- [rollback-protocol.md](rollback-protocol.md) — check 未过回 planning 重确认通用回退流程
- [subtask-operations.md](subtask-operations.md) — 第 4 节: check 修复 subtask 操作规范
- [root-cause-protocol.md](root-cause-protocol.md) — 修复 ≥3 轮不收敛的 5 维根因复盘
