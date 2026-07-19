# 优化评分 Rubric + 体检命令

> 流程 B 的细节层：先机械体检定位硬伤，再按 8 维 rubric 打分排优先级，一轮修一类。每维带方向轴 + 理想值 + 完成准则底线，配 validation-gate 循环纪律收敛。

## 体检命令（先跑，硬伤优先）

```bash
P=plugins/tools/<name>

# 1. manifest JSON 合法
jq -e . $P/.claude-plugin/plugin.json >/dev/null || echo "❌ manifest JSON 非法"

# 2. name kebab-case + = 目录名
jq -r '.name' $P/.claude-plugin/plugin.json | grep -qE '^[a-z0-9-]+$' || echo "❌ name 非 kebab-case"
[ "$(jq -r '.name' $P/.claude-plugin/plugin.json)" = "$(basename $P)" ] || echo "❌ name ≠ 目录名"

# 3. 接线双向: 挂载路径 vs 实际文件 (无悬挂)
for k in skills agents commands; do
  jq -r --arg k $k '.[$k][]? // empty' $P/.claude-plugin/plugin.json | while read p; do
    [ -e "$P/$p" ] || echo "❌ 悬挂: $k 挂了 $p 但文件不存在"
  done
done

# 4. 反查漏挂 (文件存在但没挂)
find $P/skills $P/agents $P/commands -maxdepth 2 \( -name SKILL.md -o -name '*.md' \) 2>/dev/null

# 5. SKILL.md 大写
ls $P/skills/*/SKILL.md 2>/dev/null | grep -v '/SKILL.md$' && echo "❌ SKILL.md 命名错"

# 6. 组件没误放 .claude-plugin/
ls -d $P/.claude-plugin/commands $P/.claude-plugin/skills $P/.claude-plugin/agents 2>/dev/null && echo "❌ 组件误放 .claude-plugin/ 内"

# 7. hook 路径用变量
grep -n '"command"' $P/.claude-plugin/plugin.json $P/hooks/hooks.json 2>/dev/null | grep -v CLAUDE_PLUGIN_ROOT && echo "⚠️ hook 疑似写死路径"

# 8. hook 带 timeout
grep -A2 '"command"' $P/.claude-plugin/plugin.json $P/hooks/hooks.json 2>/dev/null | grep -q timeout || echo "⚠️ hook 缺 timeout"

# 9. marketplace 一致性 (根 .claude-plugin/marketplace.json)
M=../../.claude-plugin/marketplace.json   # 按实际仓库结构调整
jq -r --arg n "$(jq -r '.name' $P/.claude-plugin/plugin.json)" '.plugins[] | select(.name==$n)' $M >/dev/null 2>&1 || echo "⚠️ marketplace 无此插件条目"
```

## 8 维评分 rubric（每维 1-10 × 权重，Σ/10 满分 100）

每维 4 列：**分 (1-10)** × **方向轴** (↑ 越高越好 / ↓ 越低越好) → **理想值** → **完成准则底线** (checkable + exhaustive，未达 = 该维未完成)。

| # | 维度 | 权重 | 方向 | 理想值 | 完成准则底线 (未达 = 该维未完成) |
|---|---|---|---|---|---|
| 1 | **Manifest 合规** | 16 | ↑ | 10 | `jq .` 通过；`name` kebab-case = 目录名；`description` 含「做什么 + 差异化」两要素；author/license/homepage 齐 |
| 2 | **组件接线完整** | 20 | ↑ | 10 | 体检 #3 #4 双向零悬挂零漏挂；路径大小写与磁盘一致 |
| 3 | **结构规范** | 12 | ↑ | 10 | 组件在插件根非 `.claude-plugin/`；`SKILL.md` 大写；`.claude-plugin/` 仅 `plugin.json` |
| 4 | **Hook 健壮性** | 14 | ↑ | 10 | 每 hook `${CLAUDE_PLUGIN_ROOT}` + `timeout` + 失败 `exit 0`；guard 用 `exit 2`；matcher 非 `*`；async 仅副作用型 |
| 5 | **组件质量** | 14 | ↑ | 8 | 逐 skill/agent/command 过：触发词准、无占位符残留（深评交 `/skill-dev`，本维只做门槛）|
| 6 | **Marketplace 一致性** | 12 | ↑ | 10 | `marketplace.json` name/source/description/author/license/keywords 与 `plugin.json` 逐字段对齐；source 路径存在；无 `../` |
| 7 | **文档完整** | 6 | ↑ | 8 | README 有装/用/例三段；`description` 无「灵活应用」空话尾巴 |
| 8 | **命名与元数据一致** | 6 | ↑ | 10 | 目录名 = manifest name = marketplace name；keywords 命中真实能力非堆砌 |

## 优化循环（validation-gate 纪律，6 要素缺一不可）

```
1. 体检硬伤先修 (维度 1/2/3 命中 = P0)
        ↓
2. 单变量轮: 一轮改一维度 (或一相关簇如 2/3/4 接线)
        ↓
3. 二层 gate 通过才留:
   - gross gate: 总分 Δ > 0 (体检硬伤数↓ + 接线零悬挂漏挂 + 质量门非空)
   - 人审 gate: 破坏性/接线/触发词变更 → 交用户确认 (禁「我觉得更好」直落)
   - 沿方向轴: 退步维度即使总分涨也标警示, 留滚交人审
        ↓ 不通过
4. ratchet 回滚: git revert HEAD (禁 git reset --hard, 保留历史可审计)
        ↓
5. 触顶停: 连续 2 轮 Δ < 2 → break
        ↓
6. 膨胀护栏: 改后体积 > 原 × 1.5 → 拒提交 (优化 ≠ 膨胀, 删 > 增)
```

### 独立验证 (防自评偏差)

每轮改完评分**禁同 context 自评**——spawn 独立子 agent 跑体检 + 评分，主 agent 只读结果。自评分数一律 +1 偏乐观，独立验证是唯一纠偏。

## 关键纪律

- **体检硬伤 P0 先于评分** — 维度 1/2/3 命中（JSON 非法 / 悬挂漏挂 / 组件误放）= 插件根本不工作，先修这些再谈质量
- **单变量轮** — 一轮只改一维度（或一相关簇：2/3/4 接线相关），多维同改归因失效
- **分数 fine-grained 不可信** — Δ>0 作 gross 信号；破坏性/接线/触发词变更必须用户确认，禁「我觉得更好」直落
- **方向轴校验** — 收敛不只看总分，退步维度（方向轴反向走）标警示，即使总分涨也交人审
- **组件深评交 `/skill-dev`** — 本 rubric 维度 5 只做门槛检查（有无占位符/触发词），单 skill 9 维评分路由 `/skill-dev` 流程 B
