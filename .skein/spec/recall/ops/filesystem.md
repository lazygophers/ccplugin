---
title: filesystem
layer: recall
category: ops
keywords: [write,incremental,diff,optimization,delete,soft-delete,trash,recovery,filesystem,move,platform,agnostic]
status: active
---

## 写盘前 diff 检查，内容无变则 skip

### 触发场景
修改 task.json 或派生文件后，需要持久化，但担心无谓 IO/mtime 抖动影响监控。

### 陷阱-正解
**陷阱**：每次都写，即使内容无变化。
**正解**：写前 diff，内容相同则跳过写，减少 IO 与 mtime 变更。

### 规则
_write_if_changed() 先比对，相同则 skip。

### 关联
data/atomic-write-single-entrance (C7)

## 删除 task 软删入 trash（可恢复）

### 触发场景
删除 task 或旧看板日志。

### 陷阱-正解
**陷阱**：直接 rm，不可恢复。
**正解**：软删入 .skein/trash/<id>.<YYYYMMDD>/，可恢复; 单 subtask 直接删。

### 规则
skein.py:186 定义 trash 路径；:673/:697-711 软删逻辑。

### 关联
ops/soft-delete-restore

## 文件移动用 shutil.move（跨平台）

### 触发场景
移动文件到 trash 或归档。

### 陷阱-正解
**陷阱**：用 os.rename，win/mac 行为不一。
**正解**：用 shutil.move；目标存在先清后移。

### 规则
skein.py:709-711 (trash), :724 (archive)。

### 关联
ops/platform-agnostic-filesystem
