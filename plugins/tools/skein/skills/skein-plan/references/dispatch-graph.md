# 子任务拆分 + 调度 DAG (落 task.json)

exec 阶段的 DAG = task.json `subtasks[].depends_on`, **由 `skein subtask add` 登记, 不写 mermaid 图文件**。planning 未登记任何 subtask → `skein start` 硬拒。

拆分时先用一张表理清 subtask + 依赖 + 验收 + agent (agent 省略默认 `skein-executor`, skills 0-n 逗号分隔), 再逐行落盘:

| subtask | depends_on | 验收标准 (checklist) | agent | skills |
|---|---|---|---|---|
| st1 | - | 迁移可回滚; 新列有默认值 | skein-executor | db-migration |
| st2 | st1 | 新字段透传响应; 旧字段不删 | skein-executor | - |
| st3 | st1 | 覆盖新旧字段两条路径 | skein-executor | - |

> 上表 st1 = **契约 subtask** (定 schema): st2/st3 只依赖它、互不依赖 → st1 done 即并行, 是「协议先行, 后并行」的落地形。

落盘 (planning 执行, main 同步跑):

```bash
skein subtask add <tid> st1 --name "改 schema"   --desc "加迁移列并回填默认值" --agent skein-executor --skills db-migration --check "迁移可回滚; 新列有默认值"
skein subtask add <tid> st2 --name "改调用站点" --desc "调用站点透传新字段" --agent skein-executor --deps st1 --check "新字段透传响应; 旧字段不删"
skein subtask add <tid> st3 --name "加测试"     --desc "覆盖新旧字段两条路径" --agent skein-executor --deps st1 --check "覆盖新旧字段两条路径"
```

`sid`/`--name`/`--desc` 三者必填 (缺一 argparse 报错); `--agent`/`--deps`/`--check`/`--skills` 选填 (`--agent` 省略默认 `skein-executor`)。

- `depends_on` 是唯一显式边源: st2/st3 依赖 st1 → st1 未 done 前不 ready; st2/st3 互不依赖 → 可并行 (并发上限 2)。
- 并行与否只看这张 DAG, 不靠脚本猜写文件重叠 (拆分时把真正有序的关系写进 `--deps`)。
- 运行态看 `skein subtask list <tid>` (脚本落盘), 不看任何 md 文件。

**统筹学: 拆 DAG 求最短工期 (min makespan)** — exec 的就绪批由脚本按**拓扑深度**优先派 (下游链长者先跑), planning 只需把下面几件事做对, 脚本自会调度:
- **协议先行, 后并行 (最优拆法)** — 先识别 subtask 间**共享契约** (接口签名 / 数据结构 / 类型 / API 格式 / DB schema), 把「定契约」抽成单个前置 subtask; 所有实现 subtask 只 `--deps` 这个契约 subtask、彼此不互挂 → 契约 done 即全批并行。反模式: 让实现 A 依赖实现 B 只因 "B 先写了接口" —— 应把接口提成独立前置, A/B 同 `--deps` 它并行, 别串成链。
- **压关键路径, 别串成一条链** — 无真实依赖的 subtask 禁互挂 `--deps` (伪依赖会拉长关键路径、扼杀并行); 有序的才连。把长任务尽量前置、让下游能早并行。

## 复杂度天花板: cold-start 大需求 (承接 SKILL.md 🛑 天花板表)

SKILL.md 天花板表命中任一即拆多 task。cold-start 维度的细化判据:

| 天花板信号 | 判据 | 动作 |
|---|---|---|
| 复合嗅味 ("X and Y and Z") / 多独立能力 / subtask 会 >8 | capability 按**用户行为**拆 (非技术层); 阈值 8 与 liza size 门 3-8 **同号合并**, 非新增阈值 | 拆多 task: `skein create <super-id> --kind supertask` + 各 child `--parent <super-id>` |

- **capability ≠ 技术模块** — capability 是用户行为 (「下单」「退款」), 非技术层 (「DB层」「API层」)。按技术层拆 = 跨层耦合依旧的假拆; 按用户行为拆 = 真独立可并。
- **walking skeleton 优先** — 拆完能力域后, 第一个 task 强制**端到端最薄能跑通** (验证数据流 / 契约 / 部署链路假设), 非铺平所有能力域。假设证伪早返工, 比铺平再发现省。

## 测试反模式 (subtask 验收标准编写参考)

> skein 不强制 TDD (由 subtask 验收标准约束行为正确性, 非先写测试再写实现)。本段仅作**验收标准编写参考** — 识别出验收标准若隐含以下反模式即判定验收设计本身有问题。

| 反模式 | 症状 | 为何坏 |
|---|---|---|
| **implementation-coupled** | 测试 mock 内部 / 测私有方法 / 走 side channel | 测试绑实现细节, 重构即崩 (实现一改, 行为没变但测试全红) |
| **tautological** | assertion 重算 expected 用了被测的同一段代码逻辑 | 永真, 测了等于没测 (用同代码算期望值 = 自己证明自己对) |
| **horizontal-slicing** | 全测试先写完再一口气全实现 | 不是一片片推进, 违反 tracer-bullet (端到端最薄先跑通); 一处设计错波及全测试集 |

**pre-agreed seam 纪律**: 写测试 (或写验收标准) 前, 先写下 seam 并确认 — 即被测单元与外部交互的边界在哪 (依赖注入点 / 接口契约)。**未确认 seam 不写测试**。skein 落地: subtask 的验收标准 checklist 即隐含 seam (验收标准写明「输入 X → 输出 Y」, 就是把 seam 钉死, 实现如何达成不约束)。

> 验收标准设计的判断: 若验收标准只能用「mock 内部 / 测私有」才能验证 → seam 没定清, 回 design.md 重定接口边界再写验收。
