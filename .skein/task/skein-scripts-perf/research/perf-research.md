# SKEIN scripts 性能调研: import 使用面 + IO 热点

> subtask s1 产出。范围: skein.py / spec.py / hooks.py / hooklib.py 的 import 使用面映射 + hooks 热路径 IO 审计 + 优化方案。
> 环境: darwin, python3.11 (实测) + python3.13 (基线已给定)。所有数据 3-8 次取 min/median。

## 基线复核 (端到端 wall time, ms)

| 命令 | min | med | 说明 |
|---|---|---|---|
| `python -c pass` | 14 | 17 | 纯解释器启动基线 |
| `import hooklib` | 19 | 21 | 最轻模块 |
| `import skein` (不跑 main) | 31 | 41 | 含全部顶层 import 依赖链 |
| `import spec` (不跑 main) | 42 | 65 | |
| `import hooks` (不跑 main) | 30 | 40 | |
| `skein.py list` (纯读) | 64 | 69 | |
| `skein.py current` (纯读) | 67 | 72 | |
| `skein.py board` (纯读) | 64 | 79 | |
| `skein.py session-context` | 67 | 71 | hook 热路径 |
| `hooks.py user-prompt` | 29 | 59 | **最频繁 hook** |
| `hooks.py guard` (Write) | 35 | 74 | |
| `spec.py session-start` | 88 | 118 | hook 热路径 |
| `spec.py inject-core` | 60 | 67 | |
| `spec.py list` | 51 | 64 | |

---

## 1. import 使用面映射表

### 1.1 skein.py (3088 行)

> 顶层 imports: `argparse contextlib datetime fcntl json os re shutil subprocess sys time Path typing hooklib`

| 模块 | cum_us (中位) | 使用命令/位置 | lazy 可否 | 预期省 ms |
|---|---|---|---|---|
| `argparse` | 4621 | `main()` 必需;所有子命令 `a: argparse.Namespace` 类型注解 (374/440/476...) | **不可** (main 路由必需;延迟构造需自写 argv 分发,破坏性大) | 0 (保留顶载) |
| `re` | 3335 | 全局 (`SLUG_RE`/`CODE_ID_RE`/fmt/`_validate_prd`/prd_section/check 等正则遍布) | **不可** (全局) | 0 |
| `pathlib.Path` | 2225 | 全局 (root/dir/tasks 路径构造,几乎每命令) | **不可** | 0 |
| `subprocess` | 2044 | `git()` (173,几乎所有写命令) + `_quality_gate` (1334 mypy/pytest) + view/serve (2350 web) + `_exec_argv` (2588) | **部分**: 读命令 (list/current/board/status/pop/ready) 不直接用,但 `Skein()` 初始化已调 `git()` 子进程 (见 §4) | 0~0.5 (写命令必需,读命令走 Skein git 已含) |
| `typing` | 1643 | 全局类型注解 | **不可** (注解遍布;且 `from __future__ import annotations` 下注解不求值,但运行时 cast() 仍需) | 0 |
| `shutil` | 1084 | 仅 `del_` (843-845) + `_archive` (857-858) + setup 迁移 (2712-2854) | **可 lazy** (仅删/归档/setup 用) | ~0.5 |
| `datetime` | 649 | 仅 `del_`/`_archive` 日期目录名 (831/841/853) + serve 日志 ts (2503) | **可 lazy** (同上,低频命令) | ~0.3 |
| `contextlib` | 266 | `@contextlib.contextmanager` 装饰 `_workspace_lock` (110) + setup `redirect_stdout` (2833/2846) + serve `asynccontextmanager` (2441 局部 import) | **部分**: redirect_stdout 可局部;但 contextmanager 装饰器在模块级 (110),改 lazy 需重构 `_workspace_lock` | ~0.1 (收益小,重构成本中等) |
| `fcntl` | **17** | 仅 `_workspace_lock` (121) | 技术可 lazy (仅 MUTATING 命令) | **~0.017 (不值)** |
| `time` | (self 1633) | `now()` (81) 全局 + `_workspace_lock` (monotonic/sleep) | **不可** (now() 几乎所有写命令) | 0 |
| `json`/`os`/`sys` | <1000 | 全局 | **不可** | 0 |

