# 修复 dashboard KeyError — PRD

## 目标
_dashboard (skein.py L1785) `c["pct"]` KeyError → 改 `c["spct"]`。card dict 只有 spct key (L1603), 无 pct。

## 根因
pre-existing bug。_dashboard active_tasks 列表引用 `c["pct"]`, 但 card dict 字段名是 `spct`。访问 /__skein__/dashboard → 500。

## 改动
skein.py L1785: `"pct": c["pct"]` → `"pct": c["spct"]`

## 验收
- [ ] curl /__skein__/dashboard 返回 200 JSON (非 500)
- [ ] ast.parse 过
