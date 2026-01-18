#!/usr/bin/env python3
"""
Kotlin 代码解析器

使用 tree-sitter 进行 AST 解析，提供高准确性的 Kotlin 代码分析。
"""

from typing import List, Dict, Optional
from .tree_sitter_base import TreeSitterParser


class KotlinParser(TreeSitterParser):
    """Kotlin 代码解析器 - 使用 Tree-sitter AST"""

    def __init__(self, language: str = "kotlin"):
        super().__init__("kotlin")
        self.language = language

    def _parse_function(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析函数定义 - Kotlin 特有实现"""
        try:
            func_name = None

            # 尝试从 simple_identifier 获取函数名
            for child in node.children:
                if child.type == "simple_identifier":
                    func_name = child.text.decode("utf8")
                    break

            if not func_name:
                return None

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            func_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "function",
                "name": func_name,
                "code": func_code,
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

    def _parse_class(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析类定义 - Kotlin 特有实现"""
        try:
            class_name = None

            # 尝试从 type_identifier 获取类名
            for child in node.children:
                if child.type == "type_identifier":
                    class_name = child.text.decode("utf8")
                    break

            if not class_name:
                return None

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            class_code = "\n".join(lines[start_line : end_line + 1])

            # 检查是否是 data class
            is_data_class = False
            for child in node.children:
                if child.type == "modifiers":
                    for mod in child.children:
                        if mod.type == "class_modifier":
                            for m in mod.children:
                                if m.text.decode("utf8") == "data":
                                    is_data_class = True

            return {
                "type": "data_class" if is_data_class else "class",
                "name": class_name,
                "code": class_code,
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "file_path": file_path,
                "language": self.language,
                "metadata": {
                    "node_type": node.type,
                    "is_data_class": is_data_class,
                },
            }
        except Exception:
            return None

    def _extract_definitions(self, node, code: str, file_path: str, depth: int = 0) -> List[Dict]:
        """提取 Kotlin 特定的定义"""
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

                # 类定义
                elif child.type == "class_declaration":
                    chunk = self._parse_class(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 对象定义
                elif child.type == "object_declaration":
                    chunk = self._parse_object(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 接口定义
                elif child.type == "interface_declaration":
                    chunk = self._parse_interface(child, code, file_path)
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

    def _parse_object(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 object 定义"""
        try:
            obj_name = None

            # 尝试从 simple_identifier 获取对象名
            for child in node.children:
                if child.type == "simple_identifier":
                    obj_name = child.text.decode("utf8")
                    break

            if not obj_name:
                return None

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            obj_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "object",
                "name": obj_name,
                "code": obj_code,
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

    def _parse_interface(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析接口定义 - Kotlin 特有实现"""
        try:
            interface_name = None

            # 尝试从 simple_identifier 获取接口名
            for child in node.children:
                if child.type == "simple_identifier":
                    interface_name = child.text.decode("utf8")
                    break

            if not interface_name:
                return None

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            interface_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "interface",
                "name": interface_name,
                "code": interface_code,
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
