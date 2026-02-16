"""
Main CLI 模块测试
"""

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
