# modify-flow — Dataview 块改写 SOP

修改 vault 内已存在的 Dataview 块时, 用本 SOP 保证幂等 + 不破坏用户自定义。

## 1. Marker 契约

cortex 生成的每个 Dataview 块带头部 HTML 注释 marker:

```html
<!-- cortex-dataview v1 kind=table hash=a3f9b2c1 -->
```

字段:
- `v<N>` — marker schema 版本 (当前 v1)
- `kind=<dql|dataviewjs|inline|task|list|table|calendar>` — 块类型, 决定 fence 语言 + 解析路径
- `hash=<sha1[:8]>` — 块体 (不含 marker 自身) sha1 前 8 位; 重生成时若 hash 一致即跳过

**无 marker 的块视为用户手写, 修改前必 `AskUserQuestion` 确认是否接管。**

## 2. 检测流程

```
1. Read 目标文件全文
2. regex 扫所有 fence:
     ^```dataview(?:js)?\s*$\n(.*?)^```\s*$
3. 对每个 match 检查上一非空行:
     是 cortex-dataview marker → 已被托管, 走 update 路径
     不是                      → 用户手写, 跳过或询问
4. 若用户请求"在这里插入" 但未指定位置:
     默认插入在 frontmatter 后第一个 H2 之前 (顶部)
     或用户指定 heading 之下
```

regex 完整版 (含 marker):

```python
import re
PATTERN = re.compile(
    r"(?:^<!--\s*cortex-dataview\s+v(\d+)\s+kind=(\w+)\s+hash=([a-f0-9]+)\s*-->\s*\n)?"
    r"^```(dataview(?:js)?)\s*\n"
    r"(.*?)\n"
    r"^```\s*$",
    re.M | re.S,
)
```

## 3. 幂等替换

```python
import hashlib

def new_marker(kind: str, body: str, v: int = 1) -> str:
    h = hashlib.sha1(body.encode("utf-8")).hexdigest()[:8]
    return f"<!-- cortex-dataview v{v} kind={kind} hash={h} -->"

def replace_block(file_text: str, kind: str, new_body: str) -> tuple[str, bool]:
    """Returns (new_text, changed). changed=False if hash already matches."""
    marker = new_marker(kind, new_body)
    fence = "dataviewjs" if kind == "dataviewjs" else "dataview"
    new_block = f"{marker}\n```{fence}\n{new_body}\n```"

    def repl(m):
        old_hash = m.group(3)
        new_hash = hashlib.sha1(new_body.encode("utf-8")).hexdigest()[:8]
        if old_hash == new_hash:
            return m.group(0)  # skip
        return new_block

    new_text = PATTERN.sub(repl, file_text, count=1)
    return new_text, new_text != file_text
```

## 4. 安全策略

| 操作 | AUTO_MODE | Interactive |
|---|---|---|
| 生成 / 改写 DQL 块 | ✅ 直接 | ✅ 直接 |
| 生成 / 改写 dataviewjs 块 | ❌ 拒绝 (输出提示要换用 DQL 或显式批准) | ⚠️ AskUserQuestion 用户必显式选 "allow" |
| 删除 dataview 块 | ⚠️ AskUserQuestion | ⚠️ AskUserQuestion |
| 移动块位置 | ✅ 直接 | ✅ 直接 |

理由: dataviewjs 是任意 JS, 写入用户 vault 等同 RCE 风险; cortex 安全基线不允许 AI 默认行为生成可执行代码。

## 5. 写入前 lint

写入前快速本地 lint:

```python
def lint_dql(body: str) -> list[str]:
    errors = []
    head = body.lstrip().split(maxsplit=1)[0].upper() if body.strip() else ""
    if head not in {"LIST", "TABLE", "TASK", "CALENDAR"}:
        errors.append(f"first token must be LIST/TABLE/TASK/CALENDAR, got '{head}'")
    # 检查 procedural 顺序: WHERE 必须在 GROUP BY 前, LIMIT 必须最后等
    lines = [l.strip().upper() for l in body.splitlines() if l.strip()]
    clauses = [l.split()[0] for l in lines if l and l.split()[0] in
               {"FROM", "WHERE", "SORT", "GROUP", "FLATTEN", "LIMIT"}]
    order = {"FROM": 0, "WHERE": 1, "SORT": 2, "GROUP": 3, "FLATTEN": 4, "LIMIT": 5}
    last = -1
    for c in clauses:
        if c == "GROUP":  # GROUP BY counts as GROUP
            cur = order[c]
        else:
            cur = order.get(c, 99)
        if cur < last:
            errors.append(f"clause order violated: {c} after higher-rank clause")
        last = cur
    return errors
```

完整 DQL 语法见 `dql-syntax.md`。

## 6. 与 cortex-dashboard / cortex-cartographer 边界

| skill | marker | 用途 |
|---|---|---|
| **cortex-dashboard** | `<!-- DASH:BEGIN/END -->` | Bases / Dataview 仪表盘三件套 (index/hot/dashboard) |
| **cortex-cartographer** | (no marker, 重渲 canvas) | canvas + dashboard 渲染编排 |
| **cortex-dataview** (本) | `<!-- cortex-dataview v1 ... -->` | 单个 Dataview 块 (DQL/dataviewjs) 的构建 / 修改 / 解释 |

三者**互不替代**: dashboard 管全局 KPI block, cartographer 管视图重渲, 本 skill 管原子 DQL 块。

## 7. 失败回滚

修改失败 (lint 不过 / 文件写错) → 不写盘, 输出错误 + 候选修正给用户。**绝不**生成"半成品" Dataview 块 (用户加载时 plugin 报错噪音大)。
