#!/usr/bin/env python3
"""
Tree-sitter AST 解析器基类

提供基于 tree-sitter 的通用 AST 解析功能。
"""

from pathlib import Path
from typing import List, Dict, Optional
from .base import CodeParser

try:
    from tree_sitter_language_pack import get_language, get_parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class TreeSitterParser(CodeParser):
    """Tree-sitter AST 解析器基类"""

    # 语言到 tree-sitter 语言 ID 的映射
    LANGUAGE_MAP = {
        "golang": "go",
        "rust": "rust",
        "java": "java",
        "kotlin": "kotlin",
        "dart": "dart",
        "javascript": "javascript",
        "typescript": "typescript",
        "flutter": "dart",
        "c": "c",
        "cpp": "cpp",
        "ruby": "ruby",
        "php": "php",
        "swift": "swift",
        "scala": "scala",
        "lua": "lua",
        "elixir": "elixir",
        "bash": "bash",
        "shell": "bash",
        "powershell": "powershell",
        "cmake": "cmake",
        "make": "make",
        "dockerfile": "dockerfile",
        "sql": "sql",
        "markdown": "markdown",
        "md": "markdown",
    }

    # 节点类型映射（语言特定）
    NODE_TYPE_MAPS = {
        "go": {
            "function": "function_declaration",
            "class": "type_declaration",
            "method": "method_declaration",
        },
        "rust": {
            "function": "function_item",
            "struct": "struct_item",
            "trait": "trait_item",
            "impl": "impl_item",
        },
        "java": {
            "function": "method_declaration",
            "class": "class_declaration",
            "interface": "interface_declaration",
        },
        "kotlin": {
            "function": "function_declaration",
            "class": "class_declaration",
            "object": "object_declaration",
        },
        "dart": {
            "function": "function_declaration",
            "class": "class_definition",
            "method": "method_declaration",
        },
        "javascript": {
            "function": "function_declaration",
            "class": "class_declaration",
            "method": "method_definition",
        },
        "typescript": {
            "function": "function_declaration",
            "class": "class_declaration",
            "method": "method_definition",
            "interface": "interface_declaration",
        },
        "c": {
            "function": "function_definition",
            "struct": "struct_specifier",
            "enum": "enum_specifier",
        },
        "cpp": {
            "function": "function_definition",
            "class": "class_specifier",
            "struct": "struct_specifier",
            "enum": "enum_specifier",
            "namespace": "namespace_definition",
        },
        "ruby": {
            "function": "method",
            "class": "class",
            "module": "module",
        },
        "php": {
            "function": "function_definition",
            "class": "class_declaration",
            "interface": "interface_declaration",
            "trait": "trait_declaration",
        },
        "swift": {
            "function": "function_declaration",
            "class": "class_declaration",
            "struct": "struct_declaration",
            "enum": "enum_declaration",
            "protocol": "protocol_declaration",
            "extension": "extension_declaration",
        },
        "scala": {
            "function": "function_definition",
            "class": "class_definition",
            "object": "object_definition",
            "trait": "trait_definition",
        },
        "lua": {
            "function": "function_declaration",
        },
        "elixir": {
            "function": "anonymous_function",
            "def": "call",
        },
        "bash": {
            "function": "function_definition",
            "alias": "declaration",
        },
        "powershell": {
            "function": "function_statement",
            "class": "class_statement",
        },
        "cmake": {
            "function": "function_call",
            "macro": "function_call",
        },
        "make": {
            "function": "rule",
        },
        "dockerfile": {
            "function": "instruction",
        },
        "sql": {
            "function": "create_function",
            "table": "create_table",
        },
    }

    def __init__(self, language: str):
        super().__init__(language)
        if not TREE_SITTER_AVAILABLE:
            raise ImportError("tree-sitter-language-pack 未安装")

        # 获取 tree-sitter 语言 ID
        self.ts_language_id = self.LANGUAGE_MAP.get(language, language)

        try:
            self.ts_language = get_language(self.ts_language_id)
            self.parser = get_parser(self.ts_language_id)
        except Exception as e:
            raise ValueError(f"不支持的语言 '{language}': {e}")

    def parse_file(self, file_path: Path) -> List[Dict]:
        """解析文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            return self.parse_code(code, str(file_path))
        except Exception as e:
            print(f"警告: 解析 {file_path} 失败: {e}")
            return []

    def parse_code(self, code: str, file_path: str) -> List[Dict]:
        """解析代码"""
        chunks = []

        try:
            # 解析为 AST
            tree = self.parser.parse(bytes(code, "utf8"))

            # 提取函数、类等定义
            chunks = self._extract_definitions(tree.root_node, code, file_path)

        except Exception as e:
            print(f"警告: AST 解析失败: {e}")

        return chunks

    def _extract_definitions(
        self, node, code: str, file_path: str, depth: int = 0
    ) -> List[Dict]:
        """提取所有定义（函数、类等）"""
        chunks = []

        # 获取当前语言的节点类型映射
        node_type_map = self.NODE_TYPE_MAPS.get(
            self.ts_language_id, {}
        )

        # 遍历子节点
        for child in node.children:
            try:
                # 跳过注释和空行
                if child.type in ["comment", "line_comment", "block_comment"]:
                    continue

                # 检查是否是函数定义
                if child.type == node_type_map.get("function"):
                    chunk = self._parse_function(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是类定义
                elif child.type == node_type_map.get("class"):
                    chunk = self._parse_class(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是接口定义
                elif child.type == node_type_map.get("interface"):
                    chunk = self._parse_interface(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 trait 定义（Rust）
                elif child.type == node_type_map.get("trait"):
                    chunk = self._parse_trait(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 impl 块（Rust）
                elif child.type == node_type_map.get("impl"):
                    chunk = self._parse_impl(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 struct 定义（C/C++）
                elif child.type == node_type_map.get("struct"):
                    chunk = self._parse_struct(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 enum 定义（C/C++）
                elif child.type == node_type_map.get("enum"):
                    chunk = self._parse_enum(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 module 定义（Ruby）
                elif child.type == node_type_map.get("module"):
                    chunk = self._parse_module(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 namespace 定义（C++）
                elif child.type == node_type_map.get("namespace"):
                    chunk = self._parse_namespace(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 trait 定义（PHP）
                elif child.type == node_type_map.get("trait"):
                    chunk = self._parse_trait(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 protocol 定义（Swift）
                elif child.type == node_type_map.get("protocol"):
                    chunk = self._parse_protocol(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 extension 定义（Swift）
                elif child.type == node_type_map.get("extension"):
                    chunk = self._parse_extension(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 object 定义（Scala）
                elif child.type == node_type_map.get("object"):
                    chunk = self._parse_object(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 检查是否是 table 定义（SQL）
                elif child.type == node_type_map.get("table"):
                    chunk = self._parse_table(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # 递归处理子节点
                elif child.child_count > 0:
                    chunks.extend(
                        self._extract_definitions(child, code, file_path, depth + 1)
                    )

            except Exception as e:
                # 继续处理其他节点
                pass

        return chunks

    def _find_identifier(self, node) -> Optional[str]:
        """递归查找 identifier 节点并返回其文本"""
        if node.type == "identifier":
            return node.text.decode("utf8")

        for child in node.children:
            result = self._find_identifier(child)
            if result:
                return result

        return None

    def _find_object_reference_name(self, node) -> Optional[str]:
        """从 object_reference 类型的子节点中查找名称"""
        for child in node.children:
            if child.type == "object_reference":
                # object_reference 节点直接包含名称文本
                return child.text.decode("utf8")
        return None

    def _parse_function(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析函数定义"""
        try:
            # 获取函数名
            name_node = node.child_by_field_name("name")
            if not name_node:
                # PowerShell 使用 function_name 字段
                name_node = node.child_by_field_name("function_name")

            if not name_node:
                # 某些语言的函数名在特定类型的子节点中
                for child in node.children:
                    if child.type in ["function_name", "identifier"]:
                        name_node = child
                        break

            if not name_node:
                # 尝试从 declarator 字段获取（C/C++ 特殊处理）
                declarator_node = node.child_by_field_name("declarator")
                if declarator_node:
                    # 查找 identifier 类型的子节点
                    for child in declarator_node.children:
                        if child.type == "identifier" or child.type.endswith("declarator"):
                            # 递归查找 identifier
                            name_text = self._find_identifier(child)
                            if name_text:
                                func_name = name_text
                                break
                    else:
                        # 尝试从 object_reference 子节点获取（SQL 特殊处理）
                        func_name = self._find_object_reference_name(node)
                        if not func_name:
                            return None
                else:
                    # 尝试从 object_reference 子节点获取（SQL 特殊处理）
                    func_name = self._find_object_reference_name(node)
                    if not func_name:
                        return None
            else:
                func_name = name_node.text.decode("utf8")

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

    def _parse_interface(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析接口定义"""
        try:
            # 获取接口名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            interface_name = name_node.text.decode("utf8")

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

    def _parse_trait(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 trait 定义（Rust）"""
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
        """解析 impl 块（Rust）"""
        try:
            # 获取 type 参数
            type_node = node.child_by_field_name("type")
            if not type_node:
                return None

            impl_name = type_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            impl_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "impl",
                "name": f"impl {impl_name}",
                "code": impl_code,
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

    def _parse_struct(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 struct 定义（C/C++）"""
        try:
            # 获取 struct 名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            struct_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            struct_code = "\n".join(lines[start_line : end_line + 1])

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
                },
            }
        except Exception:
            return None

    def _parse_enum(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 enum 定义（C/C++）"""
        try:
            # 获取 enum 名
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

    def _parse_module(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 module 定义（Ruby）"""
        try:
            # 获取 module 名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            module_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            module_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "module",
                "name": module_name,
                "code": module_code,
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

    def _parse_namespace(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 namespace 定义（C++）"""
        try:
            # 获取 namespace 名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            namespace_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            namespace_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "namespace",
                "name": namespace_name,
                "code": namespace_code,
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

    def _parse_protocol(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 protocol 定义（Swift）"""
        try:
            # 获取 protocol 名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            protocol_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            protocol_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "protocol",
                "name": protocol_name,
                "code": protocol_code,
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
        """解析 extension 定义（Swift）"""
        try:
            # 获取扩展的类型名
            type_node = node.child_by_field_name("type")
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

    def _parse_object(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 object 定义（Scala）"""
        try:
            # 获取 object 名
            name_node = node.child_by_field_name("name")
            if not name_node:
                return None

            object_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            object_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "object",
                "name": object_name,
                "code": object_code,
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

    def _parse_table(self, node, code: str, file_path: str) -> Optional[Dict]:
        """解析 table 定义（SQL）"""
        try:
            # 获取 table 名
            name_node = node.child_by_field_name("name")
            if not name_node:
                # 尝试从 object_reference 子节点获取（SQL 特殊处理）
                table_name = self._find_object_reference_name(node)
                if not table_name:
                    return None
            else:
                table_name = name_node.text.decode("utf8")

            # 获取代码范围
            start_line = node.start_point[0]
            end_line = node.end_point[0]
            lines = code.split("\n")
            table_code = "\n".join(lines[start_line : end_line + 1])

            return {
                "type": "table",
                "name": table_name,
                "code": table_code,
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
