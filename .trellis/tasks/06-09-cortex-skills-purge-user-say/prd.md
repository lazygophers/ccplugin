# purge user-say phrasing from cortex skill frontmatter

## 目标

4 cortex skill 的 frontmatter `when_to_use` 与 `description` 中含 "用户说" / "用户说 '...' 时使用" 等口语描述的位置一律去除. 改为直接列触发场景 / 关键词, 不引"用户说话"作为触发触发条件描述.

## 命中点

- `cortex-lint` when_to_use: `用户说 lint/体检/校验 vault/audit; ...`
- `cortex-extract` description: `... 用户说 '整理 inbox / 提取记忆 / 归档笔记 / promote / digest' 时使用.`

(其他 skill 已 clean)

## Requirements

| skill | 字段 | 旧 | 新 (示例) |
| --- | --- | --- | --- |
| cortex-lint | when_to_use | `用户说 lint/体检/校验 vault/audit; ...` | `lint/体检/校验 vault/audit; 整理 .wiki/ 前先跑; 排查死链/孤儿; ...` |
| cortex-extract | description | `... 用户说 '整理 inbox / 提取记忆 / 归档笔记 / promote / digest' 时使用.` | `... 触发词: 整理 inbox / 提取记忆 / 归档笔记 / promote / digest.` |

## Acceptance Criteria

- [ ] 4 SKILL.md frontmatter 中 grep "用户说" 0 命中
- [ ] description ≤ 512 / when_to_use ≤ 128 仍满足
- [ ] yaml 解析仍通过
- [ ] 自动 git add

## 范围

- 改: 4 SKILL.md frontmatter (实际只动 2 个)
- 不动: references/* / body / argument-hint / arguments / name

## 备注

PRD-only 轻量 task.
