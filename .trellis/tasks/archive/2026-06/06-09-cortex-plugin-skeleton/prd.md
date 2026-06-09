# scaffold cortex plugin skeleton under plugins/tools

## Goal

在 `plugins/tools/cortex/` 落一份占位骨架, 形态对齐既有 `plugins/tools/trellisx/`, 让后续填充 cortex 具体能力 (vault search / memory / ingest 等) 时只需写实现, 不再补结构。

## Requirements

- 目录: `plugins/tools/cortex/`
- 文件树:
  - `.claude-plugin/plugin.json` — 元数据 + agents / skills / hooks / commands 声明 (占位条目可指向骨架文件)
  - `agents/cortex.md` — 占位 agent (frontmatter 完整, 描述标 TODO)
  - `skills/cortex/SKILL.md` — 占位 skill (frontmatter 完整, when_to_use 标 TODO)
  - `hooks/` — 目录占位 (含 `.gitkeep`, 不放可执行脚本)
  - `commands/` — 目录占位 (含 `.gitkeep`)
  - `README.md` — 插件描述占位 (主题 TODO, 结构区块齐全)
  - `llms.txt` — LLM 摘要占位
- `plugin.json` 中 author / license / repository 等字段对齐 trellisx 同款 (lazygophers / AGPL-3.0-or-later)
- 不写任何具体业务逻辑, 不引入运行时依赖; 所有"待定"位置统一用 `TODO` 标记
- 自动 `git add` 到暂存区 (按项目 CLAUDE.md 全局约定), 不自动 commit

## Acceptance Criteria

- [ ] `ls plugins/tools/cortex/` 列出全部 7 个条目 (`.claude-plugin/` `agents/` `skills/` `hooks/` `commands/` `README.md` `llms.txt`)
- [ ] `plugin.json` 通过 `python3 -c "import json; json.load(open('plugins/tools/cortex/.claude-plugin/plugin.json'))"` 校验
- [ ] `agents/cortex.md` 和 `skills/cortex/SKILL.md` 均带合法 YAML frontmatter (`name` / `description` 字段非空)
- [ ] `git status` 显示新建文件全部已暂存

## Notes

- 主题待定 → 描述类字段用 `TODO: <提示>`, 不臆造主题
- 不创建 `scripts/` / `docs/` / `pyproject.toml` 等运行时目录, 留给后续按需扩展
- 不动 `plugin-marketplace.json` 等市场注册文件 (用户未要求)
