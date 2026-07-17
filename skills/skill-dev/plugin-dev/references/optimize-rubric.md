# 优化评分 Rubric + 体检命令

> 流程 B 的细节层：先机械体检定位硬伤，再按 8 维 rubric 打分排优先级，一轮修一类。

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

| # | 维度 | 权重 | 评分要点 |
|---|---|---|---|
| 1 | **Manifest 合规** | 16 | JSON 合法；`name` 必填 kebab-case = 目录名；`description` 说清做什么+差异化；author/license/homepage 齐 |
| 2 | **组件接线完整** | 20 | `skills[]/agents[]/commands[]` 每条有真实文件（无悬挂）+ 每个文件被挂载（无漏挂）；路径大小写正确 |
| 3 | **结构规范** | 12 | 组件在插件根不在 `.claude-plugin/`；`SKILL.md` 大写；agent/command frontmatter 必填字段齐；`.claude-plugin/` 只放 `plugin.json` |
| 4 | **Hook 健壮性** | 14 | `${CLAUDE_PLUGIN_ROOT}` 而非硬路径；每 hook 带 `timeout`；matcher 精确（非 `*`）；失败 exit 0 兜底；guard 用 exit 2 禁 exit 1；幂等；async 仅副作用型 |
| 5 | **组件质量** | 14 | 逐个 skill/agent/command 过：触发词准、失败模式编码、无占位符残留（深评单 skill 另跑 `/skill-dev` 流程 B，本维度只做门槛检查）|
| 6 | **Marketplace 一致性** | 12 | `marketplace.json` 条目 name/source/description/author/license/keywords 与 `plugin.json` 一致；source 路径存在；无 `../` 引外部 |
| 7 | **文档完整** | 6 | README 有装/用/例；CHANGELOG（如版本化）；description 无「灵活应用」空话尾巴 |
| 8 | **命名与元数据一致** | 6 | 目录名 = manifest name = marketplace name；keywords 命中真实能力非堆砌 |

## 优化循环

```
体检硬伤（维度 1/2/3 命中 = P0）先修
  ↓
按最低维度一轮改一类（单变量轮）
  ↓
改后重跑体检 + 过质量门（硬规 5: claude -p）
  ↓
严格更好才留（体检硬伤数↓ + 接线 0 悬挂/漏挂 + 质量门非空）
  ↓ 否则
git revert
  ↓
触顶（连续 2 轮 Δ < 2）→ break
```

## 关键纪律

- **体检硬伤 P0 先于评分** — 维度 1/2/3 命中（JSON 非法 / 悬挂漏挂 / 组件误放）= 插件根本不工作，先修这些再谈质量
- **单变量轮** — 一轮只改一维度（或一相关簇：2/3/4 接线相关），多维同改归因失效
- **分数 fine-grained 不可信** — Δ>0 作 gross 信号；破坏性/接线/触发词变更必须用户确认，禁「我觉得更好」直落
- **组件深评交 `/skill-dev`** — 本 rubric 维度 5 只做门槛检查（有无占位符/触发词），单 skill 9 维评分路由 `/skill-dev` 流程 B
