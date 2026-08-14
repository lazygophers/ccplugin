from __future__ import annotations

import sys

import conftest
from conftest import SCRIPTS

conftest

HOOK_MODULES = ("permission_denied", "permission_request", "post_tool_use",
                "post_tool_use_failure", "pre_tool_use", "stop", "user_prompt_submit", "agent", "cli", "runner",
                "util")


def test_dispatch_resolves_single_file_functions() -> None:
    sys.path.insert(0, str(SCRIPTS))
    import skeinlib.hooks as hooks
    from skeinlib.hooks.cli import DISPATCH, _resolve
    for name, target in DISPATCH.items():
        function = _resolve(name)
        assert callable(function), f"{name} → {target} 解析出来不可调用: {function!r}"
        module_name, _, function_name = target.partition(":")
        module = __import__(f"skeinlib.hooks.{module_name}", fromlist=[function_name])
        assert function is getattr(module, function_name), f"{name} 没有解析到 skeinlib.hooks.{target}"


def test_legacy_modules_only_reexport_single_file_functions() -> None:
    sys.path.insert(0, str(SCRIPTS))
    import skeinlib.hooks as hooks
    for module_name in HOOK_MODULES:
        module = __import__(f"skeinlib.hooks.{module_name}", fromlist=["*"])
        for name in dir(module):
            if name.startswith("cmd_") or name in {"_run_hooks", "task_phase_hints", "git_root", "load_stdin"}:
                assert callable(getattr(module, name)) or name in {"git_root", "load_stdin"}


if __name__ == "__main__":
    for function_name, function in sorted(globals().items()):
        if function_name.startswith("test_") and callable(function):
            function()
    print("hook 单文件结构自检过")
