# plan-hook / write-hook: trellis 生命周期 hook (worktree 自动化)

apply 把 worktree 自动建/销注入 **trellis 原生生命周期 hook** —— 不靠 Claude Code 平台 PostToolUse 监测 Bash 命令 (脆弱), 而是 trellis 自己在 `task.py start/archive` 时触发的 `after_*` hook。**内化优于外挂**。

## 机制 (已验证 trellis 源码)

trellis `task.py` 在任务生命周期事件调 `run_task_hooks(event, ...)` → `get_hooks(event)` 读 **`.trellis/config.yaml` 的 `hooks:` 字段** → 执行 shell 命令, 传 `TASK_JSON_PATH` env 指向当前 task.json。

| 事件 | 触发点 (trellis 源码) | trellisx 用途 |
| --- | --- | --- |
| `after_create` | `task_store.cmd_create` | (不用 — create 时仍 planning, 不建 worktree); 仅 task.md sync |
| `after_start` | `task.py cmd_start` | **建 worktree** (status → in_progress, 进入实施) |
| `after_finish` | `task.py cmd_finish` (先 clear active 指针, 再跑 hook) | **自动收尾** — 跑 `trellisx-finish.py`: commit→merge→archive→销 worktree。`task.py finish` 即触发, 不靠 AI 记得跑脚本 |
| `after_archive` | `task_store.cmd_archive` | **销 worktree** (被 after_finish 链里的 archive 触发, 或手动 archive) |

> 注意: 部分文档区写 hooks 在 `task.json.hooks.after_*`, 但**实际代码** `get_hooks(event, repo_root)` 只读 `.trellis/config.yaml`。以代码为准 → 注入 config.yaml。

### after_finish 自动收尾链 (已核对 trellis 源码安全)

`task.py finish` → `cmd_finish` 先 `clear_active_task` (清 active 指针) → 用 `task_json_path` 跑 `after_finish` hook → `trellisx-finish.py` 读 **`$TASK_JSON_PATH`** (此时 `task.py current` 已空, 必须靠 env 取 tid) → ① worktree commit ② merge --no-ff 回主分支 ③ `task.py archive` → `cmd_archive` 触发 `after_archive` → `trellisx-worktree.py archive` 销毁已合并 worktree。

- **无递归**: archive 只触发 `after_archive`, 不回触 `after_finish`; `cmd_finish` 跑完 hook 直接 `return 0`, 无后置状态访问 (clear/path 都在 hook 前完成)。
- **env 不泄漏**: `run_task_hooks` 每事件重设 `TASK_JSON_PATH` (task_utils.py), 嵌套 archive 的 `after_archive` 拿到的是归档后路径。
- **hook 失败非致命**: trellis hook 失败仅 `[WARN]` (returncode≠0 不中断 finish)。**合并冲突 → trellisx-finish.py 非 0 退出, stderr 报冲突文件**, `task.py finish` 仍返 0 但打 WARN —— AI MUST 检 finish 输出有无 `trellisx-finish` 冲突告警, 有则转手动解决 (任务此时 active 已清但未 archive, worktree 保留)。

优势 (对比旧 PostToolUse 外挂):
- **跨平台**: 任何 AI / 人手跑 `task.py start` 都触发, 不限 Claude Code
- **不靠文本匹配**: 不再 regex 监测 Bash 命令 (start 命令变体 / 别名会漏)
- **trellis 原生**: config.yaml 是 trellis 第一公民, 不依赖用户 `.claude/settings.json`

## 注入物 1: worktree 生命周期脚本 (复制插件脚本, 不内联)

**统一脚本管理**: 脚本以独立文件存于**插件 `scripts/` 目录** (canonical 源), apply 时**复制**到用户项目 `.trellis/scripts/`, 不在本文档内联抄写 (防 AI 抄错 + 便于统一维护升级)。

apply 复制**五个**文件 (均来自插件 `scripts/`, 统一管理): 四个 hook 脚本 + 一个 apply 工具 (`trellisx-packages.py`, 非 hook, 供手动重扫):

```bash
# apply: 从插件 scripts/ 复制脚本到用户项目
# <plugin-root> = 本 skill 所在插件根 (skill base dir 的上两级: skills/trellisx-apply → 插件根)
mkdir -p .trellis/scripts
cp "<plugin-root>/scripts/trellisx_wt.py"       .trellis/scripts/trellisx_wt.py        # 公共模块 (worktree/finish 都 import)
cp "<plugin-root>/scripts/trellisx-worktree.py" .trellis/scripts/trellisx-worktree.py
cp "<plugin-root>/scripts/trellisx-taskmd.py"   .trellis/scripts/trellisx-taskmd.py
cp "<plugin-root>/scripts/trellisx-finish.py"   .trellis/scripts/trellisx-finish.py
cp "<plugin-root>/scripts/trellisx-packages.py" .trellis/scripts/trellisx-packages.py   # apply 工具 (packages 发现, 非 hook)
chmod +x .trellis/scripts/trellisx-worktree.py .trellis/scripts/trellisx-taskmd.py .trellis/scripts/trellisx-finish.py .trellis/scripts/trellisx-packages.py
```

