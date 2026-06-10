# search — 双层 vault 搜索策略

第 1 步: 在两层 vault 中搜答案. 命中即返回 (附引用), **不走兜底**.

## 双层搜索范围 (按优先序)

| # | 层 | 路径 | 内容 | 优先级 |
| --- | --- | --- | --- | --- |
| 1 | 项目级 | `<repo>/.wiki/` | `memory/L0-L4` + `领域/` (当前项目专属; 无 项目/脚本 模块) | 优先 |
| 2 | 用户级 | `~/.cortex/.wiki/` | `memory/` + `项目/` + `领域/` + `脚本/` (跨项目沉淀) | 兜底层 |

先搜项目级 (更贴合当前上下文), 再搜用户级补全. 两层都搜, 合并结果去重.

路径/级别契约以 cortex-schema 为权威 (`L0-core/L1-long/L2-mid/L3-short/L4-inbox`; 三模块目录中文 项目/领域/脚本).

## 多级回退 (搜索工具, 先命中先用)

| # | 工具 | 适用 | 备注 |
| --- | --- | --- | --- |
| 1 | mcp-obsidian `*_search` | vault = obsidian (有 mcp) | 语义/全文, 最优 |
| 2 | `rg` (ripgrep) | vault 目录可直接扫 | `rg -i "<query>" <repo>/.wiki ~/.cortex/.wiki` |
| 3 | `grep -r` | 无 rg 时 | `grep -ri "<query>" <vault>` |
| 4 | 读 hot/index 缓存 | vault 有 `_index` / `hot` 缓存 | 命中后再回原文取上下文 |

逐级回退: 上一级工具不可用或无结果 → 降级下一级.

## 命中判定

- 找到直接回答 query 的条目 → **命中**, 返回答案 + 引用, 流程结束 (不走兜底/回填)
- 仅找到弱相关 / 不足以回答 → **未命中**, 进 `fallback.md` 第 2 步

## 返回格式

答案正文 + 引用. 引用形式:

- vault 内文件: `file:line` (e.g. `~/.cortex/.wiki/memory/L1-long/git.md:12`)
- obsidian wikilink: `[[note-title]]` 或 `[[note#标题]]`

多条命中按相关度排序, 每条附独立引用.
