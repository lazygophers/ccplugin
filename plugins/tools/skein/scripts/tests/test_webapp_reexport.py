"""前端模块的**纯转发再导出**不得与本文件内的使用混用。

## 踩过的坑
把 ETA 数学从 `app.js` 抽进 `eta.js` 后, app.js 里写的是:

    export { fmtHours, etaOf, ... } from './eta.js';

这句只是**转发** —— 它让别的模块能 `from '../app.js'` 拿到这些名字, 但**不在 app.js 自己的
作用域里建立绑定**。于是 app.js 内部那几处 `fmtHours(...)` 调用当场
`ReferenceError: fmtHours is not defined`, 而且只在真渲染到那一行时才炸 (用户点开 task
详情面板才触发)。语法检查、模块加载全都过得去。

正确写法是拆两行:

    import { fmtHours } from './eta.js';    // 给本文件用
    export { fmtHours };                    // 维持对外契约

## 这条检查在干什么
扫每个前端模块的 `export { ... } from '...'` 行, 取出被转发的名字, 再看这些名字有没有在
**同文件的其他地方**作为标识符出现。有 = 本文件自己要用它 = 必须改成 import + export。

## 局限
纯文本扫描, 不解析 JS。会把字符串字面量 / 注释里的同名词算作"使用"—— 那只会**多报**不会漏报,
而多报一次的代价是加一行 import, 可以接受。
"""
from __future__ import annotations

import re
from pathlib import Path

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from conftest import SCRIPTS  # noqa: E402

WEBAPP = SCRIPTS.parent / "assets" / "webapp" / "src" / "new"
# `export { a, b as c } from './x.js'`
REEXPORT_RE = re.compile(r"^\s*export\s*\{([^}]*)\}\s*from\s*['\"][^'\"]+['\"]", re.M)


def _js_files() -> list[Path]:
    return sorted(p for p in WEBAPP.rglob("*.js") if "vendor" not in p.parts)


def _local_uses(src: str, name: str, skip_lines: set[int]) -> list[int]:
    """name 在 src 里作为标识符出现的行号 (跳过 skip_lines 里那些再导出行)。"""
    pat = re.compile(rf"(?<![\w$.]){re.escape(name)}(?![\w$])")
    return [i for i, ln in enumerate(src.splitlines(), 1)
            if i not in skip_lines and pat.search(ln)]


def _scan(files: list[Path]) -> list[str]:
    problems: list[str] = []
    for f in files:
        src = f.read_text(errors="ignore")
        skip = {i for i, ln in enumerate(src.splitlines(), 1)
                if REEXPORT_RE.match(ln + "\n")}
        if not skip:
            continue
        forwarded: set[str] = set()
        for m in REEXPORT_RE.finditer(src):
            for part in m.group(1).split(","):
                part = part.strip()
                if not part:
                    continue
                # `a as b` → 本文件里能用的是 a (源名), 但两个都查一遍最稳
                forwarded.update(t.strip() for t in part.split(" as ") if t.strip())
        for name in sorted(forwarded):
            hits = _local_uses(src, name, skip)
            if hits:
                problems.append(
                    f"{f.relative_to(WEBAPP) if WEBAPP in f.parents else f.name}: `{name}` 只被转发导出, 但第 {hits[:3]} 行还在本文件里用它 "
                    f"— 转发不建立局部绑定, 运行到那行会 ReferenceError。改成 "
                    f"`import {{ {name} }} from '...'` + `export {{ {name} }}` 两行。")
    return problems


def test_no_reexport_used_locally() -> None:
    problems = _scan(_js_files())
    assert not problems, "前端有纯转发再导出被本文件使用:\n  " + "\n  ".join(problems)


def test_scanner_catches_a_planted_case(tmp_path: Path) -> None:
    """自检: 造一个「转发 + 本地使用」的文件, 必须被抓出来。"""
    bad = tmp_path / "bad.js"
    bad.write_text(
        "export { fmtHours } from './eta.js';\n"
        "function show(h) { return fmtHours(h); }\n")
    assert _scan([bad]), "自检失败: 明显的转发+本地使用没被抓到"

    good = tmp_path / "good.js"
    good.write_text(
        "import { fmtHours } from './eta.js';\n"
        "export { fmtHours };\n"
        "function show(h) { return fmtHours(h); }\n")
    assert not _scan([good]), "正确写法被误报"

    pure = tmp_path / "pure.js"
    pure.write_text("export { helper } from './x.js';\n")
    assert not _scan([pure]), "纯转发 (本文件不用) 被误报"


if __name__ == "__main__":
    probs = _scan(_js_files())
    for p in probs:
        print("  " + p)
    print(f"前端再导出检查: {len(probs)} 处问题")
    raise SystemExit(1 if probs else 0)