**skein.py lazy 候选小结**: 仅 `shutil` + `datetime` 值得 (合计 cum ~1.7ms, 但 shutil 多被 argparse 链带入, 实际独立省约 0.5-1ms)。fcntl 17us 完全不值。

### 1.2 spec.py (847 行)

> 顶层 imports: `argparse time json re sqlite3 subprocess sys datetime Path typing hooklib`

| 模块 | cum_us (中位) | 使用命令/位置 | lazy 可否 | 预期省 ms |
|---|---|---|---|---|
| `argparse` | 4013 | `main()` 必需 | 不可 | 0 |
| `re` | 2977 | 全局 (frontmatter/wikilink/正则遍布) | 不可 | 0 |
| `pathlib.Path` | 2319 | 全局 | 不可 | 0 |
| `subprocess` | 2303 | `spec_root()` git rev-parse (87, **每个 Spec() 初始化都调**) + `_git_mv` (649, 仅 degrade) | **半**: spec_root 对所有命令必需 (难 lazy);`_git_mv` 可局部但收益小 | ~0 (spec_root 挡道) |
| `sqlite3` | **1235** | 仅 `_recall_fts` (251) + `_rebuild_fts` (359) → recall / reindex / sediment / maintain 命令 | **强 lazy** (session-start/inject-core/subagent-start/list 完全不用) | **~1.2** |
| `typing` | 1086 | 全局注解 | 不可 | 0 |
| `datetime` | 621 | 仅 `_write_audit` (605/610) → degrade / maintain --apply 归档审计 | **可 lazy** (低频路径) | ~0.3 |
| `time`/`json`/`os`/`sys` | <800 | 全局 | 不可 | 0 |

**spec.py lazy 候选小结**: `sqlite3` 是最强候选 (热路径 session-start/subagent-start 不用, 省 1.2ms cum)。`datetime` 次之。`subprocess` 被 `spec_root()` 挡住 (除非改 spec_root 用 Path 探测, 见 §5)。

### 1.3 hooks.py (471 行) — **最值得优化 (user-prompt 最频繁)**

> 顶层 imports (全顶载, 无 lazy): `json os re subprocess sys datetime typing`

| 模块 | cum_us (中位) | 使用子命令 | lazy 可否 | 预期省 ms |
|---|---|---|---|---|
| `json` | 7331 | `_load_stdin` (42) + 所有 cmd_* 输出 JSON | **不可** (所有 hook 入口都用) | 0 |
| `re` | 6258 | `ENGINE_RE`/`BIN_RE`/`PRD_RE`/`SPEC_RE` (模块级编译, 33/37/196/220) + `_parse_fm`/`_judge_signal` | **不可** (模块级 re.compile 必需) | 0 |
| `subprocess` | **5259** | **仅 `cmd_fmt`** (212, 跑 `skein.py fmt`) | **强 lazy** (其余 8 个子命令全不用!) | **~3-5** |
| `typing` | 1877 | 类型注解 | 不可 | 0 |
| `time` | 1848 | **未被 hooks.py 直接用!** (import 了但代码无 time.* 调用) | **可删** (死 import) | ~0.5 |
| `datetime` | 932 | **仅 `cmd_stop_check`** (320, `datetime.now().isoformat`) | **可 lazy** (其余 8 个子命令不用) | ~0.5 |
| `os`/`sys` | <500 | 全局 | 不可 | 0 |

**hooks.py lazy 候选小结** (top 优先级):
- `subprocess` (5.3ms cum) — 仅 cmd_fmt 用 → 局部 import, user-prompt/guard/permission/batch/report/spec-meta/task-created 全受益
- `time` — **死 import** (grep `time\.` 在 hooks.py 零命中), 直接删
- `datetime` (0.9ms) — 仅 cmd_stop_check 用 → 局部 import

