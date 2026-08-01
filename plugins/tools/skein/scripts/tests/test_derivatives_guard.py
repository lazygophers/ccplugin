"""防漂移守卫: 新增衍生物写盘点必须先在 `derivatives.DERIVATIVES` 登记, 否则本测试报红。

## 为什么 (design.md「防漂移守卫」)
清单曾经手写维护过一次, 漏了几条 (hook 计数标记、索引聚合类产物), 多了一条历史残留。
「靠人记得同步」已经证明不成立。这条测试是唯一的自动兜底: 有人加了新的可重建产物写盘点,
却忘了去 `derivatives.py` 登记, CI 就该炸, 而不是等下一次人工盘点时才发现。

## 怎么查 (源码文本扫描, 不用运行时探测)
理由同 `test_no_dangling_self.py`: 条件分支里的写盘点运行时探测不到, 但扫描得到。

对 `skeinlib/` 下每个 `.py`, 找出「函数体内含写盘调用」(`.write_text()` / `.write_bytes()` /
`open(path, "w"/"a"/...)` / `.write_if_changed()`) 的函数, 再在**同一函数体**内结构化收集
「明显被当路径片段用」的字符串字面量 —— 只取三类位置: `目录 / "字面量"` (pathlib `/`)、
`os.path.join()`/`Path()` 调用参数、dict 字面量的 key (`{"prd.md": ...}` 这种 task scaffold
写法)。只取这三类位置, 不做全文本字面量扫描, 是为了不把 docstring/提示语里长得像文件名的碎片
(比如版本号 "3.11") 也当成写盘目标 —— 见下方「误报处理」。

收集到的字面量, 每个都必须能被下面两类之一覆盖, 否则判为「疑似未登记衍生物写盘点」:
1. `derivatives.DERIVATIVES` 里某条 pattern 的叶子名 (basename) fnmatch 命中
2. `TRUTH_FILES` (真值, 有写盘点但不可忽略) 或 `OFF_SCOPE_FILES` (不在 `.skein` 工作区范围内,
   与本登记处无关, 如 `.claude/settings.local.json`)

## 局限 (写清楚免得后人高估它)
1. 只看**同一函数体**内的字面量。写盘调用与构造路径的字面量隔了一层函数调用 (比如
   `store.py::write_if_changed(path, content)` 这个通用写盘 helper, 调用点的文件名字面量在
   *调用方* 函数里, 不在 `write_if_changed` 自己里) 时, 两头各查各的都摸不到对方 —— 这条测试
   摸不到。已把 `write_if_changed` 本身也算作写盘 sink 名字, 缓解一部分 (调用方函数只要自己
   直接组出字面量路径就仍能被抓到), 但方法级间接 (先调用一个只返回 Path 的辅助方法, 如
   `boardsource.py::_lock_file()`) 仍然漏。
2. 只抓结构化位置的字面量, 遇到纯字符串拼接 (`"a" + "b" + ".md"`) 或 f-string 里的动态段
   (`f"{topic}.md"`) 摸不到 —— 这类路径本来就无法在扫描期确定具体文件名, 摸不到是预期行为
   (拿不准就不误判, 而非漏报"能查的都不查")。
3. 结论: 宁可漏报, 不可误报 —— 见下方三条误报回归测试, 已用真实案例 (task.json/prd.md/
   已登记衍生物) 钉死不会被错杀。
"""
from __future__ import annotations

import ast
import fnmatch
import re
from pathlib import Path

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from skeinlib.derivatives import DERIVATIVES  # noqa: E402

SKEINLIB_DIR = Path(__file__).resolve().parent.parent / "skeinlib"

# 写盘调用的方法名 (`.write_text()`/`.write_bytes()` 是标准 API; `write_if_changed` 是
# store.py 自己的写盘 helper, 未来新增派生 .md 渲染大概率复用它, 一并当 sink 处理)。
WRITE_SINK_METHODS = {"write_text", "write_bytes", "write_if_changed"}
OPEN_WRITE_MODES = {"w", "wb", "a", "ab", "x", "xb"}

