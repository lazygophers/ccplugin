#!/usr/bin/env python3
"""
Java 代码解析器

使用 tree-sitter 进行 AST 解析，提供高准确性的 Java 代码分析。
"""

from typing import List, Dict, Optional
from .tree_sitter_base import TreeSitterParser


class JavaParser(TreeSitterParser):
    """Java 代码解析器 - 使用 Tree-sitter AST"""

    def __init__(self, language: str = "java"):
        super().__init__("java")
        self.language = language

    def _extract_definitions(self, node, code: str, file_path: str, depth: int = 0) -> List[Dict]:
        """提取 Java 特定的定义"""
        chunks = []

        for child in node.children:
            try:
                # 跳过注释
                if child.type in ["comment", "line_comment", "block_comment"]:
                    continue

                # 类定义
                if child.type == "class_declaration":
                    chunk = self._parse_class(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 接口定义
                elif child.type == "interface_declaration":
                    chunk = self._parse_interface(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 枚举定义
                elif child.type == "enum_declaration":
                    chunk = self._parse_enum(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 方法定义
                elif child.type == "method_declaration":
                    chunk = self._parse_function(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 字段声明
                elif child.type == "field_declaration":
                    chunk = self._parse_field(child, code, file_path)
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

            return {
                "type": "class",
                "name": class_name,
                "code": class_code,
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

    def _parse_enum(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析枚举定义"""
        try:
            # 获取枚举名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            enum_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            enum_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "enum",
                "name": enum_name,
                "code": enum_code,
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

    def _parse_field(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析字段定义"""
        try:
            # 获取字段类型
            type_node = node.child_by_field_name("type")
            field_type = type_node.text.decode("utf8") if type_node else "unknown"

            # 获取字段名列表
            declarators = node.children_by_field_name("declarator")
            field_names = []
            for decl in declarators:
                name_node = decl.child_by_field_name("name")
                if name_node:
                    field_names.append(name_node.text.decode("utf8"))

            if not field_names:
                return None

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            field_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "field",
                "name": ", ".join(field_names),
                "code": field_code,
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "file_path": file_path,
                "language": self.language,
                "metadata": {
                    "node_type": node.type,
                    "field_type": field_type,
                },
            }
        except Exception:
            return None