> ⚠️ **`trellisx_wt.py` 是 worktree 路径/分支/命名的单一真值模块**: `trellisx-worktree.py`(建/销)与 `trellisx-finish.py`(收尾)都 `import trellisx_wt`(同目录), 共用 `worktree_paths()`/`worktree_name()`/`resolve_repo()`/`git_top()`。**漏拷 → 两脚本 ImportError**; 改约定只改这一个文件, 杜绝两边各写一份漂移 (历史教训: worktree.py 与 finish.py 曾各算一份路径/命名, 差一点就失配)。

**① `trellisx-worktree.py`** (读 `$TASK_JSON_PATH`, 自适应 3 布局; 路径/命名来自 `trellisx_wt.worktree_paths`):
1. **.trellis 同级 .git** (简单项目): worktree 在 git 根 `.worktrees/<name>`
2. **.trellis 子目录, git 在上层** (微服务): worktree 在上层 git 根, sparse 只检该子目录
3. **.trellis 非 git 根, 子仓在下层** (多子仓): 读 task.json `package`/`scope` 定位子仓 git
- `start` → 建 worktree; `archive` → 干净则销毁, 脏则保留并警告

**② `trellisx-taskmd.py`** (`.trellis/task.md` 看板的**唯一读写入口** — CLI, 见 trellisx-workspace):
- 子命令: `sync <create|start|archive>` (hook 用, 读 $TASK_JSON_PATH 维护确定性列) / `update <tid> --status/--phase/--progress/--worktree` (AI 用) / `show [tid]` / `cleanup [--days N]`
- hook 的 `sync` 维护**确定性列** (ID/名称/描述/状态), upsert 时**保留 AI 主观列** (阶段/进度/worktree) 不覆盖
- `sync archive` 顺带**清理超 7 天的已完成行** (依据 task.json.completedAt)
- AI 不直接编辑 task.md, 一律经本脚本

**③ `trellisx-finish.py`** (强制闭环收尾, **after_finish hook 自动调用** + 手动 CLI 兜底):
- 触发: ① `task.py finish` → after_finish hook 自动跑 (主路径, tid 取自 `$TASK_JSON_PATH`); ② 手动 `trellisx-finish.py [--task <tid>] [--message "<提交消息>"] [--dry-run]` (缺省 tid: 先 `$TASK_JSON_PATH` 后 `task.py current`)
- 序列: ① worktree 内 `git add -A` + commit → ② `git merge --no-ff trellisx-<name>` 合并回主分支 → ③ `task.py archive` (触发 after_archive → worktree 销毁)
- 合并冲突 → 自动 `merge --abort` + 报冲突文件 + 非 0 退出 (hook 模式下表现为 `task.py finish` 打 WARN); 幂等可重入 (已提交/已合并的步骤自动跳过)
- 用 `git rev-parse --git-common-dir` 定位**主 worktree** 根 (从 worktree 内误跑也能正确解析合并目标)
- workflow.md finish 段被注入为「跑 `task.py finish` → hook 自动收尾」(见 `workflow-injection.md` 注入点 4)

> 脚本源码见**插件 `scripts/`**。要改逻辑 → 改插件源文件, 不改本文档 (本文档只描述职责)。
> **i18n**: 脚本内 stderr 提示文本可按目标语言调整; 变量名 / 路径 / git 命令保持原样。
> 多子仓 (布局 3): task 须先 `task.py set-scope <子仓>` (如 `go`/`node`) 标注, 脚本才能定位 git。

## 注入物 2: config.yaml 的 hooks 字段 (幂等)

把 hook 命令合并进 `.trellis/config.yaml` 的 `hooks:`。**幂等**: 已含 `trellisx-worktree` 则跳过, 保留用户其它 hook。