# 真值文件 (判据见 design.md「衍生物 vs 真值」): 有写盘点但绝不可忽略, 守卫不要求登记。
TRUTH_FILES = {
    "task.json",   # store.py 落盘层唯一写入口 / migrate.py 迁入数据
    "config.yaml",  # admin.py / workspace.py 用户配置
    "prd.md",      # prd.py / artifacts.py planning 唯一人写入口
    "design.md",   # lifecycle.py task scaffold
    ".gitignore",  # 本文件自身, 必须入库, 绝不可被自己忽略
}
# 不在 `.skein` 工作区范围内的写盘点 (如 .claude/settings*.json), 与本登记处无关, 不要求登记;
# 含工作区/宿主目录名本身 (`.skein`/`.claude`/`.trellis` —— 这些是路径拼接用的目录锚点字面量,
# 不是「产物」, 不该被判成待登记的衍生物)。
OFF_SCOPE_FILES = {"settings.json", "settings.local.json", ".skein", ".claude", ".trellis"}

_FILENAME_RE = re.compile(r"^(\.[\w.\-]+|[\w][\w.\-]*\.[A-Za-z0-9]{1,10}|[\w][\w.\-]*/)$")


def _is_filename_shaped(s: str) -> bool:
    """判据: 带扩展名 (`index.md`) / 点开头的 dotfile (`.pending-fix`) / 尾斜杠目录 (`trash/`)。
    过滤掉不含点、不像文件名的目录名片段 (如单独的 `"task"`), 减少无关噪声。"""
    return bool(_FILENAME_RE.fullmatch(s))


def _has_write_call(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if not isinstance(child, ast.Call):
            continue
        func = child.func
        if isinstance(func, ast.Attribute) and func.attr in WRITE_SINK_METHODS:
            return True
        if isinstance(func, ast.Name) and func.id == "open":
            mode = None
            if len(child.args) >= 2 and isinstance(child.args[1], ast.Constant):
                mode = child.args[1].value
            for kw in child.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if isinstance(mode, str) and mode in OPEN_WRITE_MODES:
                return True
    return False


def _collect_path_literals(node: ast.AST) -> set[str]:
    """收集函数体内「结构化用作路径片段」的字符串字面量, 见模块 docstring「怎么查」。"""
    lits: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.BinOp) and isinstance(child.op, ast.Div):
            for side in (child.left, child.right):
                if isinstance(side, ast.Constant) and isinstance(side.value, str):
                    lits.add(side.value)
        elif isinstance(child, ast.Call):
            fn = child.func
            is_join = (isinstance(fn, ast.Attribute) and fn.attr == "join") or (
                isinstance(fn, ast.Name) and fn.id == "Path")
            if is_join:
                for a in child.args:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        lits.add(a.value)
        elif isinstance(child, ast.Dict):
            for k in child.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    lits.add(k.value)
    return {s for s in lits if _is_filename_shaped(s)}


def _registered_leaves() -> set[str]:
    """DERIVATIVES 每条 pattern 的叶子名 (basename)。收集到的字面量多是
    `目录变量 / "叶子名"` 里的叶子, 天然不含 DERIVATIVES 里记的父目录前缀
    (如 `spec/.pending-fix` 的叶子是 `.pending-fix`), 所以按叶子比对。"""
    return {d.pattern.rstrip("/").rsplit("/", 1)[-1] for d in DERIVATIVES}


def _is_covered(lit: str, leaves: set[str]) -> bool:
    if lit in TRUTH_FILES or lit in OFF_SCOPE_FILES:
        return True
    stripped = lit.rstrip("/")
    return any(fnmatch.fnmatch(stripped, leaf) for leaf in leaves)


