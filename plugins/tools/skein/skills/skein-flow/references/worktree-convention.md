# Worktree 自适应约定

use_worktree 配置、探测方式、两种模式 (worktree 模式 vs 原地模式)、工作目录定位规则、以及 exec/check/finish 三阶段的切换约定。

---

## 1. use_worktree 配置

### 1.1 配置项

| 项 | 值 | 说明 |
|---|---|---|
| 配置名 | `use_worktree` | 布尔值 |
| 默认值 | `true` | 默认启用 worktree 隔离 |
| 存储位置 | `.skein/config.json` | 仓库级配置 |

### 1.2 探测方式

```bash
skein config --json 2>/dev/null | jq -r '.use_worktree'
# 返回: "true" / "false" / 报错 (无配置)
```

Shell 内判断：

```bash
worktree_enabled=$(skein config --json 2>/dev/null | jq -r '.use_worktree' || echo unknown)
if [ "$worktree_enabled" = "true" ]; then
  # worktree 模式
else
  # 原地模式
fi
```

### 1.3 三态取值

| 探测结果 | 含义 | 模式 |
|---|---|---|
| `true` | 显式启用 | worktree 模式 |
| `false` | 显式禁用 | 原地模式 |
| `unknown` / 报错 | 未配置 / 非 git 仓库 | 原地模式 (安全回退) |

---

## 2. 两种模式

### 2.1 Worktree 模式 (use_worktree=true 且仓库是 git)

| 特征 | 说明 |
|---|---|
| 隔离方式 | 每个 task 一个独立的 git worktree 分支 |
| 工作目录 | `.worktrees/skein-<task-id>/` |
| 主工作区 | 零改动，task 改动全部在 worktree 内 |
| 建 worktree 时机 | `skein start` 时 (就绪→进行中) |
| 销 worktree 时机 | `skein finish` 时 (merge 回主仓后删除) |
| 多子 git | `--repos` 声明的每个子 git 各建一个 worktree |

#### 多子 git 场景

task 跨多个子 git 时 (planning `--repos` 声明)：

```
skein start 为每个声明子 git 各建 worktree:
.worktrees/skein-<id>/<子git名1>/
.worktrees/skein-<id>/<子git名2>/
```

- `skein repos <id>` 可查清单
- 派 subtask 时 dispatch prompt 必须指名该 subtask 落在哪个子 git 的 worktree
- 不同子 git 改动天然隔离，可并行派
- 合计并发仍 ≤ max_active
- finish 逐子 git commit→merge，某子 git 冲突则该 task 留 `进行中` 供修复后重跑

### 2.2 原地模式 (use_worktree=false 或非 git)

| 特征 | 说明 |
|---|---|
| 隔离方式 | 无隔离，直接在当前仓库改动 |
| 工作目录 | 仓库根目录 (当前工作目录) |
| 主工作区 | 直接改动，task 完成后也留在原地 |
| task.worktree 字段 | `null` |
| finish 流程 | 仅 commit (无 merge / 销 worktree 步) |

---

## 3. 工作目录定位

### 3.1 真值来源

**工作目录真值一律以 task 的 `worktree` 字段为准**：

- `worktree` 非 null → worktree 模式，路径 = `worktree` 字段值
- `worktree` = null → 原地模式，路径 = 仓库根

> 不要用 `skein config` 的结果直接判，要用 task 的 `worktree` 字段。因为 task 一旦 start，worktree 路径就固定了，即使配置后来改了也不影响在途 task。

### 3.2 获取方式

```bash
# 方式一：list --json 批量取 (推荐，省 token)
skein list --status open --json | jq '.[] | {id, worktree}'

# 方式二：单 task 取
skein task show <tid> --json | jq -r '.worktree'
```

### 3.3 定位规则 (优先级)

```
工作目录 = task.worktree ? task.worktree : 仓库根目录
```

1. **优先**：task 的 `worktree` 字段 (非 null 时)
2. **回退**：仓库根目录 (worktree 为 null 或未配置时)

