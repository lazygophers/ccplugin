"""
Main CLI 模块测试
"""

import builtins
import importlib
import os
import sys

import pytest
from click.testing import CliRunner

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestMainCLI:
    """测试主 CLI"""
    
    def test_main_help(self):
        from main import main
        
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        
        assert result.exit_code == 0
        assert "web" in result.output
        assert "hooks" in result.output
    
    def test_web_help(self):
        from main import main
        
        runner = CliRunner()
        result = runner.invoke(main, ["web", "--help"])
        
        assert result.exit_code == 0
        assert "--port" in result.output
        assert "--no-browser" in result.output
        assert "--reload" in result.output
    
    def test_hooks_help(self):
        from main import main
        
        runner = CliRunner()
        result = runner.invoke(main, ["hooks", "--help"])
        
        assert result.exit_code == 0

    def test_main_import_fallback_to_click_when_rich_click_missing(self, monkeypatch):
        module_name = "main"
        sys.modules.pop(module_name, None)

        original_import = builtins.__import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "rich_click":
                raise ModuleNotFoundError("No module named 'rich_click'")
            return original_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        main_module = importlib.import_module(module_name)

        assert main_module.click.__name__ == "click"
