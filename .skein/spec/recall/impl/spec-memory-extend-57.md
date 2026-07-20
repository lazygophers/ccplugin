---
title: config 预算复用模式
layer: recall
category: impl
keywords: [config,预算,budget,core_budget,懒读取,fallback,热修改]
source: spec-memory-extend
authored-by: skein-spec
created: 1784557936
status: active
related: [spec-three-layer]
updated: 1784557936
---

# config 预算复用模式

## 铁律

MUST：预算类常量（如 CORE_BUDGET）应迁移到 config.yaml 使用户可配置（默认 1000）

MUST：实现 `core_budget() -> int` 模式：懒读取（每次调用时读 config 支持热修改）+ 局部 `from skein import _yaml_load` 避免循环依赖 + 缺失/非数字时 fallback 默认值

MUST：后续 spec 阈值类常量走 config 而非硬编码

## 反例表

| 禁 | 改为 |
|---|---|
| `CORE_BUDGET = 1000` 硬编码常量 | 迁移到 config.yaml + core_budget() 函数 |
| 启动时一次性读 config 固化 | 每次调用时读，支持热修改 |
| config 缺失时崩溃 | fallback 到默认值 |
| 直接 `import skein.spec` 导致循环依赖 | 局部 import `_yaml_load` |

## 模式

```python
def core_budget() -> int:
    """懒读取 config 中 core_budget，支持热修改 + fallback"""
    from skein import _yaml_load
    cfg = _yaml_load()
    val = cfg.get("core_budget", 1000)
    try:
        return int(val)
    except (ValueError, TypeError):
        return 1000
```

## 适用
- 所有预算/阈值类常量
- 需要用户可配置的数值
- 热修改需求场景

## 关联
- spec 三层架构（core 预算控制）
