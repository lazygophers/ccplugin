# 领域模块 (领域)

跨项目复用的领域 / 经验 / 方法笔记。

## 路径

`<root>/领域/<area>/<sub>/[<sub2>/]<topic>.md`

- 必须 ≥ 2 级目录 (area + sub 最少)
- `<area>` 预设: `tech` / `life` / `finance` (用户可扩展, 如 `health` / `art`)
- `<sub>` / `<sub2>` 自由分类

## frontmatter

```yaml
---
type: domain
area: tech
created: 2026-06-09
updated: 2026-06-09
tags: [rust, async, tokio]
aliases: [tokio-runtime-notes]
weight: 0.6
---
```

## 示例路径

- `领域/tech/rust/async/tokio-runtime.md`
- `领域/life/habits/sleep-protocol.md`
- `领域/finance/etf/global-allocation.md`

## 禁路径

- `领域/<topic>.md` (缺 sub 级)
- `领域/misc/...` (area=misc 不允许, 必须明确)
