---
id: S5
slug: verify
deliverable: all
parent-task: 06-09-cortex-skills-multifile
status: planned
execution-layer: main
depends-on: [S1, S2, S3, S4]
blocks: []
estimated-tokens: 3000
---

# S5 · 联合验证 + 暂存

## 目标

S1-S4 完成后, 跑结构 + 字段 + 内容完整性 三段校验, 全过后暂存.

## 验证

按 implement.md "验证命令 (S5)" 节跑.

补充内容完整性:
```bash
# 源 SKILL.md 已被覆盖, 用 git show HEAD:<path> 取原版做 token 子集校验
for s in cortex-schema-knowledge cortex-schema-memory cortex-lint cortex-extract; do
  orig=$(git show HEAD:plugins/tools/cortex/skills/$s/SKILL.md 2>/dev/null | grep -oE '[A-Za-z0-9_一-龥]+' | sort -u)
  new=$(cat plugins/tools/cortex/skills/$s/SKILL.md plugins/tools/cortex/skills/$s/references/*.md 2>/dev/null | grep -oE '[A-Za-z0-9_一-龥]+' | sort -u)
  missing=$(comm -23 <(echo "$orig") <(echo "$new") | head -20)
  [[ -z "$missing" ]] && echo "OK: $s no token loss" || echo "WARN: $s missing tokens: $missing"
done
```

## 资源

只读 + 暂存全部.

## 执行细节

S1-S4 全部 done 后:
1. 跑结构 + 字段校验
2. 跑内容完整性 diff (token 子集)
3. `git add plugins/tools/cortex/skills/`
4. 输出汇总

## 回滚

```bash
# S5 本身不写实质内容, 失败说明 S1-S4 某个不达标, 回到该 subtask 修
```
