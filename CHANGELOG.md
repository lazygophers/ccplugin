# Changelog

All notable changes to CCPlugin Market will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Breaking
- Renamed plugins: `office-docx`/`office-pdf`/`office-pptx`/`office-xlsx` → `docx`/`pdf`/`pptx`/`xlsx`; `plugin-llms` → `llms`; `plugin-template` → `template`
- Migration: re-run `claude plugin install <newname>` for any of the affected plugins

### Added
- `scripts/check.py --marketplace`: 仓库级名称对齐校验（marketplace.json ↔ plugin.json ↔ 目录名），检测 drifts/ghosts/orphans

## [0.0.193] - 2026-04-25

### Changed
- **全量插件审查**：修复所有插件的版本滞后、配置错误、安全问题
- **语言插件版本更新**：C23/C++26/C#14/.NET10/Go1.26/Java25/TS6.0/Python3.14/Rust1.95/Flutter3.41
- **Agent description 精简**：移除冗余 `<example>` 块，改为触发词格式
- **LSP 配置现代化**：去重、添加现代参数（所有语言插件）
- **Novels Skills 补全**：30 个 skills 补充 model/memory 字段

### Fixed
- **lib/ SQL 注入防护**：WHERE/ORDER BY/GROUP BY/HAVING/SELECT 子句验证
- **lib/ 路径遍历防护**：SQLite db_path 限制在 home/cwd 目录内
- **lib/ 占位符统一**：first_or_create/create_or_update 使用 adapter.get_placeholder()
- **lib/ 敏感信息过滤**：hooks 日志添加敏感字段黑名单
- **lib/ 类型安全**：ExecuteResult Protocol、单例双重检查锁
- **scripts/ 文件描述符泄露**：subprocess stdout 改用 with 语句
- **scripts/ 超时统一**：所有 subprocess.run 添加 timeout=120
- **scripts/ 环境变量白名单**：check.py 仅暴露安全变量
- **statusline/ CacheKey.__hash__**：返回 int 修复 TypeError
- **statusline/ 缓存命中**：时间窗口改为秒级 bucket
- **statusline/ buffer 上限**：parser buffer 添加 10MB 限制
- **docs/ 路径错误**：修复 .bak 后缀和错误安装命令

### Added
- **tools/version**：创建 commands/version.md（show/info/bump/set）
- **memory database.py**：asyncio.Lock 双重检查锁

## [0.0.1] - 2025-01-06

### Added
- 初始化插件市场
- 创建 marketplace.json 配置
- 添加插件开发模板

> 注：v0.0.1 至 v0.0.192 的详细变更历史未记录。

[0.0.193]: https://github.com/lazygophers/ccplugin/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/lazygophers/ccplugin/releases/tag/v0.0.1
