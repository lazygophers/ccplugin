from __future__ import annotations

import importlib
import sys
from typing import Callable, cast

from skeinlib.hooks import DISPATCH, _ARGV_DISPATCH


def _resolve(name: str) -> Callable[..., int]:
    module_name, _, function_name = DISPATCH[name].partition(":")
    module = importlib.import_module(f"skeinlib.hooks.{module_name}")
    return cast(Callable[..., int], getattr(module, function_name))


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in DISPATCH:
        sys.stderr.write(f"用法: skein-hooks {{{'|'.join(DISPATCH)}}}\n")
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
