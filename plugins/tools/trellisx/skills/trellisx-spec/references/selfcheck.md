# Spec 执行后自检

阶段 4 写盘完成后跑这套自检。任一不达标 → 报告给用户决定是否回阶段 2 重新提案。

## 必跑指标

### 命令式比例 ≥ 60%

```bash
total=$(grep -cE '^[-*]|^[0-9]+\.' .trellis/spec/**/*.md 2>/dev/null | awk -F: '{s+=$2} END {print s}')
must=$(grep -cE 'MUST|MUST NOT|禁|必须|严禁|必填|必带|必走|必经' .trellis/spec/**/*.md 2>/dev/null | awk -F: '{s+=$2} END {print s}')
[ "$total" -gt 0 ] && echo "命令式比例: $(( must * 100 / total ))%"
```

不达标 → 用户决定: 接受 (理由?) / 回阶段 2 重写。

### 描述式残留 = 0

```bash
grep -nrE '建议|可以|通常|尽量|应该|考虑|大概|差不多|尽快|适时' .trellis/spec/
```

任一命中 → 标记位置, 用户决定是否再改写。

### 死链 = 0

```bash
# 内部 wikilink + markdown 链接
grep -nrE '\[\[[^]]+\]\]|\]\([^)]+\)' .trellis/spec/ > /tmp/links.txt
# 逐条校验目标存在
while IFS= read -r line; do
    file=$(echo "$line" | cut -d: -f1)
    target=$(echo "$line" | grep -oE '\]\([^)]+\)' | head -1 | sed 's/^](\(.*\))$/\1/')
    [ -n "$target" ] && [ ! -f "$(dirname "$file")/$target" ] && echo "DEAD: $file → $target"
done < /tmp/links.txt
```

死链 > 0 → 必须修, 不接受跳过。

### 每文件首段说明完整

每个 spec 文件首段必须有 3 行:
- 何时被读
- 谁读
- 不遵守的代价

```bash
for f in .trellis/spec/**/*.md; do
    has_when=$(grep -c "何时被读" "$f")
    has_who=$(grep -c "谁读" "$f")
    has_cost=$(grep -c "不遵守的代价" "$f")
    if [ "$has_when" -eq 0 ] || [ "$has_who" -eq 0 ] || [ "$has_cost" -eq 0 ]; then
        echo "MISSING-META: $f"
    fi
done
```

### Frontmatter 完整

```bash
for f in .trellis/spec/**/*.md; do
    head=$(head -10 "$f")
    echo "$head" | grep -q "^updated:" || echo "NO-UPDATED: $f"
    echo "$head" | grep -q "^rewrite-version:" || echo "NO-VERSION: $f"
    echo "$head" | grep -q "^authored-by:" || echo "NO-AUTHOR: $f"
done
```

### index / 锚点对齐

```bash
# index.md 引用的所有锚点必须在目标文件存在
grep -oE '\]\([^)]+\)' .trellis/spec/index.md | while read ref; do
    path=$(echo "$ref" | sed 's/^](\(.*\))$/\1/')
    file=$(echo "$path" | cut -d# -f1)
    anchor=$(echo "$path" | cut -d# -f2)
    full=".trellis/spec/$file"
    [ ! -f "$full" ] && echo "INDEX-MISSING-FILE: $path" && continue
    [ -n "$anchor" ] && ! grep -q "^#.*$anchor" "$full" && echo "INDEX-MISSING-ANCHOR: $path"
done
```

### task manifest 引用同步性

本 skill 不动 task manifest, 但必须输出"待用户同步"清单:

```bash
# 把阶段 4 收集到的 affected manifest 列表给用户
cat /tmp/affected-manifests.txt
```

清单非空 → 提醒用户在下次 task planning 时同步。

## 健康度评分

```
[健康度评分]
- 命令式比例: X% (达标 ≥ 60%)            ✓ / ✗
- 描述式残留: Y 处 (达标 = 0)             ✓ / ✗
- 死链: Z 处 (达标 = 0)                   ✓ / ✗
- 首段说明完整: A/B 文件                  ✓ / ✗
- frontmatter 完整: A/B 文件              ✓ / ✗
- index 锚点对齐: A/B 引用                ✓ / ✗
- 受影响 manifest: K 项 (待用户同步)      —

总评: 健康 / 需手工修 X 处 / 重新提案
```

## 不达标处理

| 失败项 | 一线修复 | 仍失败兜底 |
| --- | --- | --- |
| 命令式比例 < 60% | 走 AskUserQuestion 让主会话定: 接受 + 标 TODO / 回阶段 2 | 用户不决 → 默认回阶段 2 重新提案, 禁自行降标准接受 |
| 描述式残留 > 0 | PATCH 改写残留条款为命令式 | hot-patch 改不动 (语义需重设计) → 回阶段 2 |
| 死链 > 0 | 直接 PATCH 修引用路径 | 目标文件不存在且无替代 → 报告主会话, 由用户决定建占位或删引用方 |
| 首段 / frontmatter 缺 | PATCH 直接补 | — |
| index 锚点错 | PATCH 修 index | 锚点对应节已删 → 同步删 index 该行 |

完成自检 + 必要修复后, 跑 final 报告返回主会话。
