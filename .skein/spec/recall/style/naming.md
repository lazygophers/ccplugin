---
title: naming
layer: recall
category: style
keywords: [localstorage,persistence,naming,key,style,language,convention,documentation,constant,state,prefix,private]
status: active
---

## localStorage key 统一 skein- 前缀

### 触发场景
需要持久化用户偏好（主题切换、面板打开状态等）。

### 陷阱-正解
**陷阱**：localStorage key 命名混乱 (theme / userData / config)。
**正解**：所有 key 一律 `skein-` 前缀 (skein-theme / skein-dagview)。

### 规则
app.js:102,118 / board/switcher.js:19,22 一致应用。

### 关联
frontend/naming-conventions

## 文档中文 / 代码标识符英文

### 触发场景
编写 docstring 或 frontmatter。

### 陷阱-正解
**陷阱**：混用中英（docstring 英文，description 中文混乱)。
**正解**：文档/描述/docstring 用中文，代码标识符/frontmatter key/commit 术语用英文。

### 规则
全仓一致（utils.py:9 中文 docstring + 英文标识符）。

## 状态常量前缀（S_/SS_）

### 触发场景
定义新状态枚举。

### 陷阱-正解
**陷阱**：PENDING/ACTIVE 无前缀混淆。
**正解**：task 级 `S_PENDING`；subtask 级 `SS_PENDING`；值为中文枚举字符串。

## 私有方法前缀单下划线 (_method)

### 触发场景
编写类内部方法。

### 陷阱-正解
**陷阱**：公私方法无区分。
**正解**：内部/私有方法前缀 `_` (如 _save/_load/_sync)。
