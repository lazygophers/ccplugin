---
id: S2
slug: schema-memory-absorb
deliverable: D2
parent-task: 06-09-cortex-schema-sot
status: planned
execution-layer: sub-agent
depends-on: []
blocks: [S3, S4, S5, S6]
estimated-tokens: 8000
---

# S2 · schema-memory 吸收 layout.md (memory 部分) + 接管 R6 映射

## 目标

把 layout.md 5 级物理树 + 遗忘曲线相关内容迁入 schema-memory; 从 cortex-lint references/rules.md 接管 R6 level↔dir 映射表权威.

## 产出

- `skills/cortex-schema-memory/references/levels.md` 补充: 完整 5 级物理树 (来自 layout.md) + level↔dir 映射表 (从 lint R6 迁来) + 路径名后缀防写反提醒
- `skills/cortex-schema-memory/references/properties.md` 补 遗忘曲线说明 (如尚未含)
- SKILL.md 不变 (路由表已含 levels)

## 验证

```bash
d=plugins/tools/cortex/skills/cortex-schema-memory
test -f $d/references/levels.md
# 5 级完整
for lv in L0-core L1-long L2-mid L3-short L4-inbox; do
  grep -q $lv $d/references/levels.md || echo "MISSING: $lv"
done
# level↔dir 映射表
grep -q 'L0.*core\|level.*L0' $d/references/levels.md
grep -q '映射\|mapping' $d/references/levels.md
# 反写防呆
grep -q 'L1-recent\|L1-short\|L3-long' $d/references/levels.md  # 应作反例提及
[[ $(wc -l < $d/SKILL.md) -le 60 ]]
python3 -c "
import yaml
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert len(fm['description']) <= 512
assert '用户说' not in fm['description'] and '用户说' not in str(fm['when_to_use'])
print('OK')
"
```

## 资源

独占 `skills/cortex-schema-memory/**`. 读 `docs/layout.md`. 读 `skills/cortex-lint/references/rules.md` 抽 R6 映射 (但不改 lint, S3 负责).

## 执行细节

1. Read docs/layout.md (5 级 ASCII 树 + 遗忘曲线表 + L0-L4 各级语义)
2. Read cortex-lint references/rules.md 抽 R6 等级映射表 (`memory/L0-core/` → L0 等)
3. 改 levels.md (补充):
   - 完整 5 级物理树 ASCII (从 layout.md 抄)
   - 各级路径 + 强度 + 复用面 + 写入触发 + 自动迁移 (已有, 补完)
   - **level↔dir 映射表** (新; 接管 R6):
     ```
     | level field | 路径段 (权威) |
     | L0 | memory/L0-core/ |
     | L1 | memory/L1-long/ |
     | L2 | memory/L2-mid/ |
     | L3 | memory/L3-short/ |
     | L4 | memory/L4-inbox/ |
     ```
   - 反写防呆提示: `L1-recent / L1-short / L3-long / L0-rules` 等都是反写, lint R6 视为 error
4. properties.md 不变 (若已含遗忘曲线则不动; 否则补一行)

### Dispatch Prompt

```
Active task: .trellis/tasks/06-09-cortex-schema-sot

## 目标
让 cortex-schema-memory 成为 5 级记忆等级 / 遗忘曲线 / level↔dir 映射的唯一真相源. 从 docs/layout.md 吸收 5 级物理树; 从 cortex-lint references/rules.md 接管 R6 level↔dir 映射表.

## 已知
- 5 级路径 (英文不变): memory/L0-core memory/L1-long memory/L2-mid memory/L3-short memory/L4-inbox
- 升级方向 = 抗遗忘: L3→L2→L1→L0
- 反直觉: L1=长期 L3=短期
- 反写防呆: L1-recent/L1-short/L3-long/L0-rules 等都视错

## 工作目录
cwd: /Users/luoxin/persons/lyxamour/ccplugin
可改: plugins/tools/cortex/skills/cortex-schema-memory/**
禁改: 其他 skill / docs/layout.md / lint references (S3 改)

## 输出
- references/levels.md 含完整 5 级物理树 + level↔dir 映射表 + 反写防呆段
- references/properties.md 补充遗忘曲线说明 (如缺)
- SKILL.md 不变, 仍 ≤ 60 行

## 验收
subtask "验证" 节命令全过, 无 MISSING.

## 失败处理
- 工具错 → 重试 1 次
- 不确定 → "需要: <问题>" 回 main

## Sub-agent 自防护
trellis-implement, 不再 spawn.
```

## 回滚

```bash
git checkout plugins/tools/cortex/skills/cortex-schema-memory/
```
