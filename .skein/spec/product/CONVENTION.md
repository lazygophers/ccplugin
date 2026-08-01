# product namespace 约定

## 目的

`product/` namespace 存放**系统现状 (state)** 的描述文档，与 `task/<tid>/prd.md` (变更请求 delta) 相对：

- **prd.md**: 一次性变更请求，做完归档
- **product/**: 长期演化的系统真值，随 task 完成被更新而非追加

## 页面组织

### 按功能域切页

按**功能域** (而非代码模块、用户旅程) 切分页面：

- ✅ `task-lifecycle/` - 任务生命周期相关
- ✅ `spec-memory/` - 规则记忆相关
- ✅ `cli/` - 命令行界面相关
- ❌ `scripts/skein.py` - 按代码模块切 (重构即失效)
- ❌ `建-task-到完成/` - 按用户旅程切 (跨域难定位)

### overview.md 约定

每个功能域固定一页 `overview.md`，描述：

- 该功能域是什么
- 边界范围
- 与其他域的关系

其余细节页按需添加。

### 文件路径格式

```
spec/product/<功能域>/<主题>.md
```

例如：
- `spec/product/task-lifecycle/overview.md`
- `spec/product/task-lifecycle/state-machine.md`

## Frontmatter 字段

```yaml
---
title: <主题名>
category: <功能域>
keywords: [<关键词列表>]
status: active
inclusion: auto
anchors: <相关代码路径,逗号分隔>
---
```

### anchors 字段

`anchors` 用于 finish 阶段回写时反查"该 task 要改哪页"：

- **格式**: 逗号分隔的代码路径
- **用途**: 当 task 的 git diff 触及这些文件时，反查到对应的 product 页作为候选更新页
- **维护**: 代码重构导致路径失效时，`maintain` 会报告断链（product 只报告，不自动 archive）

## 使用场景

### 写规范

系统功能设计、决策理由、架构约束等**稳定的知识**进 `product/`。

### 暂存/临时

临时决策、探索性想法、待验证方案 → 进 `task/<tid>/prd.md`，验证完成后再 sediment 到 `product/`。

### 持续更新

功能演进时，用 `amend` 改写对应章节（不追加，避免变成日志）。

## 与其他 namespace 的区别

| namespace | 内容类型 | 典型判据 |
|---|---|---|
| `rules/` | 规则、约定、纪律 | stale → archive |
| `product/` | 系统现状描述 | **禁自动 archive**，anchors 失效只报告 |
| `map/` | 代码骨架 (现算) | anchors 失效 → archive |
| `external/` | 外部参考 | deprecated → archive |

## 维护原则

1. **只写当前真值** - 历史版本交 git + archive，正文不留"已废弃"内容
2. **按域切页** - 一个 task 的改动通常落在一个域内，避免改多页
3. **anchors 可检测** - 路径失效会被 `maintain` 抓到，不是静默 stale
4. **长而正确胜过短而残缺** - 页越写越长没问题，不自动清理
