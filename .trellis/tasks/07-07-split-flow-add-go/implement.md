# Implement — 拆分 trellisx-flow 为 add/flow + go

工作目录: `plugins/tools/trellisx/`。所有改动自动提交暂存区 (CLAUDE.md 规范)。

## 执行顺序 (依赖驱动)

规划正文是单一真值源, 必须先建 add (S1), flow/go/docs 才有可引用的锚点。

| 序 | subtask | 产出 | 依赖 | 写文件集 |
|---|---|---|---|---|
| S1 | 建 `trellisx-add` skill | `skills/trellisx-add/SKILL.md` (+按需 references) | — | skills/trellisx-add/** |
| S2 | 建 `go` command | `commands/go.md` | S1 (语义引用 add) | commands/go.md |
| S3 | 改 flow planning 段瘦身 | `skills/trellisx-flow/SKILL.md` | S1 (指向 add) | skills/trellisx-flow/SKILL.md |
| S4 | 登记 manifest | `.claude-plugin/plugin.json` | S1,S2 | .claude-plugin/plugin.json |
| S5 | 同步 grill 硬门 + docs 矛盾 | grill/SKILL.md, docs/*, README.md | S1,S3 | skills/trellisx-grill/SKILL.md, docs/**, README.md |

- S1 阻塞其余全部 → **S1 串行首发**。
- S2/S3 写文件集不相交, 但都语义依赖 S1 → S1 后 S2‖S3 可并行 (并发上限 2)。
- S4/S5 依赖 S1-S3 落定 → 最后串行 (S4 改 json, S5 改 md, 文件集不交可并, 但置于收尾一批)。

## S1 — trellisx-add skill (checklist)

- [ ] frontmatter: `name: trellisx-add`; `description` 前置触发词 (「只规划不执行」「先看规划」「添加分析规划」); `argument-hint: [--continue|--exec] <描述>`。
- [ ] planning 正文 = 从 flow 现 step1(判新旧+登记) + step2(planning: brainstorm 主导 + grill 硬门1 边问边写) 迁入, 单一真值。
- [ ] 参数契约: 无参 = 跑完 planning **停在 start 前** (task=planning 态, 交还控制); `--continue` = 不停返回 planning 产物路径。明确「停/不停」是入口开关, planning 本体零分支。
- [ ] 边界段: add **禁 exec/check/finish** (那是 flow/go); add 禁自动触发 (仅显式)。
- 验证: `test -f skills/trellisx-add/SKILL.md`; `grep -qE 'continue|不阻塞' skills/trellisx-add/SKILL.md`; `grep -q 'start 前' skills/trellisx-add/SKILL.md`

## S2 — go command

- [ ] frontmatter: `name: go`; `description` 前置「go/执行 pending/跑规划好的 task」; `argument-hint`。
- [ ] 逻辑: 枚举 planning 态 task → 空态提示「先 /trellisx-add」 → 非空按 task 级 DAG (冲突串行/不冲突并行/上限2滚动, 引 scheduling.md) → 每 task 走 flow start→exec→check→finish 载体铁律。
- [ ] go 禁 planning (只消费 add 产物)。
- 验证: `test -f commands/go.md`; `grep -qE '并发.*2|上限 ?2' commands/go.md`; `grep -q 'planning' commands/go.md`; `grep -q '先 /trellisx-add' commands/go.md`

## S3 — flow planning 段瘦身

- [ ] 现 step2 planning 段替换为「调 `/trellisx-add --continue <描述>` + add 返回后 flow 续 step3」。
- [ ] 删除迁入 add 的重复正文 (判新旧/brainstorm/硬门1 措辞), 保留 step3-6 + 载体铁律 + 硬规 + 反例。
- [ ] 保名 trellisx-flow, 保双模触发描述不动。
- 验证: `grep -q 'trellisx-add' skills/trellisx-flow/SKILL.md`; 确认 planning 正文不再重复 (`grep -c '判新旧' skills/trellisx-flow/SKILL.md` 应显著下降 / 仅引用性提及)

## S4 — plugin.json 登记

- [ ] `skills` 数组加 `"./skills/trellisx-add"`。
- [ ] 新增 `commands` 数组含 `"./commands/go.md"` (若无则建)。
- 验证: `jq -e '.skills | index("./skills/trellisx-add")' .claude-plugin/plugin.json`; `jq -e '.commands | index("./commands/go.md")' .claude-plugin/plugin.json`

## S5 — 引用同步

- [ ] `skills/trellisx-grill/SKILL.md`: 硬门1 触发点描述 `trellisx-flow step2` → `trellisx-add planning 阶段` (硬门2 start 前仍归 flow/激活)。
- [ ] `docs/prd.md:73` + `README.md:23` + `docs/skills-reference.md:33`: flow「禁自动触发」→ 与 SKILL 双模一致 (显式 + 自动)。
- [ ] docs/skills-reference.md + README + getting-started: 补 `trellisx-add` / `go` 条目。
- 验证: `grep -rn '禁自动触发' docs README.md` 无 flow 误述; `grep -q 'trellisx-add' skills/trellisx-grill/SKILL.md docs/skills-reference.md`

## Review Gate

- G1 (S1 后): add planning 正文与 flow 原 step1/2 语义等价, 无遗漏 (grill 硬门1 保留)。
- G2 (全部后): `claude -p` 三路由测试 —— add=只规划停 / flow=全闭环 / go=执行 pending, 三者不误抢 (CLAUDE.md 质量检查规范)。
- G3: 其余 trellisx skill 交叉引用 grep 全绿 (flow 保名验证)。

## Rollback

- 每 subtask git 暂存独立, 失败 `git checkout -- <文件集>` 回退单 subtask。
- S1 失败 (add 语义无法等价迁移) → 回退 design §5 备选「共享 references/plan-phase.md」重规划。

## 验证命令汇总

```bash
cd plugins/tools/trellisx
test -f skills/trellisx-add/SKILL.md && test -f commands/go.md
jq -e '.skills|index("./skills/trellisx-add")' .claude-plugin/plugin.json
jq -e '.commands|index("./commands/go.md")' .claude-plugin/plugin.json
grep -q 'trellisx-add' skills/trellisx-flow/SKILL.md
grep -rn '禁自动触发' docs README.md   # 期望: 无 flow 误述
```
