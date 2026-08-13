# dag — 拆分与调度

planning 怎么拆 subtask、依赖怎么挂，以及脚本据此如何调度（ready 判定、排序、池模型）。执行循环、自愈、阶段跳转见 [skein-flow/references/flow-loop.md](../../skein-flow/references/flow-loop.md)。

## 1. 依赖模型

SKEIN 只认显式依赖边，不推测隐式顺序。

| 层级    | 字段         | 登记位置                                        | 登记命令                                                                                         |
| ------- | ------------ | ----------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| subtask | `depends_on` | per-task `task.json` 的 `subtasks[].depends_on` | `skein subtask add <tid> <sid> --name <str> --desc <str> --estimate <小时> --deps <sid1>,<sid2>` |
| task    | `deps`       | 顶层 task 索引                                  | `skein task create --deps <tid1>,<tid2>`                                                              |

`A --deps B` = A 依赖 B，B done 后 A 才 ready。规矩：

- 并行与否只看显式 DAG，不靠脚本猜文件重叠；有序关系必须在 planning 写进 `--deps`。
- 无真实顺序依赖就不加边 —— 伪依赖拉长关键路径、扼杀并行。
- DAG 是调度真值源：不写 mermaid 图文件，运行态看 `skein subtask list <tid>`，不看任何 md。
- planning 未登记任何 subtask → `skein task confirm` 硬拒。

`--deps` 必须无环，三个常见挂错：

| 陷阱              | 示例                                        | 正确做法                                 |
| ----------------- | ------------------------------------------- | ---------------------------------------- |
| 互相依赖          | A depends_on B，B depends_on A              | 拆共享前置 C，A/B 都依赖 C。             |
| 修复 subtask 挂错 | fix depends_on 失败项，导致原失败项无法重跑 | fix 挂失败项原前置；原失败项再依赖 fix。 |
| 跨层跳挂          | 下游直接挂源头，绕过中间真实依赖            | 按真实数据/接口依赖挂边。                |

## 2. 拆分与落盘

先用一张表理清 subtask + 依赖 + 验收 + skills（skills 0-n 逗号分隔），再逐行落盘：

| subtask | depends_on | 验收标准 (checklist)       | skills       |
| ------- | ---------- | -------------------------- | ------------ |
| st1     | -          | 迁移可回滚; 新列有默认值   | db-migration |
| st2     | st1        | 新字段透传响应; 旧字段不删 | -            |
| st3     | st1        | 覆盖新旧字段两条路径       | -            |

> st1 = **契约 subtask**（定 schema）：st2/st3 只依赖它、互不依赖 → st1 done 即并行，是「协议先行，后并行」的落地形。

落盘由 main 同步跑：

```bash
skein subtask add <tid> st1 --name "改 schema"   --desc "加迁移列并回填默认值" --estimate 2 --skills db-migration --check "迁移可回滚; 新列有默认值"
skein subtask add <tid> st2 --name "改调用站点" --desc "调用站点透传新字段" --estimate 1.5 --deps st1 --check "新字段透传响应; 旧字段不删"
skein subtask add <tid> st3 --name "加测试"     --desc "覆盖新旧字段两条路径" --estimate 1 --deps st1 --check "覆盖新旧字段两条路径"
```

`sid`/`--name`/`--desc`/`--estimate` 四者必填（缺一即报错退出），字段全表查 `skein subtask --help`。

**求最短工期（min makespan）**：就绪批由脚本打分排序后截到空闲槽位（打分细则见 §5），planning 只需做对三件事：

- **协议先行，后并行** — 先识别 subtask 间共享契约（接口签名 / 数据结构 / 类型 / API 格式 / DB schema），把「定契约」抽成单个前置 subtask，所有实现 subtask 只 `--deps` 它、彼此不互挂 → 契约 done 即全批并行。反模式：让实现 A 依赖实现 B 只因「B 先写了接口」—— 应把接口提成独立前置。
- **压关键路径** — 长任务（`--estimate` 大）尽量前置，让下游能早并行。脚本的 `crit_weight` 已用 `estimate` 加权算最长工期链（CPM），estimate 填得准直接影响调度质量。
- **瓶颈不饿（Drum Buffer）** — work 池是系统瓶颈（固定并发槽），首要目标是让瓶颈永不空闲。若 ready 数 < 空闲槽且仍有 pending subtask，说明依赖链过深（可并行化未并行化），回 planning 审视 DAG。

## 3. 复杂度天花板：cold-start 大需求

