"""
Web Server 模块测试
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestFindAvailablePort:
    """测试 find_available_port 函数"""
    
    def test_returns_int(self):
        from web.server import find_available_port
        
        port = find_available_port()
        
        assert isinstance(port, int)
    
    def test_returns_valid_range(self):
        from web.server import find_available_port
        
        port = find_available_port()
        
        assert 8000 <= port <= 9000
    
    def test_returns_different_ports(self):
        from web.server import find_available_port
        
        ports = [find_available_port() for _ in range(5)]
        
        assert len(set(ports)) > 1


class TestCreateApp:
    """测试 create_app 函数"""
    
    def test_create_app_returns_fastapi(self):
        from web.api import create_app
        from fastapi import FastAPI
        
        app = create_app()
        
        assert isinstance(app, FastAPI)
    
    def test_app_has_routes(self):
        from web.api import create_app
        
        app = create_app()
        
        routes = [route.path for route in app.routes]
        
        assert "/" in routes
        assert "/api/memories" in routes
        assert "/api/search" in routes
        assert "/api/stats" in routes
