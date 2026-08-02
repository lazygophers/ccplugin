# docs + examples 示例仓迁移 — 详细设计

架构 / 数据流 / 关键取舍 / 技术选型 (不含调度图, 调度归 task.json):

## 1. 示例仓为什么必须迁 (不是可选项)

`docs/examples/sample-skein/spec/` 是新用户第一眼看到的结构。停在旧两层结构会**直接教错人** —— 用户照着建出 `core/` `recall/` 目录, 然后发现命令报错或行为不符文档。

而且示例仓不只是「迁」: `product` 与 `map` 是本轮全部新增价值所在, **没有示例等于没人会用**。一个空的 `product/` 目录不构成示例。

## 2. 示例仓目标结构

```
sample-skein/spec/
├── index.md                      # 生成物 (reindex 产)
├── backlinks.md                  # 生成物
├── rules/
│   ├── index.md                  # 生成物
│   ├── git/order-query.md        # 原 core/git/* → inclusion: always
│   ├── arch/order-create-api.md  # 原 recall/arch/* → inclusion: auto
│   ├── domain/order-create-api.md
│   └── test/order-pay.md
├── product/                      # ★ 新增
│   ├── index.md
│   └── order/
│       ├── overview.md           # 该域是什么 / 边界 / 与其他域关系
│       └── create-flow.md        # 现状行为, 带 anchors
└── map/                          # ★ 新增
    ├── index.md
    └── api/order-handler.md      # 模块职责 / 入口 / 数据流, 带 anchors
```

**示例要覆盖至少三种 `inclusion`** —— `always` / `auto` / `fileMatch` (后者带 `globs`)。这是示例的核心教学价值: 让用户看到同一个 namespace 里可以混放不同加载策略的页。

## 3. 「示例要真的跑通」是硬约束

对示例仓跑 `spec.py reindex`, 必须能生成各 namespace `index.md` + 顶层 `index.md` + `backlinks.md`, 且条数与页内 `## 章节` 数一致。

**理由**: 示例仓的 frontmatter 若写错 (字段名拼错、`inclusion` 值非法), 光看文件是看不出来的 —— 只有跑一遍索引才知道。而一个跑不通的示例比没有示例更糟。

## 4. `.png` 的诚实处理

`docs/skein-flow.png` 需要 mermaid 工具链重生。若环境不可用:

- **如实报告, 只改 `.mmd`**
- **禁提交与 `.mmd` 不符的旧 `.png`** —— 一张过期的流程图会被当成真值读, 比没图更误导

这条写进验收标准, 不作为「尽力而为」处理。

## 5. 关键取舍

| 取舍 | 决定 | 理由 |
|---|---|---|
| 示例仓迁移 vs 重写 | **迁移 + 补新页** | 现有示例内容 (order 域) 是连贯的一套, 重写会丢掉这个连贯性 |
| product 示例域选什么 | **沿用现有 order 域** | 示例仓已围绕 order 建了 rules, product 用同一域才能展示 rules ↔ product 的关系 |
| 是否用 `migrate` 命令迁示例仓 | **用** | 顺便验证 `migrate` 在真实数据上跑得通 (示例仓就是一个小的旧结构库), 一举两得 |
| `.png` 不可重生时 | 只改 `.mmd` + 如实报告 | 过期流程图比没图更误导 |
| 文档预算数值 | 统一写键名不写数字 | 与 `spec-skills-agents-adapt` 同一决策; 写死数字必漂移 |
| docs 与 skill 措辞一致性 | 依赖前一 task 完成后再写 | 两处各说一套比一处滞后更糟 |

## 6. 测试接缝 (seam)

**本 task 无代码改动, 接缝 = 对示例仓跑真实命令 + 结构性 grep。**

- `spec.py reindex` 对 `sample-skein/spec/` 跑通, 断言生成的 index 条数与手数章节数一致
- 用 `migrate` 迁示例仓 —— 同时是 `migrate` 命令在真实数据上的验证
- 结构性 grep: `docs/` + `README.md` + `CONTEXT.md` 内无残留「两层」、无残留 `spec/core/` 路径 (除 migrate 说明处)、无写死预算数值

## 7. 已知风险

| 风险 | 缓解 |
|---|---|
| mermaid 工具链不可用 | 只改 `.mmd` + 如实报告, 禁留不符的 `.png` |
| 示例仓 frontmatter 写错但看不出来 | 硬约束跑 `reindex` 验证 (§3) |
| 用 `migrate` 迁示例仓时暴露 migrate 的 bug | **这是好事** —— 真实数据验证; 若真有 bug 则报回 `spec-migrate` 而非在本 task 绕过 |
| docs 措辞与 skill 措辞不一致 | 依赖 `spec-skills-agents-adapt` 先完成, 以其措辞为准 |
| `reference.md` 命令表遗漏新命令 | 与 `spec.py --help` 输出逐条比对, 不靠回忆 |
