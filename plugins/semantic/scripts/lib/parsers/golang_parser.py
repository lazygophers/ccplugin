#!/usr/bin/env python3
"""
Go 代码解析器

使用 tree-sitter 进行 AST 解析，提供高准确性的 Go 代码分析。
"""

from typing import List, Dict, Optional
from .tree_sitter_base import TreeSitterParser


class GoParser(TreeSitterParser):
    """Go 代码解析器 - 使用 Tree-sitter AST"""

    # Go 特定的节点类型
    NODE_TYPE_MAP = {
        "function": "function_declaration",
        "method": "method_declaration",
        "class": "type_declaration",  # Go 的 struct/类型
        "interface": "interface_type",
    }

    def __init__(self, language: str = "golang"):
        super().__init__("go")
        self.language = language

    def _extract_definitions(self, node, code: str, file_path: str, depth: int = 0) -> List[Dict]:
        """提取 Go 特定的定义"""
        chunks = []

        for child in node.children:
            try:
                # 跳过注释
                if child.type in ["comment", "line_comment", "block_comment"]:
                    continue

                # 函数定义
                if child.type == "function_declaration":
                    chunk = self._parse_function(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 方法定义（receiver）
                elif child.type == "method_declaration":
                    chunk = self._parse_method(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 类型定义（struct 等）
                elif child.type == "type_declaration":
                    chunk = self._parse_type_declaration(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 递归处理
                elif child.child_count > 0:
                    chunks.extend(
                        self._extract_definitions(child, code, file_path, depth + 1)
                    )

            except Exception:
                pass

        return chunks

    def _parse_method(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析方法定义（带 receiver）"""
        try:
            # 获取方法名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            method_name = name_node.text.decode("utf8")

            # 获取 receiver
            receiver_node = node.child_by_field_name("receiver")
            receiver = ""
            if receiver_node:
                receiver = receiver_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            method_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "method",
                "name": method_name,
                "code": method_code,
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "file_path": file_path,
                "language": self.language,
                "metadata": {
                    "receiver": receiver,
                    "node_type": node.type,
                },
            }
        except Exception:
            return None

    def _parse_type_declaration(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析类型声明（struct、interface 等）"""
        try:
            # 获取类型名
            type_node = node.child_by_field_name("name")
            if not type_node:
                return None

            type_name = type_node.text.decode("utf8")

            # 获取类型定义（struct、interface 等）
            type_spec = node.child_by_field_name("type")
            type_kind = "unknown"
            if type_spec:
                type_kind = type_spec.type

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            type_code = "\n".join(lines[start_line : end_line + 1])

            # 确定类型
            chunk_type = "type"
            if type_kind == "struct_type":
                chunk_type = "struct"
            elif type_kind == "interface_type":
                chunk_type = "interface"

            return {
                "type": chunk_type,
                "name": type_name,
                "code": type_code,
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "file_path": file_path,
                "language": self.language,
                "metadata": {
                    "type_kind": type_kind,
                    "node_type": node.type,
                },
            }
        except Exception:
            return None
