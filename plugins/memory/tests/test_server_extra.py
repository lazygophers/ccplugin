"""
Web Server 模块补充测试
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestRunWebServer:
    """测试 run_web_server 函数"""
    
    @pytest.mark.asyncio
    async def test_run_web_server_basic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                from web.server import run_web_server
                import web.server as server_module
                
                mock_server = MagicMock()
                mock_server.serve = AsyncMock()
                
                with patch("uvicorn.Config") as mock_config:
                    with patch("uvicorn.Server", return_value=mock_server):
                        with patch("webbrowser.open"):
                            await run_web_server(port=8888, open_browser=True, reload=False)
                            
                            mock_config.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_web_server_no_browser(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                from web.server import run_web_server
                
                mock_server = MagicMock()
                mock_server.serve = AsyncMock()
                
                with patch("uvicorn.Config") as mock_config:
                    with patch("uvicorn.Server", return_value=mock_server):
                        with patch("webbrowser.open") as mock_open:
                            await run_web_server(port=8889, open_browser=False, reload=False)
                            
                            mock_open.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_run_web_server_with_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("memory.database.get_project_plugins_dir", return_value=tmpdir):
                from web.server import run_web_server
                
                mock_server = MagicMock()
                mock_server.serve = AsyncMock()
                
                with patch("uvicorn.Config") as mock_config:
                    with patch("uvicorn.Server", return_value=mock_server):
                        with patch("webbrowser.open"):
                            await run_web_server(port=8890, open_browser=False, reload=True)
                            
                            call_args = mock_config.call_args
                            assert call_args[1]["reload"] is True
                            assert call_args[1]["factory"] is True


class TestStartWeb:
    """测试 start_web 函数"""
    
    def test_start_web_calls_asyncio_run(self):
        from web.server import start_web
        
        with patch("web.server.asyncio.run") as mock_run:
            start_web(port=8891, open_browser=False, reload=False)
            
            mock_run.assert_called_once()