先例: hooks.py:291 `cmd_stop_check` 已有 `from spec import Spec, core_budget` 局部 import 模式 (注释: "局部 import: 仅 stop-check 加载, 不拖其他 6 个子命令启动")。同范式套到 subprocess/datetime 零风险。

---

## 2. hooks 热路径 IO 审计

### 2.1 cmd_user_prompt — 零 IO ✓

`cmd_user_prompt` (hooks.py:384-401) 纯内存: 只 `os.path.exists/isdir` 判 config.yaml/.trellis/.git 存在性 (stat, 不读内容) + `_judge_signal` 纯字符串正则。**无文件读 IO**, 性能良好。

### 2.2 cmd_guard `_has_active_task` — 实测开销可忽略

`_has_active_task` (hooks.py:86-111) 每次 Write/Edit 扫 `.skein/task/*/task.json`:

| task 数 | _has_active_task (min/med ms) | 说明 |
|---|---|---|
| 本仓 10 task | 0.038 / 0.040 | 实测 |
| 模拟 50 task | 0.085 / 0.087 | 30% active |
| 模拟 100 task | 0.064 / 0.091 | |
| 模拟 300 task | 0.150 / 0.174 | 线性增长, 斜率极小 |

**对比 marker 文件方案** (`.skein/.has-active` 单文件 `os.path.exists`): 0.0017ms (恒定, 与 task 数无关)。

**结论**: _has_active_task 在 100 task 以内 < 0.1ms, 占 hooks.py guard 总 35ms 的 **0.3% 以下**。即使 300 task 也仅 0.17ms。**当前短路设计 (找到第一个 active 即 return, hooks.py:109-110) 已足够优**。

### 2.3 IO 优化方案利弊

| 方案 | 省 | 代价/风险 | 推荐 |
|---|---|---|---|
| **现状 (扫 task.json, 短路)** | — | 0.04ms/次 (10 task) | **保留** (开销可忽略) |
| marker 文件 `.skein/.has-active` | ~0.038ms | **一致性风险**: 每个写 task 命令 (create/start/finish/archive/del) 须同步维护 marker; 进程崩溃/marker 滞留 → 误判 (有 active 但 marker 没 → 漏阻; 无 active 但 marker 残留 → 误阻); 跨进程竞态 | **不推荐** (省的绝对值太小, 引入状态一致性问题违背 ponytail "input validation at trust boundaries") |
| mtime 缓存 | — | hook 进程短命 (每 prompt 新进程), 进程内缓存无意义; 跨进程需文件 flag = 回到 marker 方案 | **不推荐** |
| 并行 IO (threadpool 读 task.json) | 极小 | 线程开销 > IO 本身 (10 文件 stat 总 0.04ms) | **不推荐** (违反 ponytail "两 stdlib 取简") |

**IO 审计总结**: hooks IO 不是瓶颈。扫 task.json 方案正确且已优化。marker 文件是过度优化, 违背 "复杂度 vs 收益" 原则。

---

## 3. hooklib 审计 (110 行)

轻量, 总 import cum 7.6ms。imports: `os sys typing`。

- `debug_enabled` / `Debug` / `est_tokens` / `budget_guard` 全局必需 (skein.py/spec.py 都 `from hooklib import ...`)。
- `Debug.__init__` 内 `from rich.console import Console` 已是局部 lazy (hooklib.py:34), 且包在 `if enabled:` 内, 默认关时不导入 rich。**已是良好范式**。
- `Debug.kv` 内 `from rich.table import Table` 同理局部 (hooklib.py:60)。
- **无需改动**。hooklib 是 lazy import 的正面教材。

---

## 4. 隐藏大头: Skein() 的 git 子进程 (11ms)

实测 `Skein()` 初始化 (skein.py:189-200) 耗时 **min 10.9ms / med 13.9ms**, 远超多数 lazy import 能省的量。

根因: `__init__` 首行 `git("rev-parse", "--show-toplevel")` (skein.py:192) 启动 git 子进程定 root。**每个 skein.py 命令都付** (除 session-context 前的 env 持久化路径)。

