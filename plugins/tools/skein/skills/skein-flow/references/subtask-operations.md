# Subtask 操作规范

新增 / 自愈修复 / check 修复 / 并入补充 — 四种 subtask 操作场景的触发条件、命令格式、约束与一致性保证。

---

## 1. 四种场景总览

| 场景 | 触发时机 | 谁发起 | task 状态 | 典型数量 |
|---|---|---|---|---|
| **规划新增** | plan 阶段，brainstorm + grill 后拆分子任务 | skein-flow plan 阶段 | 待处理 (pending) | 多个，构成初始 DAG |
| **自愈修复** | exec 阶段，subtask 失败后的一线修复 | skein-flow exec 阶段 (main 自主) | 进行中 (active) | 1 个 (定点小缺陷) |
| **check 修复** | check 阶段，验证失败 / 检出冲突后 | skein-flow check 阶段 (需用户确认方向) | 进行中 (active，回炉) | 1~多个 (一冲突一 subtask) |
| **并入补充** | 新 flow 进来，判为对现有 active task 的补充 | skein-flow (main 裁定) | 进行中 / 待处理 | 按补充范围定 |

---

## 2. 场景一：规划新增 (Planning Add)

### 2.1 触发条件

- task 处于**待处理** (pending) 态
- 完成 brainstorm 需求澄清 + grill 硬门评审
- 需要把任务拆分为可并行 / 有依赖的 subtask

### 2.2 操作命令

```bash
skein subtask add <tid> <sid> \
  --name "<子任务名>" \
  --desc "<一句话描述>" \
  --estimate <小时数> \
  [--deps <sid1>,<sid2>] \
  [--check "验收1;验收2;验收3"] \
  [--skills "skill1,skill2"]
```

### 2.3 字段说明

| 参数 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `<tid>` | ✅ | - | 目标 task id |
| `<sid>` | ✅ | - | subtask id (kebab-case，task 内唯一) |
| `--name` | ✅ | - | 子任务名称 (简短) |
| `--desc` | ✅ | - | 子任务描述 (一句话) |
| `--estimate` | ✅ | - | 预计工时 (小时, 正数)，按本 subtask 实际要做的事估；见 `estimate-gate.md` |
| `--deps` | ❌ | (空) | 前置依赖 subtask id 列表，逗号分隔 |
| `--check` | ❌ | (空) | 验收标准 checklist，分号分隔 |
| `--skills` | ❌ | (空) | 需加载的 skill，逗号分隔 |

### 2.4 约束

- 必须在 `skein confirm` 之前完成 (确认后禁增删 subtask)
- 至少 1 个 subtask 才能 confirm
- 不能形成环 (DAG 一致性约束，见第 6 节)

---

## 3. 场景二：自愈修复 (Exec Self-healing Add)

### 3.1 触发条件

- task 处于**进行中** (active) 态
- 某个 subtask 执行失败 (`subtask fail`)
- 根因是**独立可修单元** (缺前置产物 / 共享依赖坏 / 需单独定点修)
- 不属于「定点小缺陷可原地重派」的情况

### 3.2 操作命令

```bash
skein subtask add <tid> <fix-sid> \
  --name "修复:<根因简述>" \
  --desc "定点修<失败sid>根因: <具体原因>" \
  --estimate <小时数> \
  --deps <失败sid的所有前置>
```

### 3.3 关键要点

- **挂前置位置**：修复 subtask 的 `--deps` = 失败 subtask 的原前置 (即修复 subtask 插在失败 subtask 前面)
- **失败 subtask 依赖修复 subtask**：失败 subtask 的 depends_on 自动补上修复 sid (脚本自动维护？不，需手动声明 — 实际上修复 subtask 的输出是失败 subtask 需要的输入，所以失败 sid 要依赖 fix-sid)
- **完成后重派**：修复 subtask done 后，`skein subtask start <tid> <失败sid>` 重派原 subtask

### 3.4 约束

- 必须在**本 task scope 内** (完成原范围，非扩 scope)
- 同一 subtask 累计自愈 ≤ 2 轮
- 修复 subtask 命名带 `修复:` 前缀，便于识别
- 禁止跳过自愈直接回传人工 (一线修复必须做)

### 3.5 与原地重派的分流

| 情况 | 做法 |
|---|---|
| 定点小缺陷 (实现 bug / 局部漏改) | 原地重派 `skein subtask start <tid> <sid>`，不新增 subtask |
| 根因是独立可修单元 | 插修复 subtask，修完重派原 subtask |
| 根因超本 task scope | 停手回传，走 root-cause-protocol |

---

## 4. 场景三：Check 修复 (Check Failure Fix Add)

### 4.1 触发条件

- task 处于**进行中** (active) 态 (check 未过 ≠ 状态回退，task 保持进行中)
- skein-checker 报告 FAIL / 检出冲突
- **已回 planning 重确认**：main 重新 grill / AskUserQuestion 与用户敲定修复方向
- 用户确认方向后，才补 subtask

