"""`Spec` — 把五个 mixin 组装成对外的单一门面。

拆成 mixin 而非自由函数: 这些方法要读同一批实例状态 (`root` 及派生路径), 改成函数就得把它
逐个当参数穿过四十来个调用点。拆文件的目的是让 1000 行的 spec 引擎按职责分开, mixin 做到了。

**依赖契约**: 各 mixin 只依赖 `SpecBase` 提供的 `root` / `layer_dir()` / `_scan_namespaces()`
/ `_rule_files()` / `_rules()` / `_inclusion()` / `_always_files()` / `_mtimes()` / `_age_days()`。
mixin 之间也互相调 (maintain 调 `_degrade_one`、write 调 `_reindex_all`), 全经 `self` 解析,
所以只有装配成本类后才完整 —— 单独 import 某个 mixin 去调它的方法不成立。
"""
from __future__ import annotations

from skeinlib.spec.core import SpecBase
from skeinlib.spec.index import IndexMixin
from skeinlib.spec.inject import InjectMixin
from skeinlib.spec.maintain import MaintainMixin
from skeinlib.spec.write import WriteMixin


class Spec(IndexMixin, InjectMixin, WriteMixin, MaintainMixin, SpecBase):
    """规则记忆库门面 — 子命令实现散在各 mixin, 见本模块 docstring。"""
