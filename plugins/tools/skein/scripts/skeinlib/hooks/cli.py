from __future__ import annotations

import importlib
import sys
from typing import Callable, cast

from skeinlib.hooks import DISPATCH, _ARGV_DISPATCH


def _resolve(name: str) -> Callable[..., int]:
    module_name, _, function_name = DISPATCH[name].partition(":")
    module = importlib.import_module(f"skeinlib.hooks.{module_name}")
    return cast(Callable[..., int], getattr(module, function_name))


_USAGE = (f"用法: skein-hooks {{{'|'.join(DISPATCH)}}}\n\n"
          "各子命令读 stdin 的 hook JSON, 无命中一律静默 exit 0; "
          f"{'/'.join(sorted(_ARGV_DISPATCH))} 走 --flag argv 不读 stdin。\n"
          "由 plugin.json 的 hook 配置调用, 不需手敲。\n")


def main() -> int:
    # 不上 typer: 这条路径每个 prompt 都跑, 保持 stdlib 零 import 开销 (子命令实现仍走懒加载)。
    if len(sys.argv) >= 2 and sys.argv[1] in ("-h", "--help"):
        sys.stdout.write(_USAGE)
        return 0
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.stderr.write(_USAGE)
        return 2
    name = sys.argv[1]
    function = _resolve(name)
    if name in _ARGV_DISPATCH:
        return function(name.split("-", 1)[1])
    payload = load_stdin()
    if payload is None:
        return 0
    return function(payload)


from skeinlib.hooks.util import load_stdin

__all__ = ["DISPATCH", "_ARGV_DISPATCH", "_resolve", "main"]
