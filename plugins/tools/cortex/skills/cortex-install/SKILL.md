---
name: cortex-install
description: 初始化 vault — 双 namespace (知识库 + 记忆 L0-L4) + 仪表盘 + 归档 + 9 cron 注册。lang 询问 (zh-CN/en/ja)。触发: "init vault" / "安装 cortex" / "初始化 vault" / "cortex 装机"。
disable-model-invocation: true
allowed-tools: Bash Read Write Edit Glob AskUserQuestion mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content
---

# cortex-install

把一个 (新或既有) Obsidian vault 初始化为 cortex 标准布局 — **双 namespace** (知识库 + 记忆 L0-L4) + 仪表盘 + 归档 + HTML 片段库 + 可选 9 cron jobs。

## 触发场景

- 用户初次安装 cortex, 把空 vault 起骨架
- 已有 vault 需补 `_meta/` / `_templates/` / 新结构

## 关键决策树

1. **解析 vault** — 跑 `<PLUGIN_ROOT>/scripts/hooks/_lib/resolve_vault.sh`; 失败则提示配置 `OBSIDIAN_VAULT` env 或 `~/.cortex/config.json`
2. **询问 lang** — `AskUserQuestion`: 默认 `zh-CN`, 可选 `en` / `ja`; 写 `_meta/version.json:.lang`
3. **写共享根 + 业务结构** — `_meta/` 元数据 + `_templates/` (36 模板) + `index.md` / `hot.md` + 双 namespace 子目录 + 44 seed_files + `.cortex/` 骨架 (state + config); 详见 [references/install-flow.md](references/install-flow.md)
4. **git auto-sync 询问** (vault 是 git repo 时) — `AskUserQuestion` 三选: 关 / 仅 commit / commit+push, 写 `_meta/version.json:auto_commit,auto_push`
5. **9 cron 询问** — `AskUserQuestion` 多选要注册的 job + 平台 (launchd/cron/GHA/不启用), 详见 [references/cron-setup.md](references/cron-setup.md)
6. **wrapper 安装** — 跑 `scripts/install_wrappers.sh` 生成 24 个 `~/.cortex/scripts/*.sh`; 详见 [references/update-config.md](references/update-config.md)
7. **回报** — 列已创建/已存在/跳过的文件, 提示跑 `/cortex:doctor` 验证

## AUTO_MODE (wrapper / cron 传 `auto` 后缀)

- **不调** AskUserQuestion (wrapper allowed-tools 已禁); 强行调用必失败
- 默认决策: `lang=zh-CN`, `git auto-sync=off`, `cron=off` (用户后续手动跑 `~/.cortex/scripts/install_cron.sh`)
- persistent: 任何 IO error 自决降级 / 重试 / 换工具, 禁询问禁中止
- 写盘前不需二次确认 (AUTO_MODE 隐含已授权)
- 单文件已存在 → skipped, 继续下一项

## 写入策略

- **不覆盖已有文件** — 用 `Glob` 或 `mcp__obsidian__obsidian_get_file_contents` 检查, 存在则 `(skipped)`
- 优先 `mcp__obsidian__obsidian_append_content` (vault 索引一致); MCP 不可用回退 `Write`
- 模板 `{{TITLE}}` / `{{CREATED}}` / `{{UPDATED}}` 占位**不替换** — 留给 cortex-save / memory skill
- 单文件失败不中断, 末尾汇总

## References

| 文件 | 内容 |
|---|---|
| [references/install-flow.md](references/install-flow.md) | 顶层结构 / 知识库 4 子目录 / 记忆 L0-L4 / 36 模板 / 44 seed_files 完整清单 |
| [references/cron-setup.md](references/cron-setup.md) | 9 cron job 调度表 + 3 平台后端 (launchd/cron/GHA) + PLUGIN_ROOT 解析 |
| [references/update-config.md](references/update-config.md) | 24 wrapper 分组 + 卸载提示 + 输出格式样本 + 错误处理 |

## 错误处理

- 单文件 IO/权限错: 标 ❌, 继续, 末尾汇总
- vault 路径解析失败: 立即退出, 提示配置方式
- 模板源缺失 (插件文件丢): 退出, 提示重装 cortex
- `_meta/memory-policy.yaml` 源缺失: 警告跳过, 提示手动复制