> 🛑 **必经门**：禁跳过确认直接补 subtask。方向确认 = 用户拍板，不是 main 自己决定。

### 4.2 操作命令

按错误性质分档：

#### 4.2.1 孤立失败 (单点 lint/type/test/契约 fail)

```bash
skein subtask add <tid> <fix-sid> \
  --name "修复: <失败点简述>" \
  --desc "<报错原文 / file:line>" \
  --estimate <小时数> \
  --deps <失败源 subtask sid>
```

#### 4.2.2 一致性冲突 / 根因跨 subtask

```bash
# 一冲突一 subtask，逐条覆盖
skein subtask add <tid> <fix-1> \
  --name "修复冲突1: <冲突点>" \
  --desc "<冲突描述 + 涉及文件>" \
  --estimate <小时数> \
  --deps <源 sid1>,<源 sid2>

skein subtask add <tid> <fix-2> \
  --name "修复冲突2: <冲突点>" \
  --desc "..." \
  --estimate <小时数> \
  --deps <源 sid3>
```

#### 4.2.3 方案性 / 设计缺陷

先走 planning 补充或重设计 design.md + 修 prd + 改契约，再按新设计 `subtask add` 重拆或补子任务。

### 4.3 约束

- 必须先与用户确认修复方向 (grill / AskUserQuestion)
- 新增修复 subtask 的 `depends_on` 挂失败源 subtask (已 done) → 立即 ready
- 冲突必须逐条覆盖，零冲突才放行 finish
- task 全程保持「进行中」态，不建新 task、不改状态

---

## 5. 场景四：并入补充 (Merge-in Add)

### 5.1 触发条件

- 新 flow 进来，判为**对现有 active task 的补充** (而非全新 task)
- 判定依据：与现有 task 目标一致 / 改动范围重叠 / 属于同一交付单元
- 由 skein-flow main 裁定 (不准用 AskUserQuestion 问用户)

### 5.2 操作命令

```bash
skein subtask add <tid> <new-sid> \
  --name "<补充任务名>" \
  --desc "<补充描述>" \
  --estimate <小时数> \
  --deps <合适的前置 sid> \
  [--check "验收项"]
```

### 5.3 关键要点

- **并入 = 归并到现有 task**，不新建 task
- 新 subtask 的 `--deps` 挂到合适位置 (依赖已有的相关 subtask)
- 如果 task 已经在「进行中」态，新 subtask add 后若 deps 全 done 则立即 ready，下一轮 claim exec 即派

### 5.4 约束

- 必须是**相关工作**才能并入 (目标一致 / 范围重叠)
- 不相关的独立工作 → 新建 task，不并入
- 不准拿不准就问用户 (main 自己裁定)

---

## 6. DAG 一致性约束 (加 subtask 后不能形成环)

### 6.1 环检测

每次 `subtask add --deps` 时，脚本自动检测：

- 从新 subtask 出发，沿 depends_on 边递归遍历前置
- 如果能绕回自己 → 形成环 → 硬拒，报错退出

### 6.2 常见环陷阱

| 陷阱 | 示例 | 正确做法 |
|---|---|---|
| 互相依赖 | A.deps=[B], B.deps=[A] | 拆出共享前置 C，A.deps=[C], B.deps=[C] |
| 修复 subtask 挂错 | 修复 subtask deps=[失败sid] | 修复 subtask deps=[失败sid的前置]，失败sid 依赖修复sid |
| 跨层跳挂 | 下游 subtask 直接 deps 源头，但中间层也依赖它 | 理清楚真实顺序，按层级挂 |

### 6.3 违反后果

- `subtask add` 命令直接失败 (SystemExit)
- 不写入 task.json
- 需要调整 `--deps` 后重试

---

## 7. 复杂度天花板

### 7.1 触发阈值

- **> 8 个 subtask** → 提醒拆 task
- **跨子系统** (改动涉及多个独立模块 / 服务 / 领域) → 提醒拆 task

### 7.2 判定逻辑

| 情况 | 建议 |
|---|---|
| ≤ 8 subtask 且单子系统 | 正常，单 task 承载 |
| > 8 subtask 但单子系统 | 提醒：考虑拆成多个 task，用 task 级 `--deps` 串 |
| 跨子系统 (无论数量) | 提醒：按子系统拆 task，各管各的域 |
| > 8 subtask 且跨子系统 | 强烈建议拆：一系统一 task，task 级 DAG 串 |

### 7.3 拆 task 的方式

- 新建独立 task：`skein create <new-tid> --name "..." --desc "..." --deps <原tid>`
- 用 task 级 `--deps` 建立先后关系
- 每个 task 内部 subtask ≤ 8，各司其职

### 7.4 为什么是 8

- 人类认知负载上限：同时追踪 7±2 个单元
- 超过 8 个 subtask，DAG 复杂度指数上升，排错困难
- 拆成 task 级 DAG，每层都在认知范围内
