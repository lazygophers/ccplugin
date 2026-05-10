---
name: cortex-install
description: 初始化或升级 Obsidian vault 至 cortex 标准布局 — 写共享根与所选 preset (lyt/zettel/para/blank) 业务目录, 不覆盖。Triggers on "init vault", "install cortex", "安装 cortex", "初始化 obsidian vault".
allowed-tools: Bash Read Write Edit Glob mcp__obsidian__obsidian_list_files_in_vault mcp__obsidian__obsidian_list_files_in_dir mcp__obsidian__obsidian_get_file_contents mcp__obsidian__obsidian_append_content
---

# cortex-install

把一个 (新或既有) Obsidian vault 升级到 cortex 标准布局。

## 触发场景

- 用户初次安装 cortex, 需要把空 vault 起骨架
- 已有 vault 接入 cortex, 需补 `_meta/` 与 `_templates/`
- 切换 preset (lyt ↔ para ↔ zettel ↔ blank)

## 输入

- `preset` ∈ `{lyt, zettel, para, blank}`, 默认 `lyt`
- vault 路径来自 `${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh`

## 流程

1. **解析 vault** — 跑 `${CLAUDE_PLUGIN_ROOT}/hooks/_lib/resolve_vault.sh` 拿绝对路径; 失败则提示用户配置 `OBSIDIAN_VAULT` env 或 `~/.config/cortex/config.json`
2. **校验 preset** — 不在白名单则报错并退出
3. **写共享根** (所有 preset 必备):
   - `_meta/version.json` — `{"schema": "1.0", "preset": "<preset>", "created": "<UTC ISO>"}`
   - `_meta/lint-baseline.json` — `{"exempt": []}`
   - `_meta/migrations/` — 确保目录存在 (用 `Bash mkdir -p` 或写入一个 `.gitkeep`)
   - `_templates/` — 复制 `${CLAUDE_PLUGIN_ROOT}/templates/{concept,entity,domain,dashboard,question,source,_index}.md` 到此目录
   - `index.md` — 用 `_templates/_index.md` 内容作为基础, 或写空骨架由用户填充
   - `hot.md` — 空骨架 (frontmatter `type: meta, title: hot`)
   - `log/_index.md` — 空骨架
   - `folds/_index.md` — 空骨架
4. **写 preset 业务目录**:
   - 读 `${CLAUDE_PLUGIN_ROOT}/presets/<preset>/_structure.json`
   - 按 `directories[]` 在 vault 内创建空目录
   - 按 `seed_files[]` 把 `${CLAUDE_PLUGIN_ROOT}/presets/<preset>/<src>` 复制到 `<vault>/<dst>`
   - blank preset 的 directories/seed_files 均为空, 跳过即可
5. **回报** — 列已创建/已存在的文件, 提示运行 `/cortex:doctor` 验证

## 写入策略

- **不覆盖已有文件** — 用 `Glob` 或 `mcp__obsidian__obsidian_get_file_contents` 检查目标路径, 存在则跳过并标 `(skipped)`
- 优先用 `mcp__obsidian__obsidian_append_content` (vault 索引一致); MCP 不可用回退 `Write`
- 模板文件中的 `{{TITLE}}` / `{{CREATED}}` / `{{UPDATED}}` / `{{PRESET}}` 占位 **不在此 skill 替换** — `_templates/` 下保留原样供 `/cortex:new` 使用
- 任何单文件失败不中断后续步骤, 最后统一报错

## 输出格式

```
解析 vault: /Users/.../knowledge/obsidian (源: env)
preset: lyt

[共享根]
✅ 写入 _meta/version.json
✅ 写入 _meta/lint-baseline.json
✅ 创建 _meta/migrations/
✅ 复制 _templates/concept.md
⏭️  _templates/entity.md (已存在)
✅ 写入 index.md
✅ 写入 hot.md
✅ 写入 log/_index.md
✅ 写入 folds/_index.md

[preset: lyt]
✅ 创建 00_MOC/ ... 80_archive/
✅ 复制 00_MOC/home.md
✅ 复制 00_MOC/topics-moc.md
... (省略)

总结: 22 项写入, 3 项跳过, 0 项失败
下一步: /cortex:doctor 验证
```

## 错误处理

- 单文件 IO/权限错: 标 ❌, 继续下一项, 末尾汇总
- vault 路径解析失败: 立即退出并提示配置方式
- preset 名错: 立即退出并列出 4 个有效值
- 模板/preset 源缺失 (插件文件丢): 立即退出, 提示重装 cortex 插件
