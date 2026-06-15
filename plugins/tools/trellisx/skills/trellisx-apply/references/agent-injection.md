# plan-agent / write-agent: 注入 trellis agent `background: true`

apply 确保 `.claude/agents/` 下所有 **`trellis` 开头**的 agent frontmatter 都有 `background: true`。这些是 trellis init 生成的 sub-agent (trellis-check / trellis-implement / trellis-research 等), 让它们默认后台运行。

## 规则 (幂等)

对每个 `.claude/agents/trellis*.md`:
- frontmatter 已有 `background: true` → 跳过 (幂等)
- frontmatter 有 `background:` 但值 ≠ true → **强制改为 `true`**
- frontmatter 无 `background` 字段 → **追加 `background: true`** (插在 frontmatter 末尾)
- 无 frontmatter (无 `---` 块) → 跳过 + 警告 (不破坏非常规文件)

## 算法

```python
import re, glob

for f in glob.glob(".claude/agents/trellis*.md"):
    s = open(f, encoding="utf-8").read()
    m = re.match(r"^(---\n)(.*?)(\n---\n)", s, re.DOTALL)
    if not m:
        print(f"trellisx: {f} 无 frontmatter, 跳过", file=sys.stderr)
        continue
    head, fm, tail = m.group(1), m.group(2), m.group(3)
    if re.search(r"(?m)^background:\s*true\s*$", fm):
        continue                                              # 已 true → 幂等跳过
    if re.search(r"(?m)^background:\s*\S.*$", fm):
        fm = re.sub(r"(?m)^background:\s*\S.*$", "background: true", fm)   # 非 true → 强制改
    else:
        fm = fm.rstrip() + "\nbackground: true"               # 缺 → 末尾追加
    open(f, "w", encoding="utf-8").write(head + fm + tail + s[m.end():])
    print(f"trellisx: {f} background: true", file=sys.stderr)
```

> 注: `background` 是顶层 key, 追加在 frontmatter 末尾 (不会落进 `description: |` 多行块, 因 `tools:` 等后续顶层 key 已脱离该块)。

## 验证

```bash
for f in .claude/agents/trellis*.md; do
  [ -f "$f" ] || continue
  awk '/^---$/{c++} c==1&&/^background:[[:space:]]*true[[:space:]]*$/{ok=1} c==2{print (ok?"✓":"✗"), FILENAME; exit}' "$f"
done
```
全 ✓ = 每个 trellis agent frontmatter 都有 `background: true`。

## 边界

- 只动 `trellis` 开头的 agent (trellis init 生成的); 不碰用户自定义 / 其他 agent
- 只增/改 `background` 一个字段, frontmatter 其余 (name/description/tools) 一字不动
- trellis update 重置 agent 文件后需重跑 apply 恢复 (同 workflow.md 注入)
