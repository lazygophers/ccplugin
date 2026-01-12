#!/usr/bin/env python3
"""
Dart/Flutter 代码解析器

使用 tree-sitter 进行 AST 解析，提供高准确性的 Dart 代码分析。
"""

from typing import List, Dict, Optional
from .tree_sitter_base import TreeSitterParser


class DartParser(TreeSitterParser):
    """Dart/Flutter 代码解析器 - 使用 Tree-sitter AST"""

    def __init__(self, language: str = "dart"):
        super().__init__("dart")
        self.language = language

    def _extract_definitions(self, node, code: str, file_path: str, depth: int = 0) -> List[Dict]:
        """提取 Dart/Flutter 特定的定义"""
        chunks = []

        for child in node.children:
            try:
                # 跳过注释
                if child.type in ["comment", "line_comment", "block_comment"]:
                    continue

                # 类定义
                if child.type == "class_definition":
                    chunk = self._parse_class(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 函数定义
                elif child.type == "function_declaration":
                    chunk = self._parse_function(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 方法定义
                elif child.type == "method_declaration":
                    chunk = self._parse_method(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # Mixin 定义
                elif child.type == "mixin_declaration":
                    chunk = self._parse_mixin(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # Extension 定义
                elif child.type == "extension_declaration":
                    chunk = self._parse_extension(child, code, file_path)
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

    def _parse_class(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析类定义"""
        try:
            # 获取类名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            class_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            class_code = "\n".join(lines[start_line : end_line + 1])

            # 检查是否是 Widget
            is_widget = False
            for child in node.children:
                if child.type == "extends_clause":
                    for ext in child.children:
                        if ext.text and b"Widget" in ext.text:
                            is_widget = True
                            break

            chunk_type = "widget" if is_widget else "class"

            return {
                "type": chunk_type,
                "name": class_name,
                "code": class_code,
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "file_path": file_path,
                "language": self.language,
                "metadata": {
                    "node_type": node.type,
                    "is_widget": is_widget,
                },
            }
        except Exception:
            return None

    def _parse_method(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析方法定义"""
        try:
            # 获取方法名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            method_name = name_node.text.decode("utf8")

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
                    "node_type": node.type,
                },
            }
        except Exception:
            return None

    def _parse_mixin(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 mixin 定义"""
        try:
            # 获取 mixin 名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            mixin_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            mixin_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "mixin",
                "name": mixin_name,
                "code": mixin_code,
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "file_path": file_path,
                "language": self.language,
                "metadata": {
                    "node_type": node.type,
                },
            }
        except Exception:
            return None

    def _parse_extension(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 extension 定义"""
        try:
            # 获取扩展的类型名
            type_node = node.child_by_field_name("class_type")
            if not type_node:
                return None

            type_name = type_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            ext_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "extension",
                "name": f"extension {type_name}",
                "code": ext_code,
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "file_path": file_path,
                "language": self.language,
                "metadata": {
                    "node_type": node.type,
                    "type_name": type_name,
                },
            }
        except Exception:
            return None
