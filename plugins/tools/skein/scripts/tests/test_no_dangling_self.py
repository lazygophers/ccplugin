"""静态守卫: `self.X` 引用必须真的存在 — 抓「方法搬走了但调用点还在」。

## 为什么需要这条
分包过程中同一类故障出现了两次:

1. `boardsource._run_server` 调 `self._probe_same_project(...)`, 而那个方法早已提成
   `serve.probe_same_project(...)` 模块函数 → `AttributeError: 'Skein' object has no
   attribute '_probe_same_project'`, **只在真起 serve 时才炸**。
2. `uvicorn.run("skeinlib.web.serve:_serve_app_factory")` 的模块字符串没跟着函数搬家 (另有测试守)。

共同点: 失效点在**运行时才解析**, 而覆盖它的测试要么起真服务、要么开浏览器, 单测天然摸不到。
Python 又没有编译期检查, 于是搬完家全绿, 用户跑起来才崩。

## 怎么查
把 `Skein` / `Spec` 两个门面装配起来 (mixin 全挂上), 收集每个类方法体里所有 `self.<name>`
访问, 逐一确认: 类上有 (方法/属性), 或在某个 `__init__` 里被 `self.<name> = ` 赋过值。
两者都不满足 = 悬空引用。

## 局限 (写清楚免得后人高估它)
只看**字面** `self.<name>`, 不追 `getattr(self, x)` / `setattr` 这类动态访问。当前代码没有
那种用法; 真要加, 得同时把这条测试的能力边界补上, 别让它给出虚假的安全感。
"""
from __future__ import annotations

import ast
import inspect

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from skeinlib.core.admin import Admin  # noqa: E402
from skeinlib.core.artifacts import Artifacts  # noqa: E402
from skeinlib.core.commands import Skein  # noqa: E402
from skeinlib.core.lifecycle import Lifecycle  # noqa: E402
from skeinlib.core.query import Query  # noqa: E402
from skeinlib.core.scheduling import Scheduler  # noqa: E402
from skeinlib.spec.facade import Spec  # noqa: E402
from skeinlib.core.workspace import Workspace  # noqa: E402

# 五个协作对象 (commands.Skein 的装配图)。它们不再共享一个 self, 而是持有 self.ws ——
# 于是同一类故障换了个马甲: `self.ws.<搬走的方法>`。下面第二条检查专治这个。
COLLABORATORS = (Admin, Lifecycle, Scheduler, Query, Artifacts)


def _self_attrs(cls: type) -> tuple[set[str], set[str]]:
    """扫遍 cls 的 MRO(含 mixin), 返回 (被读的 self.X, 被赋值的 self.X)。"""
    read: set[str] = set()
    assigned: set[str] = set()
    for klass in cls.__mro__:
        if klass is object:
            continue
        try:
            src = inspect.getsource(klass)
        except (OSError, TypeError):
            continue
        tree = ast.parse(_dedent(src))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            if not (isinstance(node.value, ast.Name) and node.value.id == "self"):
                continue
            (assigned if isinstance(node.ctx, ast.Store) else read).add(node.attr)
    return read, assigned


def _dedent(src: str) -> str:
    """inspect.getsource 对嵌套类会带缩进, 统一去掉首行缩进。"""
    lines = src.splitlines()
    pad = len(lines[0]) - len(lines[0].lstrip())
    return "\n".join(ln[pad:] if len(ln) > pad else ln.lstrip() for ln in lines)


def _dangling(cls: type) -> list[str]:
    read, assigned = _self_attrs(cls)
    return sorted(name for name in read
                  if not hasattr(cls, name) and name not in assigned)


def test_skein_has_no_dangling_self_reference() -> None:
    """`Skein` (含 DoctorMixin / BoardSourceMixin) 的 self.X 全都解析得到。"""
    missing = _dangling(Skein)
    assert not missing, (
        f"Skein 上有 {len(missing)} 个悬空引用 {missing} — 方法搬去模块函数后忘了改调用点。"
        f"这类故障只在真跑到那条分支时才炸 (如 `skein serve` 复用已有服务那一支)。")


