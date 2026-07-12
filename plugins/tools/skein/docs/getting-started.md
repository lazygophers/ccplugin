# 快速开始

## 1. 前置要求

- **git 仓库** — SKEIN 用 git worktree 做隔离, 项目必须是 git 仓库 (`git init` 过)。
- **Python 3** — 引擎 `skein.py` / `memory.py` 是纯 Python 3 脚本, 无第三方依赖。
- **Claude Code** — SKEIN 是 Claude Code 插件, 通过 skill / command / hook 驱动。

## 2. 安装

SKEIN 是 ccplugin 市场里的一个插件。装好插件后, Claude Code 会自动加载它的 skills、command、agents 和 hooks (见 `.claude-plugin/plugin.json`)。

装好后可验证脚本可跑:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py --help
```

> plugin 启用后 `bin/` 自动进 Bash tool 的 PATH, 上面这行可缩为裸命令 `skein --help` (`skein-memory` 同理指向 memory.py)。下文示例沿用完整长形式以求明确。

## 3. 初始化工作区

第一次在某个项目里用 SKEIN, 用 `setup` 初始化 `.skein/` 工作区 (幂等):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py setup
```

> **推荐入口 = `setup`** (不是裸 `init`): 幂等 scaffold + 兼容 trellis。检测到 `.trellis/` → 软链 spec + 输出迁移 manifest (spec 重组 / task 重建交 `skein-setup` agent 语义迁移, 清 trellis 残留)。无 trellis → 等价 `init` + 建本地 spec 库。
> SessionStart 时若 git 仓无 `.skein/`, hook 会**自动注入** setup 建议; Claude 主动调 **skein-setup** skill 完成初始化, 无需手动。

`init` 会建出:

```
.skein/
├── .gitignore       # 忽略 task.md/task.html/board/ (自动渲染); 另补 worktree_root 到仓库根 .gitignore
├── task.json        # {tasks:[]} — 顶层状态全表, 脚本维护, AI 禁读写
├── task.md          # 空看板 — 由 task.json 自动渲染 (git 忽略)
├── task.html        # 静态可视化看板 (2 列 dashboard, subtask DAG/表默认展开可折叠) — 由 task.json 自动渲染 (4 主题 6 配色 深浅色, git 忽略); `skein view` 按需打开
├── board/           # 主题/配色 CSS (从插件 assets 拷贝, git 忽略, html link 引入)
├── config.yaml      # max_active:2 / max_parallel:2 / retain_days:7 / auto_commit:true / worktree_root:.worktrees / board_*
└── task/
    └── archive/     # 归档根
```

> `init` 还会把 worktree 根目录 (默认 `.worktrees/`) 追加到**仓库根** `.gitignore` — worktree 是隔离的任务源码副本, 不入库 (幂等, 已存在则跳过)。

规则记忆库 `.skein/spec/` 在首次 sediment 时按需建出。

> **可选 — 空仓冷启动播种**: 若是已有代码但从没用过 SKEIN 的仓库 (`.skein/spec` 为空), 可先走 `skein-memory` 冷启动播种 (`references/bootstrap-seeding.md`) — 扫既有代码库约定 (命名 / 错误处理 / 测试 / 架构边界 / 构建) 播种一批基线规则, 让第一个 task 就能召回项目习惯。一次性动作, 之后靠正常 finish 增量沉淀。首次上手不跑也行。

## 4. 跑通第一个 task

最简单的方式 — 用命令:

```
/skein-go 把 config 读取从环境变量改为读 config.yaml, 并更新所有调用点
```

或者**什么都不用输** — 只要请求够复杂 (跨 ≥2 文件 / 多步骤 / 需调研), Claude 会自动加载 `skein-flow` skill 走同一套闭环。

接下来 Claude 会 (你只需在关键处拍板):

1. **plan** — 和你 brainstorm 需求与方案, 跑对抗审查 (grill), 产出 `prd.md` / `implement.md`, 请你评审。(可选: 把不可回退的不变量锁成契约, 供 check 逐条验; 首次上手可先跳过。)
2. **exec** — 建 worktree, 派 subagent 在里面写代码, 完成一批即回传进度。
3. **check** — 派 checker 跑 lint / type / test / 契约校验, 不过就派合适 agent (无则 `general-purpose`) 修。
4. **finish** — 判本次有无值得沉淀的规则, 然后 commit → 合并回主分支 → 销 worktree, 状态转 completed。**完成 task 不立即归档**, 留看板 `retain_days` 天 (默认 7), 超期自动移入 `archive/`; 想提前清走用 `/skein-clean [保留天数]` (仅用户主动)。

## 5. 看进度

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py board      # 渲染并打印看板
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py current    # 列全部 active task (无 focus, 就绪皆可并行)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py ready      # 脚本算就绪 task 批 (pending+前置全done+空闲槽)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py list       # 全部 task (含已归档)
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py view       # 打开 task.html 可视化看板 (缺则生成)
```

看板文件 `.skein/task.md` (文本) + `.skein/task.html` (可视化, title/标题带项目名) 每个生命周期节点后自动重渲染。**禁直接编辑 task.md** — guard hook 会硬阻; task.html 只读, 用 `view` 按需打开。

## 6. 边界: 什么请求不该建 task

| 请求特征 | 建 task? |
| --- | --- |
| 纯查询 / 读文档 / 问答 (无改动) | 豁免, 直接回答 |
| 单文件单处改, ≤20 行且位置已知 | 豁免, 直接改 |
| 跨 ≥2 文件 / 单文件多处 / 多步骤 | 必建 task |
| 需外部调研 (选型 / 对比) 或产出文档 | 必建 task |
| 边界模糊 | Claude 会用 AskUserQuestion 问你 |

下一步: 想懂它内部怎么转 → [workflow.md](workflow.md); 想看不同活儿怎么用 → [scenarios.md](scenarios.md)。