归一 vs 分立的判据见 [skein-flow/references/flow-loop.md#作用域边界](../../skein-flow/references/flow-loop.md#作用域边界)（默认归一）。只有下列 cold-start 信号命中才升级为多 task：

| 信号                                                    | 判据                                    | 动作                                                                                   |
| ------------------------------------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------- |
| 复合嗅味（"X and Y and Z"）/ 多独立能力 / subtask 会 >8 | capability 按**用户行为**拆（非技术层） | 拆多 task：`skein task create <super-id> --kind supertask` + 各 child `--parent <super-id>` |

- **capability ≠ 技术模块** — capability 是用户行为（「下单」「退款」），非技术层（「DB 层」「API 层」）。按技术层拆 = 跨层耦合依旧的假拆。
- **walking skeleton 优先** — 第一个 task 强制端到端最薄能跑通（验证数据流 / 契约 / 部署链路假设），非铺平所有能力域。假设证伪早返工，比铺平再发现省。

## 4. 验收标准编写参考

> skein 不强制 TDD（行为正确性由 subtask 验收标准约束）。本段用于识别验收设计本身的问题。

| 反模式                     | 症状                                          | 为何坏                                     |
| -------------------------- | --------------------------------------------- | ------------------------------------------ |
| **implementation-coupled** | 测试 mock 内部 / 测私有方法 / 走 side channel | 绑实现细节，重构即崩（行为没变但测试全红） |
| **tautological**           | assertion 重算 expected 用了被测的同一段逻辑  | 永真，自己证明自己对                       |
| **horizontal-slicing**     | 全测试先写完再一口气全实现                    | 违反 tracer-bullet；一处设计错波及全测试集 |

**pre-agreed seam 纪律**：写验收标准前先写下 seam 并确认 —— 被测单元与外部交互的边界在哪（依赖注入点 / 接口契约）。未确认 seam 不写测试。subtask 的验收 checklist 即隐含 seam（写明「输入 X → 输出 Y」就把 seam 钉死，不约束实现如何达成）。

> 若验收标准只能靠「mock 内部 / 测私有」才能验证 → seam 没定清，回 design.md 重定接口边界再写验收。

## 5. ready 判定与排序

```text
subtask.ready = 所有 depends_on 均 done
                且 subtask.status == pending
                且 pools.work 有空槽
```

| 操作                           | 是否被 deps 阻塞 | 说明                           |
| ------------------------------ | ---------------- | ------------------------------ |
| `skein task create` / `subtask add` | 否               | planning 可提前做。            |
| `skein task confirm`                | 否               | confirm 只审 planning 产物 + 人审，不看前置进度（前置没跑完也能先批）。 |
| `skein claim exec` / `flow run`     | 是               | 前置 task 未 done 的 task 不出活；subtask 自身 depends_on 未 done 也不 ready。 |
| `skein subtask claim` / `subtask start` | 是           | 同上，单 task 路径同一道门。   |

ready 数超过空闲槽时按四键稳定排序截取：

```text
排序键 (降序优先):
  1. task 优先级 (urgent=3 > high=2 > normal=1 > low=0)
  2. score = crit_weight × 100 + 等待小时数 × 1 + (exec phase ? 1 : 0)
  3. task 登记序
  4. subtask 登记序
```

score 的三项权重设计：`W_CRIT >> W_WAIT ≈ W_EXEC`。关键路径权重占绝对主导（保证 makespan 最小化），等待时长和 exec phase 只在同 crit 级别内微调 —— `W_WAIT` 防饿死（等够久的低 crit subtask 能翻盘），`W_EXEC` 软优先 exec phase（同分时 exec 先走，但 research 不会被无限期饿死）。

```text
# CPM 加权关键路径: estimate 加权的最长下游工期链 (非跳数)
crit_weight(node) = estimate(node) + max(crit_weight(child) for child in children(node))   # 叶子 = estimate
layer(source) = 0; layer(node) = max(layer(dep)) + 1                                      # BFS 分层, 看板渲染用
```

> CPM（关键路径法）：`crit_weight` 用 `estimate` 加权而非跳数，因为 0.5h 前置和 8h 前置在跳数模型中等权，但工期影响差 16 倍。前端 ETA 计算已用相同逻辑，两端一致。

## 6. 双池模型

| 池     | 计数对象                                    | 配置         | 校验位置                        |
| ------ | ------------------------------------------- | ------------ | ------------------------------- |
| `work` | `status=running` 的 exec/research subtask   | `pools.work` | `skein claim` / `subtask start` |
| `gate` | `status=check` / `status=finishing` 的 task | `pools.gate` | `skein task finishing`               |

`skein task confirm` 不占池；真正资源约束在 running subtask 与 gate task。

> **利用率警戒（Kingman 近似）**：work 池利用率 ρ = running/exec 槽位超 80% 时，subtask 等待时间呈非线性增长。planning 阶段若预估 subtask 总量大，考虑提高 `pools.work` 或减少伪依赖释放并行度。
>
> **gate 优先级反转风险**：gate 池满时，urgent task 的 check/finishing 可能被 low priority task 阻塞。若频繁出现，考虑提高 `pools.gate` 或拆分大体量 task 减少 gate 占用时长。

## 7. claim 命令族

| 命令                              | 范围        | 语义                                                                                                                              |
| --------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `skein claim`                     | 全局跨 task | 同时处理 exec + check 两路，只推状态不做路由；派谁由 main 按 task 状态判，见 [skein-flow/references/flow-loop.md#主循环骨架](../../skein-flow/references/flow-loop.md#主循环骨架)。 |
| `skein claim exec`                | 全局跨 task | 只认领 ready subtask 并标 `running`。                                                                                             |
| `skein claim check`               | 全局跨 task | 只认领可进 check / finishing 的 task。                                                                                            |
| `skein subtask claim <tid>`       | 单 task     | 单 task 内批量认领。                                                                                                              |
| `skein subtask start <tid> <sid>` | 单 subtask  | 启动 pending/failed subtask。                                                                                                     |

任一 claim 加 `--dry-run` = 只读预览，不改状态。

exec 统一派 `skein:skein-executor`，dispatch 只给 tid、sid、工作目录，executor 自读 `skein subtask show <tid> <sid>`。完成即派、失败重试、断点续跑见 [skein-flow/references/flow-loop.md#主循环骨架](../../skein-flow/references/flow-loop.md#主循环骨架) 与 [skein-redo/references/redo.md](../../skein-redo/references/redo.md)。
