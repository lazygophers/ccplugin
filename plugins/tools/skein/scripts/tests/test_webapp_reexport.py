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


DECL_RE = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", re.M)
EXPORT_FN_RE = re.compile(r"^\s*export\s+(?:async\s+)?function\s+([A-Za-z_$][\w$]*)", re.M)
IMPORT_RE = re.compile(r"^\s*import\s*\{([^}]*)\}\s*from\s*['\"]([^'\"]+)['\"]", re.M)
CALL_RE = re.compile(r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*\(")
# 字符串字面量 / 注释里的 `xxx()` 不是调用 (router.js 的报错文案里就写着 "page 未导出 render()")
LITERAL_RE = re.compile(r"'[^'\n]*'|\"[^\"\n]*\"|`[^`]*`|//[^\n]*|/\*.*?\*/", re.S)


def _blank_literals(src: str) -> str:
    """把字符串/注释内容抹成空格, **保留换行**以维持行号。"""
    return LITERAL_RE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), src)


def _bound_names(src: str) -> set[str]:
    """本模块内**能解析到**的名字: 自己声明的 + import 进来的 (含默认/命名空间导入)。"""
    names = set(DECL_RE.findall(src))
    names |= set(re.findall(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)", src, re.M))
    names |= set(re.findall(r"^\s*import\s+\*\s*as\s+([A-Za-z_$][\w$]*)", src, re.M))
    names |= set(re.findall(r"^\s*import\s+([A-Za-z_$][\w$]*)\s*(?:,|from)", src, re.M))
    for m in IMPORT_RE.finditer(src):
        for part in m.group(1).split(","):
            part = part.strip()
            if part:
                names.add(part.split(" as ")[-1].strip())
    return names


def _scan_unbound(files: list[Path]) -> list[str]:
    """调用了**兄弟模块导出的函数**却没 import 它 = 运行到那行必 ReferenceError。

    只拿「同目录树里某个模块 export 了这个名字」当证据, 避免把浏览器全局 / 局部变量误报成
    未绑定 —— 宁可漏报也不制造噪音。fmtHours / deltaText 两次事故都落在这个判据里。
    """
    exported: dict[str, Path] = {}
    for f in files:
        for name in EXPORT_FN_RE.findall(f.read_text(errors="ignore")):
            exported.setdefault(name, f)
    problems: list[str] = []
    for f in files:
        src = f.read_text(errors="ignore")
        bound = _bound_names(src)
        seen: set[str] = set()
        for i, ln in enumerate(_blank_literals(src).splitlines(), 1):
            if ln.lstrip().startswith(("import ", "export ", "//", "*")):
                continue
            for name in CALL_RE.findall(ln):
                if (name in exported and exported[name] != f
                        and name not in bound and name not in seen):
                    seen.add(name)
                    problems.append(
                        f"{f.name}:{i}: 调用了 `{name}()`, 但本模块没 import 它 "
                        f"(它 export 在 {exported[name].name}) — 运行到这行会 ReferenceError。")
    return problems


def test_no_call_to_unimported_sibling_export() -> None:
    problems = _scan_unbound(_js_files())
    assert not problems, "前端有跨模块调用却没 import:\n  " + "\n  ".join(problems)


def test_unbound_scanner_catches_a_planted_case(tmp_path: Path) -> None:
    """自检: 造「A export / B 直接调用不 import」, 必须被抓到; 补上 import 后不再报。"""
    (tmp_path / "eta.js").write_text("export function deltaText(d) { return d; }\n")
    bad = tmp_path / "view.js"
    bad.write_text("function row(d) { return deltaText(d); }\n")
    files = [tmp_path / "eta.js", bad]
    assert _scan_unbound(files), "自检失败: 未 import 的跨模块调用没被抓到"
    bad.write_text("import { deltaText } from './eta.js';\n"
                   "function row(d) { return deltaText(d); }\n")
    assert not _scan_unbound(files), "补了 import 仍被误报"


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