---

## 4. 三阶段工作目录切换约定

### 4.1 Exec 阶段

| 模式 | 工作目录 | 操作约定 |
|---|---|---|
| worktree 模式 | task.worktree 路径 | 所有 subagent 共享该 task worktree，subtask 不绑定单独 worktree |
| 原地模式 | 仓库根 | 所有改动直接在仓库根 |

**dispatch prompt 必须包含工作目录信息**：

```
工作目录与范围: <worktree路径 或 仓库根>;
worktree 态 → 只在此 worktree 内改、禁碰主工作区;
原地态 → 在仓库根改、无隔离。
```

**关键约束**：
- fan-out 的所有 subagent 共享 task worktree (不为每个 subtask 单开)
- 默认 1 task 1 worktree，多 worktree 需 opt-in (非自动)
- 改任何文件前先 Read 全文 (读后写硬门)

### 4.2 Check 阶段

| 模式 | 工作目录 | 操作约定 |
|---|---|---|
| worktree 模式 | task.worktree 路径 | skein-checker 在该 worktree 内跑 lint/test/契约验证 |
| 原地模式 | 仓库根 | 在仓库根跑验证 |

**验证与修复都在同一工作目录**：
- checker 只读验证 → 返回 PASS/FAIL 报告
- 修复 agent 在同一工作目录定点改
- 重验也在同一工作目录

### 4.3 Finish 阶段

| 模式 | 工作目录 | 操作约定 |
|---|---|---|
| worktree 模式 | task.worktree 路径 → 主仓 | commit→merge 回主仓→销 worktree |
| 原地模式 | 仓库根 | 仅 commit (无 merge / 销 worktree) |

#### worktree 模式 finish 流程

```
1. 收尾勘察 (在 worktree 内)
   ↓
2. 清悬挂残留
   ↓
3. git add -A + commit (在 worktree 内，auto_commit=true 时自动)
   ↓
4. merge 回主仓 (切到主分支)
   ↓
5. 删除 worktree (销 worktree)
   ↓
6. 标记 task 已完成
```

#### auto_commit 自适应

- 配置名：`auto_commit`
- 默认值：`true`
- `true` → `skein finish` 自动 `git add -A` + commit 再 merge
- `false` → finish 不自动 commit，worktree/原地有未提交改动即**拒绝 finish 报错**
- 探测：`skein config --json 2>/dev/null | jq -r '.auto_commit' || echo unknown`

---

## 5. 各阶段切换速查表

| 阶段 | 进入前状态 | 工作目录 | 谁决定路径 |
|---|---|---|---|
| plan | 待处理 | 主工作区 (不写源码) | N/A |
| start (建 worktree) | 就绪 → 进行中 | 建 worktree | skein start 脚本 |
| exec | 进行中 | task.worktree / 仓库根 | task.worktree 字段 |
| check | 进行中 → 检查中 | 同 exec | task.worktree 字段 |
| check 失败回炉 | 检查中 → 进行中 | 同 exec | task.worktree 字段 |
| finish | 进行中 / 检查中 → 已完成 | worktree → 主仓 | skein finish 脚本 |

---

## 6. 常见注意事项

### 6.1 不要在主工作区改

worktree 模式下，main 和 subagent 都**禁碰主工作区**，所有改动必须在 task worktree 内。

### 6.2 worktree 路径不要硬拼

不要自己拼 `.worktrees/skein-<id>/` 路径，要从 task 的 `worktree` 字段取。因为：
- 多子 git 时路径多一层
- 未来路径规则可能变
- 字段是唯一真值源

### 6.3 非 git 仓库安全回退

如果仓库不是 git (没有 `.git/`)，即使 `use_worktree=true` 也自动回退到原地模式。脚本自动处理，上层不用判断。

### 6.4 finish 后 worktree 已销

task finish 后，worktree 已被删除。不要试图再去访问。需要看改动 → 看主仓的 commit log。
