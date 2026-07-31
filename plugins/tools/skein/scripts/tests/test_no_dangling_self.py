"""静态守卫: `self.X` 引用必须真的存在 — 抓「方法搬走了但调用点还在」。

## 为什么需要这条
分包过程中同一类故障出现了两次:

1. `boardsource._run_server` 调 `self._probe_same_project(...)`, 而那个方法早已提成
   `serve.probe_same_project(...)` 模块函数 → `AttributeError: 'Skein' object has no
   attribute '_probe_same_project'`, **只在真起 serve 时才炸**。
2. `uvicorn.run("skein:_serve_app_factory")` 的模块字符串没跟着函数搬家 (另有测试守)。

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
from skeinlib.commands import Skein  # noqa: E402
from skeinlib.spec.facade import Spec  # noqa: E402


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
            return self.gone_away()      # ← 不存在

    missing = _dangling(Base)
    assert missing == ["gone_away"], f"自检失败, 期望抓到 gone_away, 实际 {missing}"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("悬空 self 引用自检过")
