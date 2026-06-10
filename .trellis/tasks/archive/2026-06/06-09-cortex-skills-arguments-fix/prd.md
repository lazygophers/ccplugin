# fix cortex skills arguments field format

## 目标

4 个 cortex skill 的 frontmatter `arguments` 字段从结构化对象列表改成字符串, 与 `argument-hint` 一一对位, value 中文化.

## 背景

上次拆多文件时把 `arguments` 误写成 yaml 对象列表 `- name: ... description: ...`. 实际约定是简单字符串 (参照 trellisx-spec 的 `argument-hint: [scope]` + `arguments: [范围]`).

## Requirements

| skill | argument-hint (保持) | arguments (新值, 中文) |
| --- | --- | --- |
| cortex-schema-knowledge | `[module]` | `[模块]` |
| cortex-schema-memory | `[level]` | `[等级]` |
| cortex-lint | `[--check\|--fix] [target]` | `[--check\|--fix] [路径]` |
| cortex-extract | `[--dry-run\|--apply] [target]` | `[--dry-run\|--apply] [路径]` |

## Acceptance Criteria

- [ ] 4 skill frontmatter `arguments` 是字符串, 不是 yaml 列表
- [ ] 与对应 `argument-hint` 形状一致 (相同槽位数, 同样可选/必选标记)
- [ ] arguments 槽位 value 中文化 (module→模块 / level→等级 / target→路径; 命令名如 `--check` 等保留英文)
- [ ] 4 SKILL.md frontmatter yaml 解析通过, 无字段类型冲突
- [ ] 自动 git add 暂存

## 范围边界

- 在范围: 4 SKILL.md 各自 frontmatter `arguments` 字段
- 不动: description / when_to_use / argument-hint / 其他字段 / references/* / 任何脚本

## 风险

| 风险 | 缓解 |
| --- | --- |
| arguments 在 SKILL.md body 里也提到 (引用 frontmatter) | grep 一遍, 同步改 |
| 中文翻译歧义 (module 是"模块"还是"子模块") | 按 argument-hint 既有语义对位, 不臆造 |

## 备注

轻量 task, PRD-only.
