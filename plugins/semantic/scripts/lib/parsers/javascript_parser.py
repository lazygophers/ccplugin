#!/usr/bin/env python3
"""
JavaScript/TypeScript 代码解析器

使用 tree-sitter 进行 AST 解析，提供高准确性的 JS/TS 代码分析。
"""

from typing import List, Dict, Optional
from .tree_sitter_base import TreeSitterParser


class JavaScriptParser(TreeSitterParser):
    """JavaScript/TypeScript 代码解析器 - 使用 Tree-sitter AST"""

    def __init__(self, language: str = "javascript"):
        # TypeScript 和 JavaScript 使用相同的 parser
        ts_lang = "typescript" if language in ["typescript", "tsx"] else "javascript"
        super().__init__(ts_lang)
        self.language = language

    def _extract_definitions(self, node, code: str, file_path: str, depth: int = 0) -> List[Dict]:
        """提取 JavaScript/TypeScript 特定的定义"""
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

                # 箭头函数（作为变量声明）
                elif child.type == "variable_declaration":
                    chunk = self._parse_arrow_function(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 类定义
                elif child.type == "class_declaration":
                    chunk = self._parse_class(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 接口定义（TypeScript）
                elif child.type == "interface_declaration":
                    chunk = self._parse_interface(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 类型别名（TypeScript）
                elif child.type == "type_alias_declaration":
                    chunk = self._parse_type_alias(child, code, file_path)
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

    def _parse_arrow_function(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析箭头函数"""
        try:
            # 获取变量名
            for declarator in node.children_by_field_name("declarator"):
                # 检查是否是箭头函数
                has_arrow = False
                for child in declarator.children:
                    if child.type == "arrow_function":
                        has_arrow = True
                        break

                if has_arrow:
                    # 获取变量名
                    name_node = declarator.child_by_field_name("name")
                    if name_node:
                        func_name = name_node.text.decode("utf8")

                        # 获取代码范围
                        start_line = node.start_point[0]
                        end_line = node.end_point[0]
                        lines = code.split("\n")
                        func_code = "\n".join(lines[start_line : end_line + 1])

                        return {
                            "type": "arrow_function",
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
            pass

        return None

    def _parse_type_alias(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析类型别名（TypeScript）"""
        try:
            # 获取类型别名名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            alias_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            alias_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "type_alias",
                "name": alias_name,
                "code": alias_code,
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