```python
import re, os
cfg = ".trellis/config.yaml"
s = open(cfg, encoding="utf-8").read() if os.path.exists(cfg) else ""

if "trellisx-worktree.py" in s:
    pass   # 已注入 → 跳过 (幂等)
elif re.search(r"(?m)^hooks:", s):
    # 既有顶层 hooks: (非注释) → 把 trellisx 行合并进 after_start/after_finish/after_archive 列表;
    # 缺的事件键在 hooks: 下新增。绝不删用户已有 hook 命令。
    s = merge_into_existing_hooks(s)
else:
    block = (
        "\n# [trellisx] worktree 自动生命周期 + task.md 看板维护 (apply 注入)\n"
        "hooks:\n"
        "  after_create:\n"
        '    - "python3 .trellis/scripts/trellisx-taskmd.py sync create"\n'
        "  after_start:\n"
        '    - "python3 .trellis/scripts/trellisx-worktree.py start"\n'
        '    - "python3 .trellis/scripts/trellisx-taskmd.py sync start"\n'
        "  after_finish:\n"
        '    - "python3 .trellis/scripts/trellisx-finish.py"\n'
        "  after_archive:\n"
        '    - "python3 .trellis/scripts/trellisx-worktree.py archive"\n'
        '    - "python3 .trellis/scripts/trellisx-taskmd.py sync archive"\n'
    )
    s = s.rstrip() + "\n" + block

open(cfg, "w", encoding="utf-8").write(s)
```

> config.yaml `hooks:` 用 YAML 2 空格缩进, 已验证 trellis `parse_simple_yaml` 能解析 `hooks: → after_start: → - "cmd"` 嵌套。**注意**: trellis config.yaml 模板里 `hooks:` 默认是注释 (以 `#` 开头), 注释行不算 `^hooks:`, apply 应追加真实 (非注释) `hooks:` 块。

## 注入物 2.5: `session_auto_commit: true` (强制闭环依赖)

trellisx 强制自动收尾链的 ③ archive 调 `task_store._auto_commit_archive` 提交 `.trellis` 归档 bookkeeping, 该函数**受 `session_auto_commit` 控制** (`config.get_session_auto_commit`): 若用户显式设 `false` → archive 跳过 stage/commit → 归档移动未提交, **工作区脏留**, 闭环不干净 (worktree 仍销、feature 仍合并, 但 `.trellis/tasks/archive` 改动悬空)。

trellis **默认 `true`** (模板里 `# session_auto_commit: true` 注释 = 默认值)。但 apply 必须**显式写实 `session_auto_commit: true`**, 防用户曾设 `false` 时闭环破裂 —— 这是 owner「强制提交收尾」授权在 config 层的落地。

```python
import re
cfg = ".trellis/config.yaml"
s = open(cfg, encoding="utf-8").read() if os.path.exists(cfg) else ""
# 实值 (非注释) session_auto_commit 行?
m = re.search(r"(?m)^session_auto_commit:\s*(\S+)\s*$", s)
if m:
    if m.group(1).strip().lower() not in ("true", "yes", "1", "on"):
        s = re.sub(r"(?m)^session_auto_commit:.*$", "session_auto_commit: true", s)  # 非 true → 强制
    # 已 true → 幂等跳过
else:
    # 无实值行 (缺失 / 仅注释 `# session_auto_commit:`) → 追加实值
    s = s.rstrip() + "\n\n# [trellisx] 强制闭环收尾依赖 archive 自动提交 (apply 注入)\nsession_auto_commit: true\n"
open(cfg, "w", encoding="utf-8").write(s)
```

> 不删/不改模板里的注释说明行 (`# session_auto_commit: ...`), 只新增/纠正**实值行**。幂等: 已是实值 true 则跳过。

## 注入物 2.6: packages 注册表自动发现 (apply 一次扫描, 非 hook)

monorepo 项目 `.trellis/config.yaml` 的 `packages:` 注册表 (包名→path/type/git) 驱动 spec 注入 scoping (`packages_context.py` 按 task.package 选 `.trellis/spec/<pkg>/<layer>/`) 与包可见性。apply **一次扫描**自动发现并写入, 用户后续仓结构变化需重跑 (非 hook, 无运行时开销)。

由 `trellisx-packages.py` (插件脚本) 执行, **4 类发现信号** (强→弱):

| 信号 | 识别 | 注册为 |
| --- | --- | --- |
| git submodule | `.gitmodules` 的 `path =` | `type: submodule` |
| 嵌套独立 .git 子仓 | 子目录含独立 `.git` (深度≤4, 剪枝 node_modules/.worktrees 等) | `git: true` |
| workspace 清单 | `package.json` workspaces / `pnpm-workspace.yaml` / `go.work` 声明的包路径 (**须含项目 manifest**) | `local` |
| 约定目录 | `packages\|apps\|services\|libs\|modules/*` 且**含 manifest** (package.json/go.mod/Cargo.toml/pyproject.toml) | `local` |

> manifest 过滤 (信号 3/4) 降误报: 空目录 / 非项目目录不注册。强信号 (submodule>git>local) 覆盖弱。

