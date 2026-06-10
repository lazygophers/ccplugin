# Implement — cortex skills 多文件改造

## Phase A — 并行拆 4 skill (S1//S2//S3//S4)

派 4 个 sub-agent 并行, 互不依赖.

- [ ] **[L3] S1** 拆 cortex-schema-knowledge → SKILL.md + references/{projects,domains,scripts}.md
- [ ] **[L3] S2** 拆 cortex-schema-memory → SKILL.md + references/{levels,axes-routing,properties}.md
- [ ] **[L3] S3** 拆 cortex-lint → SKILL.md + references/{rules,fixers,output}.md
- [ ] **[L3] S4** 拆 cortex-extract → SKILL.md + references/{classifier,io,usage}.md

每个 sub-agent 必须:
1. 先 Read 当前单文件 SKILL.md (信息源)
2. 删原 SKILL.md, 写新 SKILL.md (≤ 60 行) + references/*.md
3. frontmatter 改造:
   - `description` ≤ 512 字符 (扁平字符串, 不分行)
   - `when_to_use` ≤ 128 字符 (改成单行短句, 不再 yaml list)
   - 新增 `arguments` (按 design.md 规范)
   - 保持 `name` `argument-hint`

## Phase B — 联合验证 (S5)

- [ ] **[L1] S5.1** 跑 4 skill 结构 + 字段校验脚本
- [ ] **[L1] S5.2** 跑 cortex-lint 自检 (插件自己的 lint 是否也能识别新结构)
- [ ] **[L1] S5.3** 内容完整性 diff (源 SKILL.md token 子集校验)
- [ ] **[L1] S5.4** git add 暂存

## 验证命令 (S5)

```bash
# 结构 + 字段
for s in cortex-schema-knowledge cortex-schema-memory cortex-lint cortex-extract; do
  d=plugins/tools/cortex/skills/$s
  test -f $d/SKILL.md || { echo "FAIL: missing $d/SKILL.md"; exit 1; }
  ref_count=$(/usr/bin/find $d/references -name '*.md' -type f 2>/dev/null | wc -l | tr -d ' ')
  [[ $ref_count -ge 2 ]] || { echo "FAIL: $s references < 2 (got $ref_count)"; exit 1; }
  lines=$(wc -l < $d/SKILL.md | tr -d ' ')
  [[ $lines -le 60 ]] || { echo "FAIL: $s SKILL.md $lines > 60 lines"; exit 1; }
  python3 -c "
import yaml, sys
fm = yaml.safe_load(open('$d/SKILL.md').read().split('---')[1])
assert fm['name'] == '$s', f'name mismatch'
desc = fm['description']
wtu = fm['when_to_use'] if isinstance(fm['when_to_use'], str) else '/'.join(fm['when_to_use'])
assert len(desc) <= 512, f'description {len(desc)} > 512'
assert len(wtu) <= 128, f'when_to_use {len(wtu)} > 128'
assert fm.get('arguments'), 'arguments missing'
assert isinstance(fm['arguments'], list) and len(fm['arguments']) >= 1
print(f'$s: OK (desc={len(desc)}, wtu={len(wtu)}, args={len(fm[\"arguments\"])})')
" || exit 1
done
```

## Rollback

每 skill 独立, 失败仅:
```bash
git checkout plugins/tools/cortex/skills/<failed-skill>/
```
