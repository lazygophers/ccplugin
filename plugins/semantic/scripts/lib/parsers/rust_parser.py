#!/usr/bin/env python3
"""
Rust 代码解析器

使用 tree-sitter 进行 AST 解析，提供高准确性的 Rust 代码分析。
"""

from typing import List, Dict, Optional
from .tree_sitter_base import TreeSitterParser


class RustParser(TreeSitterParser):
    """Rust 代码解析器 - 使用 Tree-sitter AST"""

    def __init__(self, language: str = "rust"):
        super().__init__("rust")
        self.language = language

    def _extract_definitions(self, node, code: str, file_path: str, depth: int = 0) -> List[Dict]:
        """提取 Rust 特定的定义"""
        chunks = []

        for child in node.children:
            try:
                # 跳过注释
                if child.type in ["comment", "line_comment", "block_comment"]:
                    continue

                # 函数定义
                if child.type == "function_item":
                    chunk = self._parse_function(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 结构体定义
                elif child.type == "struct_item":
                    chunk = self._parse_struct(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # Trait 定义
                elif child.type == "trait_item":
                    chunk = self._parse_trait(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # Impl 块
                elif child.type == "impl_item":
                    chunk = self._parse_impl(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # Mod 定义
                elif child.type == "mod_item":
                    chunk = self._parse_mod(child, code, file_path)
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

    def _parse_struct(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析结构体定义"""
        try:
            # 获取结构体名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            struct_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            struct_code = "\n".join(lines[start_line : end_line + 1])

            # 检查是否是 pub
            is_pub = False
            for child in node.children:
                if child.type == "pub":
                    is_pub = True

            return {
                "type": "struct",
                "name": struct_name,
                "code": struct_code,
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "file_path": file_path,
                "language": self.language,
                "metadata": {
                    "node_type": node.type,
                    "is_pub": is_pub,
                },
            }
        except Exception:
            return None

    def _parse_trait(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 trait 定义"""
        try:
            # 获取 trait 名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            trait_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            trait_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "trait",
                "name": trait_name,
                "code": trait_code,
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

    def _parse_impl(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 impl 块"""
        try:
            # 获取 type 参数
            type_node = node.child_by_field_name("type")
            if not type_node:
                return None

            impl_type = type_node.text.decode("utf8")

            # 检查是否有 trait
            trait_node = node.child_by_field_name("trait")
            trait_name = ""
            if trait_node:
                trait_name = trait_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            impl_code = "\n".join(lines[start_line : end_line + 1])

            # 生成名称
            if trait_name:
                name = f"impl {trait_name} for {impl_type}"
            else:
                name = f"impl {impl_type}"

            return {
                "type": "impl",
                "name": name,
                "code": impl_code,
                "start_line": start_line + 1,
                "end_line": end_line + 1,
                "file_path": file_path,
                "language": self.language,
                "metadata": {
                    "node_type": node.type,
                    "impl_type": impl_type,
                    "trait": trait_name,
                },
            }
        except Exception:
            return None

    def _parse_mod(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 module 定义"""
        try:
            # 获取 module 名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            mod_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            mod_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "module",
                "name": mod_name,
                "code": mod_code,
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
