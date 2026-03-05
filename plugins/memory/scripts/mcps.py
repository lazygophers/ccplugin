"""
MCP Server for Memory Plugin

提供 MCP 协议接口，让 AI Agent 能直接操作记忆系统。

工具列表:
- read_memory: 读取记忆
- create_memory: 创建记忆
- update_memory: 更新记忆
- delete_memory: 删除记忆
- search_memory: 搜索记忆
- preload_memory: 预加载记忆
- save_session: 保存会话
- list_memories: 列出记忆
- get_memory_stats: 获取统计
- export_memories: 导出记忆
- import_memories: 导入记忆
- add_alias: 添加别名
- get_memory_versions: 获取版本历史
- rollback_memory: 回滚记忆
- diff_versions: 对比版本
- list_rollbacks: 列出可回滚版本
- detect_patterns: 检测操作模式
- detect_conflicts: 检测冲突
- resolve_conflict: 解决冲突
- generate_report: 生成分析报告
- get_recommendations: 获取推荐
"""

import json
import os
import sys
from datetime import datetime
from typing import Any


class DateTimeEncoder(json.JSONEncoder):
	"""自定义 JSON 编码器，处理 datetime 对象。"""
	def default(self, obj):
		if isinstance(obj, datetime):
			return obj.isoformat()
		return super().default(obj)


def json_dumps(obj: Any) -> str:
	"""使用自定义编码器序列化 JSON。"""
	return json.dumps(obj, cls=DateTimeEncoder, ensure_ascii=False, indent=2)

# 设置路径以便导入本地模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))




class MemoryMCPServer:
	"""MCP Server for Memory operations."""
