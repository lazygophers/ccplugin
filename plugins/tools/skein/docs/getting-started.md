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

第一次在某个项目里用 SKEIN, 需要初始化 `.skein/` 工作区:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py init
```

> 用 `/skein-go` 时若检测到无 `.skein/`, 会**自动**先跑 `init`, 无需手动。

`init` 会建出:

```
.skein/
├── task.md          # 空看板
├── state.json       # {focus: null}
├── config.json      # {max_active:2, auto_commit:true, worktree_root:".worktrees"}
└── task/
    └── archive/     # 归档根
```

规则记忆库 `.claude/rules/` 在首次 sediment 时按需建出。

> **可选 — 空仓冷启动播种**: 若是已有代码但从没用过 SKEIN 的仓库 (`.claude/rules` 为空), 可先跑一次 `skein-bootstrap` — 它扫既有代码库约定 (命名 / 错误处理 / 测试 / 架构边界 / 构建) 播种一批基线规则, 让第一个 task 就能召回项目习惯。一次性动作, 之后靠正常 finish 增量沉淀。首次上手不跑也行。

## 4. 跑通第一个 task

最简单的方式 — 用命令:

```
/skein-go 把 config 读取从环境变量改为读 config.yaml, 并更新所有调用点
```

或者**什么都不用输** — 只要请求够复杂 (跨 ≥2 文件 / 多步骤 / 需调研), Claude 会自动加载 `skein-flow` skill 走同一套闭环。

接下来 Claude 会 (你只需在关键处拍板):

1. **plan** — 和你 brainstorm 需求与方案, 跑对抗审查 (grill), 产出 `prd.md` / `implement.md`, 请你评审。(可选: 把不可回退的不变量锁成契约, 供 check 逐条验; 首次上手可先跳过。)
2. **exec** — 建 worktree, 派 subagent 在里面写代码, 完成一批即回传进度。
3. **check** — 派 checker 跑 lint / type / test / 契约校验, 不过就派 implementer 修。
4. **finish** — 判本次有无值得沉淀的规则, 然后 commit → 合并回主分支 → 归档 → 销 worktree。

## 5. 看进度

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py board      # 渲染并打印看板
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py current    # 当前 focus task
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py current --all  # 所有 active task
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/skein.py list       # 全部 task (含已归档)
```

看板文件 `.skein/task.md` 每个生命周期节点后自动重渲染。**禁直接编辑它** — guard hook 会硬阻。

## 6. 边界: 什么请求不该建 task

| 请求特征 | 建 task? |
| --- | --- |
| 纯查询 / 读文档 / 问答 (无改动) | ❌ 豁免, 直接回答 |
| 单文件单处改, ≤20 行且位置已知 | ❌ 豁免, 直接改 |
| 跨 ≥2 文件 / 单文件多处 / 多步骤 | ✅ 必建 task |
| 需外部调研 (选型 / 对比) 或产出文档 | ✅ 必建 task |
| 边界模糊 | ❓ Claude 会用 AskUserQuestion 问你 |

下一步: 想懂它内部怎么转 → [workflow.md](workflow.md); 想看不同活儿怎么用 → [scenarios.md](scenarios.md)。