def test_collaborators_have_no_dangling_self_reference() -> None:
    """五个协作对象各自的 self.X 也要解析得到 (它们不在 Skein 的 MRO 上, 上面那条盖不到)。"""
    for cls in COLLABORATORS:
        missing = _dangling(cls)
        assert not missing, f"{cls.__name__} 上有悬空引用 {missing}"


def _ws_members() -> set[str]:
    """Workspace 上真实存在的名字: 类上的方法/属性 + `__init__` 里 `self.X =` 赋过的。

    只用 `hasattr` 不够 —— `store` / `root` / `tasks` 这些是实例属性, 类上查不到。
    """
    _, assigned = _self_attrs(Workspace)
    return {n for n in dir(Workspace) if not n.startswith("__")} | assigned


def _dangling_ws(cls: type, members: set[str] | None = None) -> list[str]:
    """`self.ws.<name>` 里 name 在 Workspace 上不存在的那些。"""
    known = _ws_members() if members is None else members
    missing: list[str] = []
    try:
        tree = ast.parse(_dedent(inspect.getsource(cls)))
    except (OSError, TypeError):
        return missing
    for node in ast.walk(tree):
        # 形状: Attribute(value=Attribute(value=Name('self'), attr='ws'), attr=<name>)
        if not isinstance(node, ast.Attribute):
            continue
        inner = node.value
        if not (isinstance(inner, ast.Attribute) and inner.attr == "ws"
                and isinstance(inner.value, ast.Name) and inner.value.id == "self"):
            continue
        if node.attr not in known:
            missing.append(node.attr)
    return sorted(set(missing))


def test_collaborators_only_touch_real_workspace_members() -> None:
    """协作对象经 `self.ws.X` 摸到的东西必须真在 `Workspace` 上。

    这是分包后**新出现**的悬空形态: 把某个方法从 Workspace 挪走 (或改名), 五个协作对象里的
    `self.ws.那个名字` 一个都不会报错, 直到真跑到那条分支。和当初 `_probe_same_project` 同一
    个坑, 只是多了一跳。
    """
    members = _ws_members()
    bad = {cls.__name__: d for cls in COLLABORATORS if (d := _dangling_ws(cls, members))}
    assert not bad, (
        f"这些协作对象引用了 Workspace 上不存在的成员: {bad} — "
        f"Workspace 现有: {sorted(members)}")


def test_ws_probe_catches_a_planted_case() -> None:
    """自检: 造一个 `self.ws.不存在的东西`, 必须被抓到。"""
    class Fake:
        def __init__(self, ws: object) -> None:
            self.ws = ws

        def ok(self) -> object:
            return self.ws.store          # type: ignore[attr-defined] # Workspace 上真有, ws 故意标 object 让检查器只靠 AST 摸名字, 从不真跑

        def broken(self) -> object:
            return self.ws.gone_away()    # type: ignore[attr-defined] # ← 没有, 同上: 故意植入的悬空引用, 只喂 ast.parse 不执行

    got = _dangling_ws(Fake)
    assert got == ["gone_away"], f"自检失败, 实际 {got}"


def test_spec_has_no_dangling_self_reference() -> None:
    """`Spec` (含 Index/Inject/Write/Maintain 四个 mixin) 同理。"""
    missing = _dangling(Spec)
    assert not missing, f"Spec 上有 {len(missing)} 个悬空引用 {missing}"


def test_probe_catches_a_planted_dangling_reference() -> None:
    """自检: 造一个悬空引用, 必须被抓出来 —— 免得检查器哪天写崩后永远绿。"""
    class Base:
        def __init__(self) -> None:
            self.real_attr = 1

        def ok(self) -> object:
            return self.real_attr

        def method(self) -> None:
            pass

        def broken(self) -> object:
            return self.gone_away()      # type: ignore[attr-defined] # ← 不存在, 故意植入的悬空引用, 只喂 ast.parse 不执行

    missing = _dangling(Base)
    assert missing == ["gone_away"], f"自检失败, 期望抓到 gone_away, 实际 {missing}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("悬空 self 引用自检过")