def _scan_unregistered_writes(root: Path) -> list[tuple[str, str, str]]:
    """返回 (文件相对路径, 函数名, 未覆盖字面量) 列表 —— 疑似未登记衍生物写盘点。"""
    leaves = _registered_leaves()
    bad: list[tuple[str, str, str]] = []
    for f in sorted(root.rglob("*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not _has_write_call(node):
                continue
            for lit in _collect_path_literals(node):
                if not _is_covered(lit, leaves):
                    bad.append((str(f.relative_to(root)), node.name, lit))
    return bad


def test_no_unregistered_derivative_writes() -> None:
    """全量守卫: skeinlib/ 下不存在「写盘点未登记且非真值/域外」的情况。"""
    bad = _scan_unregistered_writes(SKEINLIB_DIR)
    assert not bad, (
        "发现疑似未登记的衍生物写盘点 (文件:函数(): 字面量) — 若确实是可重建产物, 去 "
        "skeinlib/derivatives.py 的 DERIVATIVES 补登记; 若是真值/域外文件, 加进本测试的 "
        "TRUTH_FILES/OFF_SCOPE_FILES:\n" +
        "\n".join(f"  {p}:{fn}(): {lit!r}" for p, fn, lit in bad))


def test_probe_catches_a_planted_unregistered_write(tmp_path: Path) -> None:
    """自检 (反向验证): 造一个「新衍生物写盘点但未登记」, 必须被抓到 ——
    没红过的守卫等于没有守卫。"""
    (tmp_path / "planted.py").write_text(
        "from pathlib import Path\n\n"
        "class Foo:\n"
        "    def render(self, d: Path) -> None:\n"
        "        p = d / 'totally_new_derivative.report'\n"
        "        p.write_text('x')\n",
        encoding="utf-8")
    bad = _scan_unregistered_writes(tmp_path)
    assert bad == [("planted.py", "render", "totally_new_derivative.report")], f"自检失败, 实际 {bad}"


def test_registered_derivative_write_is_not_flagged(tmp_path: Path) -> None:
    """误报回归: 已登记衍生物 (如 vision.md) 的写盘点不能被误判为漏登记。"""
    (tmp_path / "planted_ok.py").write_text(
        "from pathlib import Path\n\n"
        "class Foo:\n"
        "    def render(self, d: Path) -> None:\n"
        "        p = d / 'vision.md'\n"
        "        p.write_text('x')\n",
        encoding="utf-8")
    assert _scan_unregistered_writes(tmp_path) == []


def test_truth_write_is_not_flagged(tmp_path: Path) -> None:
    """误报回归: 真值写盘点 (如 task.json) 不能被误判为漏登记衍生物 ——
    判错方向的代价不对称 (design.md), 这条测试钉死"真值绝不误伤"这一侧。"""
    (tmp_path / "planted_truth.py").write_text(
        "from pathlib import Path\n\n"
        "class Foo:\n"
        "    def save(self, d: Path) -> None:\n"
        "        p = d / 'task.json'\n"
        "        p.write_text('{}')\n",
        encoding="utf-8")
    assert _scan_unregistered_writes(tmp_path) == []


def test_docstring_lookalike_literal_is_not_flagged(tmp_path: Path) -> None:
    """误报回归: 写盘调用附近若有「长得像文件名但其实是 docstring/提示语碎片」的字面量
    (如版本号 "3.11"), 因为不在结构化路径位置上, 不会被当成写盘目标误抓。"""
    (tmp_path / "planted_doc.py").write_text(
        "from pathlib import Path\n\n"
        "class Foo:\n"
        "    def save(self, d: Path) -> None:\n"
        "        \"\"\"依赖 python 3.11.\"\"\"\n"
        "        p = d / 'task.json'\n"
        "        p.write_text('{}')\n",
        encoding="utf-8")
    assert _scan_unregistered_writes(tmp_path) == []


if __name__ == "__main__":
    import inspect
    import tempfile

    for name, fn in sorted(globals().items()):
        if not (name.startswith("test_") and callable(fn)):
            continue
        if "tmp_path" in inspect.signature(fn).parameters:
            with tempfile.TemporaryDirectory() as td:
                fn(Path(td))
        else:
            fn()
    print("衍生物登记守卫自检过")
