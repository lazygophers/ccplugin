---
updated: 2026-06-09
rewrite-version: 1
authored-by: trellisx-spec
mode: optimize
---

# Cross-Layer Rules

何时被读: 改动 ≥ 2 层 (e.g. API + service + DB) 时
谁读: trellis-implement sub-agent; main agent
不遵守的代价: 跨层耦合泄漏, 下次跨层改动连锁失败, 测试无法独立

---

## MUST — 改前列契约

改 ≥ 2 层 MUST 先列每层契约边界:

```
Layer A → Layer B:
  输入格式: <exact type/schema>
  输出格式: <exact type/schema>
  错误: <possible errors>
```

缺任一层契约边界 → 禁开始编码。

验证: 契约边界文档必须存在, 缺一不改。

## MUST — 显式接口

跨层调用 MUST 走显式接口 (function / class method / API contract), 禁直接读对方内部实现字段。

验证: `grep -rE '<对方内部字段名>' src/ | grep -v 'interface\|contract\|types'` 必须 0 行。

## MUST — 验证单点

每个数据验证 MUST 在入口层执行一次, 禁在多层重复验证同一字段。

验证: `grep -rE '<同一字段验证逻辑>' src/ | wc -l` 必须 ≤ 1。

## MUST — 格式显式转换

层边界处 MUST 显式转换数据格式, 禁隐式假设 (e.g. 日期格式 / null 处理 / 类型)。

验证: 跨层数据流经的每个边界 MUST 含显式 transform / adapter 调用。

## MUST — Security Filter Pipeline

当流程涉及 URL 摄取 / HTML 处理 / 自由文本写入时:

1. URL 输入 MUST 经 `url_security.is_safe()` 检查 (SSRF / metadata host check) 后才可 fetch
2. 抓取的 HTML/markdown MUST 经 `html_sanitize.sanitize()` 后才可继续处理
3. 最终文本 MUST 经 `masking.mask()` 后才可写盘
4. 过滤顺序 MUST 为: `url_security → fetch → html_sanitize → masking → write`, 禁重排
5. `url_security` 失败 MUST fail-closed (拒绝, 禁不带检查重试)

## MUST — 改后必验

实现后 MUST 验证:

- [ ] 每个边界用边界值测试 (null / empty / invalid)
- [ ] 错误处理在每个边界独立可测
- [ ] 数据 round-trip 存活验证 (输入 → 穿越所有层 → 输出 一致)

## 禁止

- 禁组件直接依赖数据库 schema → 每层仅知相邻层
- 禁多层分别实现同一逻辑 → 入口层一次, 下游信任
- 禁跳过边界格式转换 → 显式转换必须存在

## Checklist

改前:
- [ ] 列出完整数据流 (Source → Transform → Store → Retrieve → Display)
- [ ] 标注所有层边界
- [ ] 每个边界定义输入/输出格式
- [ ] 确定验证发生在哪一层

改后:
- [ ] 每边界边界值测试通过
- [ ] 每边界错误处理可独立触发
- [ ] 数据 round-trip 一致