对比: `_all()` 读 10 个 task.json 仅 0.2ms。**IO 不是瓶颈, git 子进程才是**。

### 4.1 潜在优化 (独立于 lazy import, 供 main 评估)

| 方案 | 省 | 风险 |
|---|---|---|
| 用 `Path(__file__).parents[N]` 推导 root | ~11ms | **跨 worktree 失效**: skein.py 在 plugins/tools/skein/scripts/, `__file__` 永远指向插件安装路径而非用户仓库; worktree 隔离下 root≠cwd, 必须靠 git rev-parse。**不可行** |
| 从 env/var 取缓存 root | ~11ms (命中时) | 跨 worktree/跨项目串台风险; 需按 cwd 分键缓存, 复杂度 vs 11ms 收益 |
| git rev-parse 本身不可避免 | — | skein 设计依赖 git 识别 root + worktree |

**结论**: Skein() git 子进程是设计代价 (worktree 隔离需要), 不在本 subtask 范围内改。但 main 设计 lazy import 时应知道: **lazy import 总收益 (约 5-8ms) < 单次 Skein git 子进程 (11ms)**, 若要大幅降延迟应优先评估 git root 缓存可行性 (另立项)。

### 4.2 argparse 构造成本

实测 24 subparser 构造 + parse_args: **1.2-1.4ms** (精简版)。main() 完整版 (含所有 add_argument, skein.py:2986-3041) 约 2-4ms。

延迟构造 subparser (先解析顶层 cmd, 再按需展开) 收益约 2-3ms, 但:
- argparse 不原生支持两阶段构造, 需自写 argv 路由层
- 破坏 subparser help 生成 (`--help` 需全展开)
- 重构成本高, 收益 (2-3ms) 相对 Skein git (11ms) 较小

**不推荐本轮做**。

---

## 5. 优化方案优先级排序

### Tier 1: 高收益低风险 (推荐本轮做)

| # | 方案 | 文件 | 省 | 风险 | 改动 |
|---|---|---|---|---|---|
| 1 | **hooks.py lazy `subprocess`** (仅 cmd_fmt 用) | hooks.py:22 (删顶 import) + cmd_fmt 内 (212) 局部 `import subprocess` | ~3-5ms / user-prompt 等热路径 | 极低 (已有 cmd_stop_check 局部 import 先例 :291) | 2 行 |
| 2 | **hooks.py lazy `datetime`** (仅 cmd_stop_check 用) | hooks.py:24 (删) + cmd_stop_check 内 (320) 局部 `from datetime import datetime` | ~0.5-1ms / 非 stop-check 路径 | 极低 | 2 行 |
| 3 | **hooks.py 删死 import `time`** | hooks.py:22 (`import time` 但全文件零 `time.*` 调用) | ~0.5ms | 零 (死代码) | 1 行 |
| 4 | **spec.py lazy `sqlite3`** (热路径 session-start/inject-core/subagent-start/list 不用) | spec.py:34 (删) + `_recall_fts` (251) / `_rebuild_fts` (359) 内局部 `import sqlite3` | ~1.2ms / session-start 等热路径 | 极低 (sqlite3 仅这两个方法用) | 3 行 |

**Tier 1 合计**: hooks user-prompt 省 ~4-6ms (29→~24ms), spec session-start 省 ~1.2ms。

### Tier 2: 中收益中风险 (可选)

| # | 方案 | 省 | 风险 |
|---|---|---|---|
| 5 | skein.py lazy `shutil` + `datetime` (仅 del_/archive/setup 用) | ~0.8ms / 读命令 | 低 (改动点多: del_/_archive/setup 迁移) |
| 6 | spec.py lazy `datetime` (仅 _write_audit 用) | ~0.3ms | 低 |

### Tier 3: 不推荐 (低收益或高风险)

