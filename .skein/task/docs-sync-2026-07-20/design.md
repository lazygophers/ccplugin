# docs-sync — 详细设计

## 用户确认方向 (2026-07-20)

- **项目定位**: Claude Code 的 **插件 + skills 集合**(非单一插件)
- **ONBOARDING**: 就地重写(不删除)
- **通用 docs**: 删除 5 个非项目特定文档(api-reference / best-practices / supported-languages / compiled-languages-guide / mcp-servers-research)
- **保留 docs**: ONBOARDING.md(重写) + plugin-development.md(修正项目引用)

## 4 subtask 方案

### readme-fix (README.md)
- marketplace.json 真源: 仅 7 个插件 `cortex / deepresearch / notify / novelist / skein / trellisx / version`
- 当前 README 列了 22 个插件, 其中 15 个不存在
- 路径纠正: `plugins/<name>` → `plugins/tools/<name>` (pluginRoot=./plugins, source=./plugins/tools/<name>)

### onboarding-rewrite (docs/ONBOARDING.md)
- 当前 2026-05-26 自动生成版本严重失真
- 失真项: 引用 Memory/Git/Task/Llms 不存在插件; 引用 .trellis/ .claude/scripts/ .claude/hooks/ .claude/skills/ 不存在目录; 过时 Trellis 引用
- 重写为反映 plugin+skills 实际结构的新贡献者上手指南

### claude-md-extend (CLAUDE.md)
- 当前仅含自动提交规则 + 代码质检规范 + 指针, 缺项目结构描述
- 补: 实际结构(plugins/tools/ 7 插件 + 根 skills/ 开发模板 + skein/trellisx 共存)

### docs-audit (docs/)
- 删除 5 个通用 Claude Code 文档(用户确认不需要)
- plugin-development.md 第 496-500 行项目引用修正

## 执行约束

- skein start 激活 → 建 worktree skein/docs-sync-2026-07-20 → 派 skein-executor 改
- 禁 main inline 改源码
- 完成后 skein check 跑 claude -p 质检门(CLAUDE.md 强制) + 一致性核查
