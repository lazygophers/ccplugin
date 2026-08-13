# writing-for-agents — agent 文档写作方法论

skein 所有 skill / agent / reference 的编写、优化、精简都应参考此文。核心理念：**agent 每次走同一流程，而非产出同一输出**。

## Context pointer

**Context pointer** = agent 上下文中引用 out-of-context 材料的引用行，编码了到达条件。skill 的 `description` 是一个 pointer；`AGENTS.md` 中指向某文档的一行也是。

pointer 的**措辞**（不是目标文件）决定 agent 何时到达材料、多可靠。必达材料放在弱措辞 pointer 后面 = 方差 bug：先锐化措辞，只有锐化失败才 inline。

pointer 做两件事：声明材料是什么 + 列出触发到达的 **branch**（branch = 文档处理的独立分支，不同 run 走不同路径）。always-loaded pointer 的每个词每轮都花 token，prune 比 body 更狠：

- **前置 leading word** — pointer 的触发工作在首词
- **一 branch 一触发** — 同义词重命名单 branch = 写了两遍，合并
- **删 body 已有的 identity**

## 两类负载

每加一个文档/pointer 花一种预算：

- **Context load** — always-loaded 材料对 agent 窗口的成本（AGENTS.md 行、skill description），无论是否触发都花 token 和注意力
- **Cognitive load** — 对人的成本：哪些文档存在、何时取。人是 index；不可最小化的代价，花在判断重要的地方，移除不重要的

仅经 pointer 到达的材料逃 context load，代价是 pointer 自身一行；无 pointer 的材料纯靠 cognitive load。

## Information hierarchy

文档由两类内容组成：**step**（agent 执行的有序动作）和 **reference**（按需查阅的定义/规则/事实）。核心决策是每段内容在阶梯上的位置：

1. **In-file step** — 主层：agent 做什么，有序
2. **In-file reference** — 按需查阅。flat peer-set（一审查的全部规则在同一层）是合法结构
3. **Disclosed reference** — 推出到独立文件，经 pointer 到达，仅 pointer 触发时加载

**下推不够 → 顶层膨胀；下推过度 → 藏了 agent 实际需要的材料。**

**Progressive disclosure** = 沿阶梯下移（出主文件、进 pointer）以保顶层可读。主要不是 token 优化，是保护层级。**分支测试**：每分支都需要的 inline，只有部分分支到达的推到 pointer 后面。有 step 的文档中，该 disclose 的 in-file reference 会埋没 step — 是方差杠杆。

**Co-location** = 同文件内：定义 + 规则 + 注意事项聚在一个 heading 下，不散放。

**Sprawl** = 文档过长（即使每行都活跃且唯一）。注意力被稀释。治法：disclose reference behind pointer，按 branch 或 sequence 拆分。

## Completion criterion

每个 step 以 **completion criterion** 结尾。两个属性使它成为杠杆：

- **Clarity** — agent 能区分 done / not-done？模糊边界（"理解达成"）引发 **premature completion**：提前结束。后面的 step（**post-completion steps**）提供拉力；criterion 的清晰度是阻力。先锐化边界（局部且便宜）；不可逆地模糊且观察到赶工时，拆 sequence 藏后续 step — 但只跨真实 context boundary 才有效（handoff / subagent dispatch）。
- **Demand** — 要求多少？"每个改动 model 都要核对" 比 "产出改动清单" 强。Demand 驱动 **legwork** — agent 在工作内挖的深度，潜伏在措辞中而非写成独立 step。

最强 criterion 同时 checkable + exhaustive。

## Leading word

**Leading word** = 模型预训练中已有的紧凑概念，agent 运行文档时用它思考（_tracer bullet_ / _frontier_ / _fog of war_ / _seam_）。作为 token 重复，不是句子 — 积累分布式定义，用最少 token 锚定一整片行为。

锚定两次：body 中 _execution_（每次出现都触发同一行为）；pointer 中 _invocation_（prompt + 文档 + 代码库共用同一词时，agent 更可靠到达材料）。

**Negation 是失败模式**：禁止性措辞把被禁行为拉进 context，使其更可用。_别想大象_ → 大象占满。用 **positive** — 状态目标行为（"写一行注释"），让被禁的永远不被说出。禁令只在无法正面表述时作为硬护栏，且配正面目标。

## Pruning

- **单一真值源** — 一个含义一处。**Duplication** = 同含义多处，花维护 + token，虚胖 ladder 排名。（与 leading word 的反面：leading word 故意重复 token 从不重复含义。）
- **环境也是真值源** — `package.json` scripts、config、目录布局、`--help` 输出。重述环境的文档是 **cache**：只在查询昂贵时赚回负载。cache 查不到的：未写的约定、选择的原因、config 不说的陷阱。
- **每行查 relevance** — 是否仍与文档职责相关？失去 relevance 的方式：从不相关（纯叙述 / 该 disclose 的 branch）或 stale。短文档更容易保持 relevant。无 pruning 纪律的默认命运 = **sediment**：stale 层堆积。
- **逐句 hunt no-op**：模型默认已遵守的指令 = 花负载说废话。测试 — 是否改变默认行为？— 是 model-relative。失败时删整句而非修剪。

## 何时拆分

拆分花两类负载之一，只在 cut 赚回时拆：

- **按 sequence** — 拆一段 step，post-completion steps 诱 agent 赶工当前。藏起来驱动更多 legwork。反面：merge sequence 暴露后续 step 诱 premature completion。
- **按 invocation** — skill 专属：见 skein-flow SKILL.md 的 $1 路由。