| # | 方案 | 省 | 不推荐原因 |
|---|---|---|---|
| — | skein.py lazy `fcntl` | 0.017ms | 绝对值可忽略 |
| — | skein.py argparse 延迟构造 | 2-3ms | 重构成本高, 破坏 --help, 收益 < Skein git (11ms) |
| — | _has_active_task marker 文件 | 0.038ms | 一致性风险 > 收益 |
| — | Skein() git root 缓存 | 11ms | 跨 worktree 串台, 需另立项评估 |

---

## 6. design 建议 (lazy import 落地)

### 6.1 落地范式 (复用既有先例)

**统一用"顶层删 import + 调用点局部 import"**, 先例:
- hooks.py:291 `cmd_stop_check`: `from spec import Spec, core_budget` (注释: "局部 import: 仅 stop-check 加载, 不拖其他 6 个子命令启动")
- hooklib.py:34 `Debug.__init__`: `from rich.console import Console` (包在 `if enabled:`)
- spec.py:99 `core_budget`: `from skein import _yaml_load` (局部免循环依赖)

### 6.2 具体改动清单 (供 executor 实现)

**hooks.py** (top 优先):
```python
# 顶层 (22-24 行附近) 改为:
import json
import os
import re
import sys
from typing import Any, Optional, cast
# 删: import subprocess, import time, from datetime import datetime

# cmd_fmt (199-216) 内, 212 行前加:
def cmd_fmt(d):
    ...
    import subprocess  # 局部: 仅 fmt 子命令用, 不拖 user-prompt 等热路径
    subprocess.run(...)

# cmd_stop_check (283-326) 内, 320 行附近改:
def cmd_stop_check(_):
    ...
    from datetime import datetime  # 局部: 仅 stop-check 用
    from spec import Spec, core_budget
    ...
    "ts": datetime.now().isoformat(timespec="seconds"),
```

**spec.py**:
```python
# 顶层 (30-37) 删 import sqlite3
# _recall_fts (237-261) 内, 250 行前加:
def _recall_fts(self, query):
    ...
    import sqlite3  # 局部: 仅 recall + reindex 链用, 不拖 session-start/inject-core
    con = sqlite3.connect(db)

# _rebuild_fts (353-373) 内, 359 行前加:
def _rebuild_fts(self):
    import sqlite3
    ...
```

### 6.3 验收

- `python3 hooks.py --self-check` 全过 (信号证据 self-check 不依赖 subprocess/datetime)
- `python3 hooklib.py` 自检过
- 端到端: `hooks.py user-prompt` wall time 应从 ~29ms 降至 ~24ms (实测验收)
- 端到端: `spec.py session-start` 应从 ~88ms 降 ~1-2ms (sqlite3 省)
- 功能回归: cmd_fmt 仍能跑 skein.py fmt; cmd_stop_check 仍写 .pending-fix; spec recall 仍查 FTS; reindex/sediment 仍重建 .recall.db

### 6.4 不改的 (明确)

- fcntl 保留顶载 (17us 不值)
- argparse 保留顶载 (路由必需)
- Skein() git rev-parse 不动 (设计代价, 另立项)
- _has_active_task 扫描逻辑不动 (IO 非瓶颈)
- hooklib 不动 (已是 lazy 正面教材)

---

## 附录: 测量方法

- importtime: `python3 -X importtime`, 5 runs 取 cum_us 中位数 (self time 不含子依赖, cum 含)
- 端到端: `subprocess.run` + `time.perf_counter`, 6-8 runs 取 min/median
- _has_active_task: 临时造 n 个 task.json 目录, 30 runs 取 min/median
- 数据采集: darwin, python3.11.15 (mise); 基线给定 python3.13 数据用作交叉验证, 量级一致

## SPEC 标记 (供 finish sediment)

`SPEC:` 脚本启动性能优化遵循"顶层删 import + 调用点局部 import"统一范式 (skein-scripts-perf); 判定标准: 该 import 仅被 ≤2 个低频子命令用时即 lazy 候选, 全局/模块级 (re.compile/类型注解/main 路由) 保留顶载。先例: hooks.py:291 cmd_stop_check, hooklib.py:34 Debug, spec.py:99 core_budget。
