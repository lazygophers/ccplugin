# deep-module 设计词表 + ADR 机制

skein 设计阶段的 deep-module 词表 + 难逆决策 (ADR) 记录机制。ask-matt `/codebase-design` (deep-module 词表) + `/domain-modeling` (ADR) 同源, skein 原生化。

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

## ADR (Architecture Decision Record) 机制

### 触发

难逆决策 — 改回去代价高。典型: 改契约 / 删旧路径 / 选型定死 / 数据模型定形。

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
