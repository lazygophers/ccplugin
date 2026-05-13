# Slash Commands

cortex 提供 20 个 plugin slash command, 在 Claude Code 任何会话中可直接调用: 输入 `/cortex:<name>` (冒号格式)。

所有命令**无入参**, 全自动执行, 不询问用户 (AUTO_MODE persistent)。命令体定义在 `commands/<name>.md`, 触发后 AI 加载对应 SKILL.md 自决执行直至任务完成。

## 命令清单

| 命令 | 触发 | 用途 |
|------|------|------|
| `/cortex:init` | 初始化 vault (首次安装) | 创建目录骨架 + 默认模板 + 配置 |
| `/cortex:install_cron` | 安装定时任务 | 部署 launchd / cron / GitHub Actions 触发器 |
| `/cortex:config` | 编辑配置 | 交互式更新 `~/.cortex/config.json` |
| `/cortex:update` | 更新插件 | 拉最新 marketplace + 重生成 wrapper |
| `/cortex:doctor` | 体检 | 检查 vault 完整性 / 配置正确性 / 依赖可用性 |
| `/cortex:lint` | 全自动修复 | 跑 17 条 lint 规则 + autofix + 循环修复直至 clean |
| `/cortex:refactor` | 重构 vault | 改名 / 合并 / 拆分页面, 同步 wikilink |
| `/cortex:archive` | 归档 | 把过期内容移到 `_meta/.cortex-backup/` |
| `/cortex:search` | 搜索 | 多级回退: hot → index → Smart Connections → ripgrep |
| `/cortex:save` | 落档 | 写一篇新笔记 (concept / domain / log 三类) |
| `/cortex:ingest` | 深度摄取 | 深度分析当前目录 / URL / 文件 → 知识库 |
| `/cortex:recall` | 召回记忆 | 多级语义搜索 vault + 记忆层 |
| `/cortex:memory` | 记忆管理 | 列出 / 查看 / 修改 L0-L4 记忆条目 |
| `/cortex:promote` | 提升记忆等级 | L2 → L1 / L1 → L0 (经用户审批) |
| `/cortex:forget` | 遗忘 | 删除指定记忆条目 |
| `/cortex:consolidate` | 整合 | 7 天 ledger → 候选概念页 + 反思 / 连接 |
| `/cortex:dashboard` | 刷新仪表盘 | 重渲 `index.md` / `hot.md` / canvas 三件套 |
| `/cortex:fold` | 折叠 | 长 log/ledger 切尾到 `folds/<YYYY-QN>.md` |
| `/cortex:compact` | 紧凑 | 整理 vault, 删空目录, 合并碎片 |
| `/cortex:warden` | 守卫巡检 | 周期扫描孤儿 / 死链 / 老 fleeting, 自动处理 |

## 使用方式

### Claude Code 交互会话内

```
> /cortex:lint
```

直接输入即触发, 等同于自然语言"跑一遍 lint"。

### Bash 脚本调用

每个 slash command 都有对应 `~/.cortex/scripts/<name>.sh` wrapper, 调用 `claude -p "/cortex:<name>"` 走全权限流。详见 [Bash 脚本](Bash%20脚本.md)。

### 定时任务

通过 `/cortex:install_cron` 注册的 cron 任务最终也走 slash command 路径。详见 [周期任务](周期任务.md)。

## 行为约束 (所有命令一致)

- **禁询问**: AskUserQuestion 工具不可用; 遇歧义按推荐默认值执行
- **禁中止**: 报 errors_remaining > 0 然后停 = 违规; 必须循环修复直至稳定 或 工具客观失败
- **禁推卸**: "需人工" / "AI 不会" / "建议后续处理" 等推卸辞令禁止输出
- **唯一终态**: clean (任务完成) 或 stuck (磁盘只读 / 权限拒绝 / git lock)

详见各命令 `commands/<name>.md` 的 AUTO_MODE 章节。
