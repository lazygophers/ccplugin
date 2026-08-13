---
type: domain
area: tech
sub: go
created: 2026-06-09
tags: [go, tips]
---

# Go tip: defer 性能

defer 在 Go 1.14+ 已接近 inlined 函数调用开销, 热路径仍建议手动展开。