**安全策略 (防误污染注册表)**:
- **仅当项目当前无实值 `packages:` (单仓)** 才自动写入; 已配置 monorepo → **只报告发现的包供人工核对, 绝不覆盖用户配置**。
- 写入用 marker 注释块标识 (`# [trellisx] 自动发现...`), 写在 config 末尾。
- 发现 0 包 → 保持单仓, 不写空 `packages:`。
- apply 审批门 (step5) 展示发现的包清单, 用户批准才写盘 (误报在审批时拦截)。

```bash
# plan-hook (read-only): 发现的包清单进 diff plan
python3 .trellis/scripts/trellisx-packages.py discover --repo "$(git rev-parse --show-toplevel)"
# write-hook (审批后): 写入 config.yaml packages: (单仓才写, 已配置只报告)
python3 .trellis/scripts/trellisx-packages.py apply --repo "$(git rev-parse --show-toplevel)"
```

> ⚠️ 注: `trellisx-worktree.py` 布局3 (多子仓) 用 task.json 的 `package/scope` **直接**定位 `troot/<pkg>` git, **不读** config packages 注册表。故注册表收益是 spec scoping + 可见性 + 少手配, **不替代** per-task `task.py set-scope`。

## 注入物 3: .gitignore 排除 worktree

worktree 在 **git 根** `.worktrees/`, 在 git 根 .gitignore (非 .trellis/.gitignore) 追加:
```bash
groot=$(git rev-parse --show-toplevel 2>/dev/null || echo .)
grep -q '.worktrees/' "$groot/.gitignore" 2>/dev/null || echo ".worktrees/" >> "$groot/.gitignore"
```

## 不再做 (相对旧版)

- ❌ 不写 `.claude/hooks/trellisx-worktree.py` (Claude Code 平台 hook)
- ❌ 不注册用户 `.claude/settings.json` 的 PostToolUse Bash matcher
- ❌ 不 regex 监测 `task.py create/start` 命令文本
- ❌ 不在本文档内联完整脚本源码 (改为从插件 scripts/ 复制)

全部由 trellis 原生 config.yaml hooks 取代。**不改 task.py 脚本** (仅加 config.yaml hooks + 复制独立 worktree 脚本)。

## 注入原则

- **统一脚本管理**: 脚本是插件 `scripts/` 下的独立文件; apply 复制到用户 `.trellis/scripts/`, 不内联
- **不改 task.py**: worktree 靠 trellis 原生 lifecycle hook 触发, 不改脚本
- **幂等**: 重复 apply 检测 `trellisx-worktree.py` 已在 config.yaml 则跳过; 脚本文件覆盖更新 (从插件源重新复制)

## 验证

```bash
# config.yaml hooks 注入成功且 trellis 能解析
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; print('after_start:', get_hooks('after_start')); print('after_archive:', get_hooks('after_archive'))"
# 四文件复制成功 + 语法合法 + 公共模块可导入
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx_wt.py').read())" && echo "公共模块 OK"
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); import trellisx_wt; print('worktree_paths' in dir(trellisx_wt) and '公共模块导出 OK')"
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx-worktree.py').read())" && echo "worktree 脚本 OK"
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx-taskmd.py').read())" && echo "taskmd 脚本 OK"
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx-finish.py').read())" && echo "finish 脚本 OK"
python3 -c "import ast; ast.parse(open('.trellis/scripts/trellisx-packages.py').read())" && echo "packages 脚本 OK"
python3 .trellis/scripts/trellisx-packages.py discover --repo "$(git rev-parse --show-toplevel)" >/dev/null && echo "packages discover 可跑"
grep -q "import trellisx_wt" .trellis/scripts/trellisx-worktree.py .trellis/scripts/trellisx-finish.py && echo "两脚本均 import 公共模块"
python3 .trellis/scripts/trellisx-finish.py --dry-run >/dev/null 2>&1; echo "finish dry-run 退出码 $? (无 active task 时非 0 正常)"
# config hooks 含 after_create/after_start/after_finish/after_archive
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; print('after_create:', get_hooks('after_create')); print('after_finish:', get_hooks('after_finish'))"
# after_finish 含 trellisx-finish.py (自动收尾链)
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; assert any('trellisx-finish' in c for c in get_hooks('after_finish')), 'after_finish 缺自动收尾'; print('✓ after_finish 自动收尾已装')"
# session_auto_commit 解析为 true (archive 自动提交闭环依赖)
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_session_auto_commit; assert get_session_auto_commit() is True, 'session_auto_commit 非 true, 闭环 archive 不提交'; print('✓ session_auto_commit=true')"
# gitignore
grep -q '.worktrees/' "$(git rev-parse --show-toplevel)/.gitignore" && echo "worktrees 已排除"
```
