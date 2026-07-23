# deep-module 设计词表 + ADR 机制

skein 设计阶段的 deep-module 词表 + 难逆决策 (ADR) 记录机制。ask-matt `/codebase-design` (deep-module 词表) + `/domain-modeling` (ADR) 同源, skein 原生化。**存在则用增强 / 否则原生**: 已装这两个 skill → 评 design.md 时可选委托作词表/ADR 增强 (原生为主); 未装则用本文件原生词表兜底。

- **用途一 (词表)**: design.md 写架构/取舍时, 用这套词描述模块边界与质量。
- **用途二 (ADR)**: 难逆决策实时记在 design.md「取舍」/「可能性分支」段, 防遗忘、防回退代价高的决策无痕迹蒸发。

## deep-module 词表

| 词 | 定义 | skein 落点 |
|---|---|---|
| **module** | 行为的内聚单元, 对外是一个接口 | design.md「架构」基本单元 |
| **interface** | 模块对外暴露的契约 (签名/类型/协议) | 契约 subtask 定死的共享契约 (skein-plan L99) |
| **depth** | deep module = 多行为背后小接口; shallow = 大接口少行为 | design.md「取舍」评每个模块 deep/shallow |
| **seam** | 可替换/可测试的接缝 (依赖注入点 / 适配器边界) | subtask 拆分沿 seam 切, 各 subtask 落 seam 一侧 |
| **adapter** | 跨 seam 的适配层 (协议转换/外部系统封装) | 跨子系统 task 的契约 subtask 常是 adapter |
| **leverage** | 小改动撬动大行为 (改一个 deep 接口影响多调用方) | design.md「可能性分支」标高 leverage 点 |
| **locality** | 相关行为聚一处 (改一个功能只动一处) | subtask scope 边界判据 (locality 高归一 subtask) |

**原则**: 倾向 deep module + clean seam + high locality — 少行为大接口的 shallow module + 散落多处的行为是设计债。

### 设计判据 (ask-matt `/codebase-design` 原则, 评 design.md 架构时逐模块过)

| 判据 | 含义 | 用法 |
|---|---|---|
| **deletion test** | 删掉这个模块, 复杂度是否消失? | 不消失说明模块划错了边界 (复杂度被假封装, 实际散在别处) |
| **interface is the test surface** | 接口即测试面 | 小接口 = 少测试 + 易测; 大接口 = 必然测不全 |
| **one adapter = hypothetical seam, two = real** | 第一个适配器只是假设的接缝, 第二个才证明接缝真实存在 | design 勿因「未来可能要换」就提前抽 adapter (YAGNI); 出现第二个真实适配器才坐实 seam |

**为可测性设计三原则**: accept deps (依赖作参数注入, 不在内部 new) / return results (返结果不直接改全局状态) / small surface (对外暴露最小接口面)。

**设计接口三问 (评每个新接口时问)**: 能减方法吗? 能简化参数吗? 能把复杂度藏到接口后面吗? 三问都答「否」→ 接口大概率过度设计或 leak 了实现细节。

## ADR (Architecture Decision Record) 机制

### 触发

**三者全中才记 ADR** (防 ADR 滥用):
1. **hard-to-reverse** (难逆, 回退代价高)
2. **surprising** (非显而易见, 别人看了会问「为什么」)
3. **real-trade-off** (有真实取舍, 不是显然最优解)

只中一两条不记 — 显而易见或无取舍的决策不配 ADR, 记了只是噪音。

补充典型 (三者全中时的常见类型): 改契约 / 删旧路径 / 选型定死 / 数据模型定形。

### 记录到哪

`.skein/task/<id>/design.md` 的「取舍」或「可能性分支」段 (轻量, 不单建 ADR 目录); 特别关键的 (跨 task 复用) finish 时 sediment 进 core spec。

### 格式 (每条 ADR)

```
### ADR: <决策标题>
- **背景**: 为什么需要决策
- **决策**: 选了什么
- **否决**: 否了什么 (备选 + 为何否)
- **后果**: 这个决策带来的约束/影响
- **难逆度**: 高/中 (回退代价)
```

### 与 sediment 分工

ADR 是 task 内 design 阶段的实时记录; sediment 是 finish 后抽取的可复用规则。ADR 是 sediment 的原料池 — finish 时挑跨 task 复用的 ADR sediment, 其余随 task 归档。

---

词表+ADR 是 design.md 的工具非额外负担 — 简单 task 用不上不勉强, 跨子系统/破坏式重构/选型类 task 必用。

## 不引入的工件 (YAGNI 边界)

- **术语单一真值源落 prd.md 词汇段 + spec recall, 不另建 CONTEXT.md glossary** — 与现有工件重叠, YAGNI。
- **不产 HTML 可视化报告** — skein 工件范式是 `.skein/` 下的 markdown (prd / design / findings / spec), 非 HTML 报告。
