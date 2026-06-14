# 步骤 4: 注入 trellis 原生生命周期 hook (worktree 自动化)

apply 把 worktree 自动建/销注入 **trellis 原生生命周期 hook** —— 不靠 Claude Code 平台 PostToolUse 监测 Bash 命令 (脆弱), 而是 trellis 自己在 `task.py start/archive` 时触发的 `after_*` hook。**内化优于外挂**。

## 机制 (已验证 trellis 源码)

trellis `task.py` 在任务生命周期事件调 `run_task_hooks(event, ...)` → `get_hooks(event)` 读 **`.trellis/config.yaml` 的 `hooks:` 字段** → 执行 shell 命令, 传 `TASK_JSON_PATH` env 指向当前 task.json。

| 事件 | 触发点 (trellis 源码) | trellisx 用途 |
| --- | --- | --- |
| `after_create` | `task_store.cmd_create` | (不用 — create 时仍 planning, 不建 worktree) |
| `after_start` | `task.py cmd_start` | **建 worktree** (status → in_progress, 进入实施) |
| `after_finish` | `task.py` finish | (不用 — finish 只清活跃指针, 不动 worktree) |
| `after_archive` | `task_store.cmd_archive` | **销 worktree** (任务完成归档) |

> 注意: 部分文档区写 hooks 在 `task.json.hooks.after_*`, 但**实际代码** `get_hooks(event, repo_root)` 只读 `.trellis/config.yaml`。以代码为准 → 注入 config.yaml。

优势 (对比旧 PostToolUse 外挂):
- **跨平台**: 任何 AI / 人手跑 `task.py start` 都触发, 不限 Claude Code
- **不靠文本匹配**: 不再 regex 监测 Bash 命令 (start 命令变体 / 别名会漏)
- **trellis 原生**: config.yaml 是 trellis 第一公民, 不依赖用户 `.claude/settings.json`

## 注入物 1: worktree 生命周期脚本 (复制插件脚本, 不内联)

**统一脚本管理**: 脚本以独立文件存于**插件 `scripts/` 目录** (canonical 源), apply 时**复制**到用户项目 `.trellis/scripts/`, 不在本文档内联抄写 (防 AI 抄错 + 便于统一维护升级)。

apply 复制**四个**文件 (均来自插件 `scripts/`, 统一管理):

```bash
# apply: 从插件 scripts/ 复制脚本到用户项目
# <plugin-root> = 本 skill 所在插件根 (skill base dir 的上两级: skills/trellisx-apply → 插件根)
mkdir -p .trellis/scripts
cp "<plugin-root>/scripts/trellisx_wt.py"       .trellis/scripts/trellisx_wt.py        # 公共模块 (worktree/finish 都 import)
cp "<plugin-root>/scripts/trellisx-worktree.py" .trellis/scripts/trellisx-worktree.py
cp "<plugin-root>/scripts/trellisx-taskmd.py"   .trellis/scripts/trellisx-taskmd.py
cp "<plugin-root>/scripts/trellisx-finish.py"   .trellis/scripts/trellisx-finish.py
chmod +x .trellis/scripts/trellisx-worktree.py .trellis/scripts/trellisx-taskmd.py .trellis/scripts/trellisx-finish.py
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

**③ `trellisx-finish.py`** (强制闭环收尾 CLI, AI 在 check 通过后调用 — 非 hook):
- 用法: `trellisx-finish.py [--task <tid>] [--message "<提交消息>"] [--dry-run]` (缺省 task 取 `task.py current`)
- 序列: ① worktree 内 `git add -A` + commit → ② `git merge --no-ff trellisx-<name>` 合并回主分支 → ③ `task.py archive` (触发 worktree 销毁 hook)
- 合并冲突 → 自动 `merge --abort` + 报冲突文件 + 非 0 退出; 幂等可重入 (已提交/已合并的步骤自动跳过)
- 用 `git rev-parse --git-common-dir` 定位**主 worktree** 根 (从 worktree 内误跑也能正确解析合并目标)
- workflow.md finish 段被注入为「强制跑此脚本」(见 `workflow-injection.md` 注入点 4)

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
    # 既有顶层 hooks: (非注释) → 把 trellisx 行合并进 after_start/after_archive 列表;
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
        "  after_archive:\n"
        '    - "python3 .trellis/scripts/trellisx-worktree.py archive"\n'
        '    - "python3 .trellis/scripts/trellisx-taskmd.py sync archive"\n'
    )
    s = s.rstrip() + "\n" + block

open(cfg, "w", encoding="utf-8").write(s)
```

> config.yaml `hooks:` 用 YAML 2 空格缩进, 已验证 trellis `parse_simple_yaml` 能解析 `hooks: → after_start: → - "cmd"` 嵌套。**注意**: trellis config.yaml 模板里 `hooks:` 默认是注释 (以 `#` 开头), 注释行不算 `^hooks:`, apply 应追加真实 (非注释) `hooks:` 块。

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
grep -q "import trellisx_wt" .trellis/scripts/trellisx-worktree.py .trellis/scripts/trellisx-finish.py && echo "两脚本均 import 公共模块"
python3 .trellis/scripts/trellisx-finish.py --dry-run >/dev/null 2>&1; echo "finish dry-run 退出码 $? (无 active task 时非 0 正常)"
# config hooks 含 after_create/after_start/after_archive
python3 -c "import sys; sys.path.insert(0,'.trellis/scripts'); from common.config import get_hooks; print('after_create:', get_hooks('after_create'))"
# gitignore
grep -q '.worktrees/' "$(git rev-parse --show-toplevel)/.gitignore" && echo "worktrees 已排除"
```
