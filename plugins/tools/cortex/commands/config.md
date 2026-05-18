---
description: 查看/编辑 cortex 配置 — ~/.cortex/config.json + <vault>/.cortex/config/*.yaml (无入参 → 列全部 + validate; verb: get/set/unset/validate)
---

# /cortex:config

[AUTO_MODE persistent: 禁询问, 自决执行, 禁中止]

调用 **`cortex-config` skill** 完成查看 / 编辑 / 校验。覆盖两个真相源:

- `~/.cortex/config.json` — 用户级
- `<vault>/.cortex/config/{digest,enrich,tags}.yaml` — vault 级

## 入参形态

| 形态 | 行为 |
|---|---|
| 无参 | 列全部 config + 标 default/user + 末尾 validate 报告 |
| `get <key>` | 读单字段 (支持点号路径, e.g. `digest.stages.consolidate`) |
| `set <key> <value>` | schema 校验 → 通过则 atomic write |
| `unset <key>` | schema 校验 → 通过则删除键 |
| `validate` | 仅校验, 输出 `{ok, errors, warnings}` JSON |

详见 cortex-config skill 的 `references/usage.md`。

## 兼容旧行为 (仅展示 `~/.cortex/config.json`)

```bash
INSTALL_PATH="$(jq -r .install_path ~/.cortex/config.json)"
python3 "$INSTALL_PATH/scripts/cortex_config.py" validate
```

若 config 不存在, 提示用户跑 `install.sh` 初始化。新展示与编辑功能由 `cortex-config` skill 提供。

## AUTO_MODE (shell wrapper 触发, persistent)

**核心原则**: "禁问" ≠ "中止". AI 必须**自决并执行直至任务完成**。遇歧义按推荐默认值执行; 工具不熟悉则尝试其他工具组合 (Bash/Edit/Write/MCP/WebSearch/WebFetch/Read 现有样本); 禁报"需人工"/"AI 不会"/"建议后续处理"。

### 严禁 (任一出现 = 契约违反)

| # | 禁止 |
|---|------|
| 1 | 任何"修复建议"/"建议"/"推荐操作" 章节/表格/列表 (`## 修复建议`, `\| 类型 \| 操作 \|`) |
| 2 | 用户确认问句 (`需确认?`, `是否执行?`, `要继续吗?`, `ok?`, 末尾问号) |
| 3 | AskUserQuestion 调用 (allowed-tools 已禁) |
| 4 | "下一步"/"后续"/"如需"/"可选" 导引 |
| 5 | "需人工"/"待人工"/"建议人工" 推卸辞令 |
| 6 | "AI 能力不足"/"无法自动" 类借口 |
| 7 | 报状态后停 (除非工具客观失败: 磁盘只读/权限拒绝/git lock) |
