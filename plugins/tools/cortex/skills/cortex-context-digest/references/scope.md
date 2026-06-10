# scope 判定: global vs project

## 6 优先序 (先命中先用)

| # | 规则 | 结果 | 举例 |
| --- | --- | --- | --- |
| 1 | 用户显式 `--scope global` | **全局** `~/.cortex/.wiki/memory/` | `digest --scope global` |
| 2 | 用户显式 `--scope project` | **项目级** `<repo>/.wiki/memory/` | `digest --scope project` |
| 3 | 含 L0 触发词 (`永远` / `硬性` / `never` / `严禁` / `绝不` / `禁` 起首) | **全局** L0-core | "永远不要 force push 到 main" |
| 4 | 引用当前 repo 名 / 仓库路径 / 具体文件 (e.g. `plugins/tools/cortex/...`) | **项目级** | "本仓库 cortex 插件的 schema 路径用 ..." |
| 5 | 跨项目通用 (shell 通则 / AI 协作规范 / 工具用法 / 语言通病) | **全局** | "zsh 数组下标从 1 开始" |
| 6 | 兜底 | **项目级** (保守, 防误升全局污染) | 不确定的决策 / 选型 |

## --scope 显式语义

- `--scope global` — 强制写 `~/.cortex/.wiki/memory/<L0..L3>/`; 跳过自动判定
- `--scope project` — 强制写 `<repo>/.wiki/memory/<L0..L3>/`; 跳过自动判定
- 不带 `--scope` — 走 3-6 自动判定

显式覆盖优先于自动. 用户判断 > 启发式规则.

## 为何默认保守 project

- 全局记忆库跨项目共享, 误升的项目特定规则会污染其他仓库
- 项目级污染范围限当前 repo, 易清理
- L0 / 跨项目通用的明确信号才升全局, 模糊默认下沉

## L0 候选额外审

命中规则 3 (L0 触发词) 时, 除了路由全局外, **必须 ask 用户确认** (不 auto). L0-core 是硬性规则, 误入代价大. cortex-extract 路由表第 3 行同义 (`mode=ask`).

## 与 cortex-extract 三轴的关系

scope 判定决定**落点 vault** (`~/.cortex` vs `<repo>`); 三轴判定决定**层级** (L0-L4 / 项目 / 领域). 两步分离, scope 在外, 三轴在内. 实际调用:

```
extract --target <vault-by-scope> --dry-run
```

`<vault-by-scope>` = `$HOME/.cortex` (global) 或当前 repo 根 (project).
