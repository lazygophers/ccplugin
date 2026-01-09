#!/usr/bin/env python3
"""
符号提取器 - 从代码中提取函数、类等符号信息

支持多种编程语言的符号提取，用于构建符号级索引。
"""

import re
from typing import List, Dict, Optional, Tuple
from enum import Enum


class SymbolType(Enum):
    """符号类型"""
    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"
    INTERFACE = "interface"
    ENUM = "enum"
    STRUCT = "struct"
    TRAIT = "trait"


class SymbolExtractor:
    """符号提取器基类"""

    def extract_symbols(self, code: str, language: str) -> List[Dict]:
        """提取代码中的符号"""
        extractor_class = self._get_extractor(language)
        if not extractor_class:
            return []

        extractor = extractor_class()
        return extractor.extract(code)

    def _get_extractor(self, language: str):
        """根据语言获取提取器"""
        extractors = {
            "python": PythonSymbolExtractor,
            "javascript": JavaScriptSymbolExtractor,
            "typescript": JavaScriptSymbolExtractor,
            "go": GoSymbolExtractor,
            "rust": RustSymbolExtractor,
            "java": JavaSymbolExtractor,
            "cpp": CppSymbolExtractor,
        }
        return extractors.get(language.lower())


class BaseLanguageExtractor:
    """语言提取器基类"""

    def extract(self, code: str) -> List[Dict]:
        """提取符号，返回符号列表"""
        raise NotImplementedError

    def _extract_imports(self, code: str) -> List[str]:
        """提取导入语句"""
        raise NotImplementedError

    def _extract_functions(self, code: str) -> List[Dict]:
        """提取函数定义"""
        raise NotImplementedError

    def _extract_classes(self, code: str) -> List[Dict]:
        """提取类定义"""
        raise NotImplementedError


class PythonSymbolExtractor(BaseLanguageExtractor):
    """Python 符号提取器"""

    def extract(self, code: str) -> List[Dict]:
        """提取 Python 代码中的符号"""
        symbols = []

        # 提取导入
        symbols.extend(self._extract_imports(code))

        # 提取类
        symbols.extend(self._extract_classes(code))

        # 提取函数
        symbols.extend(self._extract_functions(code))

        # 提取常量（全大写变量）
        symbols.extend(self._extract_constants(code))

        return symbols

    def _extract_imports(self, code: str) -> List[str]:
        """提取 Python 导入语句"""
        imports = []
        patterns = [
            r"^import\s+([\w.]+)",
            r"^from\s+([\w.]+)\s+import",
        ]

        for line in code.split('\n'):
            line = line.strip()
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    imports.append(match.group(1))

        return imports

    def _extract_functions(self, code: str) -> List[Dict]:
        """提取 Python 函数定义"""
        functions = []
        # 匹配函数定义：def function_name(...):
        pattern = r"^def\s+(\w+)\s*\((.*?)\):"

        for i, line in enumerate(code.split('\n')):
            match = re.match(pattern, line)
            if match:
                func_name = match.group(1)
                params = match.group(2)

                functions.append({
                    "type": SymbolType.FUNCTION.value,
                    "name": func_name,
                    "params": params,
                    "line": i + 1,
                })

        return functions

    def _extract_classes(self, code: str) -> List[Dict]:
        """提取 Python 类定义"""
        classes = []
        # 匹配类定义：class ClassName(...):
        pattern = r"^class\s+(\w+)(?:\((.*?)\))?:"

        for i, line in enumerate(code.split('\n')):
            match = re.match(pattern, line)
            if match:
                class_name = match.group(1)
                bases = match.group(2) or ""

                classes.append({
                    "type": SymbolType.CLASS.value,
                    "name": class_name,
                    "bases": bases,
                    "line": i + 1,
                })

        return classes

    def _extract_constants(self, code: str) -> List[Dict]:
        """提取 Python 常量（全大写）"""
        constants = []
        # 匹配全大写变量赋值
        pattern = r"^([A-Z_][A-Z0-9_]*)\s*="

        for i, line in enumerate(code.split('\n')):
            match = re.match(pattern, line)
            if match:
                const_name = match.group(1)
                constants.append({
                    "type": SymbolType.CONSTANT.value,
                    "name": const_name,
                    "line": i + 1,
                })

        return constants


class JavaScriptSymbolExtractor(BaseLanguageExtractor):
    """JavaScript/TypeScript 符号提取器"""

    def extract(self, code: str) -> List[Dict]:
        """提取 JavaScript 代码中的符号"""
        symbols = []

        # 提取导入
        symbols.extend(self._extract_imports(code))

        # 提取类
        symbols.extend(self._extract_classes(code))

        # 提取函数
        symbols.extend(self._extract_functions(code))

        # 提取接口（TypeScript）
        symbols.extend(self._extract_interfaces(code))

        return symbols

    def _extract_imports(self, code: str) -> List[str]:
        """提取 JavaScript 导入语句"""
        imports = []
        patterns = [
            r"import\s+(?:.*?)\s+from\s+['\"]([^'\"]+)['\"]",
            r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, code):
                imports.append(match.group(1))

        return imports

    def _extract_functions(self, code: str) -> List[Dict]:
        """提取 JavaScript 函数定义"""
        functions = []
        patterns = [
            r"(?:async\s+)?function\s+(\w+)\s*\((.*?)\)",
            r"(?:async\s+)?(\w+)\s*:\s*(?:async\s+)?\((.*?)\)\s*=>",
            r"(?:async\s+)?(\w+)\s*\((.*?)\)\s*\{",
        ]

        for i, line in enumerate(code.split('\n')):
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    func_name = match.group(1)
                    params = match.group(2)

                    functions.append({
                        "type": SymbolType.FUNCTION.value,
                        "name": func_name,
                        "params": params,
                        "line": i + 1,
                    })
                    break

        return functions

    def _extract_classes(self, code: str) -> List[Dict]:
        """提取 JavaScript 类定义"""
        classes = []
        # 匹配类定义：class ClassName { ... }
        pattern = r"class\s+(\w+)(?:\s+extends\s+(\w+))?"

        for i, line in enumerate(code.split('\n')):
            match = re.search(pattern, line)
            if match:
                class_name = match.group(1)
                extends = match.group(2)

                classes.append({
                    "type": SymbolType.CLASS.value,
                    "name": class_name,
                    "extends": extends,
                    "line": i + 1,
                })

        return classes

    def _extract_interfaces(self, code: str) -> List[Dict]:
        """提取 TypeScript 接口定义"""
        interfaces = []
        # 匹配接口定义：interface InterfaceName { ... }
        pattern = r"interface\s+(\w+)"

        for i, line in enumerate(code.split('\n')):
            match = re.search(pattern, line)
            if match:
                interface_name = match.group(1)

                interfaces.append({
                    "type": SymbolType.INTERFACE.value,
                    "name": interface_name,
                    "line": i + 1,
                })

        return interfaces


class GoSymbolExtractor(BaseLanguageExtractor):
    """Go 符号提取器"""

    def extract(self, code: str) -> List[Dict]:
        """提取 Go 代码中的符号"""
        symbols = []

        # 提取包
        symbols.extend(self._extract_packages(code))

        # 提取导入
        symbols.extend(self._extract_imports(code))

        # 提取函数
        symbols.extend(self._extract_functions(code))

        # 提取类型/结构体
        symbols.extend(self._extract_types(code))

        return symbols

    def _extract_packages(self, code: str) -> List[Dict]:
        """提取 Go 包定义"""
        packages = []
        pattern = r"^package\s+(\w+)"

        for i, line in enumerate(code.split('\n')):
            match = re.match(pattern, line)
            if match:
                packages.append({
                    "type": "package",
                    "name": match.group(1),
                    "line": i + 1,
                })

        return packages

    def _extract_imports(self, code: str) -> List[str]:
        """提取 Go 导入语句"""
        imports = []
        pattern = r"import\s+(?:\"([^\"]+)\"|(?:\((?:[^)]*)\)))"

        for match in re.finditer(pattern, code):
            if match.group(1):
                imports.append(match.group(1))

        return imports

    def _extract_functions(self, code: str) -> List[Dict]:
        """提取 Go 函数定义"""
        functions = []
        # 匹配函数定义：func FunctionName(...) { ... }
        pattern = r"func\s+(?:\(.*?\)\s+)?(\w+)\s*\((.*?)\)"

        for i, line in enumerate(code.split('\n')):
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                params = match.group(2)

                functions.append({
                    "type": SymbolType.FUNCTION.value,
                    "name": func_name,
                    "params": params,
                    "line": i + 1,
                })

        return functions

    def _extract_types(self, code: str) -> List[Dict]:
        """提取 Go 类型/结构体定义"""
        types = []
        pattern = r"type\s+(\w+)\s+(?:struct|interface)"

        for i, line in enumerate(code.split('\n')):
            match = re.search(pattern, line)
            if match:
                type_name = match.group(1)
                symbol_type = SymbolType.STRUCT.value if "struct" in line else SymbolType.INTERFACE.value

                types.append({
                    "type": symbol_type,
                    "name": type_name,
                    "line": i + 1,
                })

        return types


class RustSymbolExtractor(BaseLanguageExtractor):
    """Rust 符号提取器"""

    def extract(self, code: str) -> List[Dict]:
        """提取 Rust 代码中的符号"""
        symbols = []

        # 提取导入
        symbols.extend(self._extract_imports(code))

        # 提取函数
        symbols.extend(self._extract_functions(code))

        # 提取结构体/枚举/Trait
        symbols.extend(self._extract_types(code))

        return symbols

    def _extract_imports(self, code: str) -> List[str]:
        """提取 Rust 导入语句"""
        imports = []
        pattern = r"use\s+([\w:]+)"

        for match in re.finditer(pattern, code):
            imports.append(match.group(1))

        return imports

    def _extract_functions(self, code: str) -> List[Dict]:
        """提取 Rust 函数定义"""
        functions = []
        pattern = r"(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*\((.*?)\)"

        for i, line in enumerate(code.split('\n')):
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                params = match.group(2)

                functions.append({
                    "type": SymbolType.FUNCTION.value,
                    "name": func_name,
                    "params": params,
                    "line": i + 1,
                })

        return functions

    def _extract_types(self, code: str) -> List[Dict]:
        """提取 Rust 类型定义"""
        types = []
        patterns = [
            (r"(?:pub\s+)?struct\s+(\w+)", SymbolType.STRUCT.value),
            (r"(?:pub\s+)?enum\s+(\w+)", SymbolType.ENUM.value),
            (r"(?:pub\s+)?trait\s+(\w+)", SymbolType.TRAIT.value),
        ]

        for i, line in enumerate(code.split('\n')):
            for pattern, sym_type in patterns:
                match = re.search(pattern, line)
                if match:
                    type_name = match.group(1)

                    types.append({
                        "type": sym_type,
                        "name": type_name,
                        "line": i + 1,
                    })
                    break

        return types


class JavaSymbolExtractor(BaseLanguageExtractor):
    """Java 符号提取器"""

    def extract(self, code: str) -> List[Dict]:
        """提取 Java 代码中的符号"""
        symbols = []

        # 提取导入
        symbols.extend(self._extract_imports(code))

        # 提取类
        symbols.extend(self._extract_classes(code))

        # 提取接口
        symbols.extend(self._extract_interfaces(code))

        # 提取方法
        symbols.extend(self._extract_methods(code))

        return symbols

    def _extract_imports(self, code: str) -> List[str]:
        """提取 Java 导入语句"""
        imports = []
        pattern = r"import\s+([\w.]+)"

        for match in re.finditer(pattern, code):
            imports.append(match.group(1))

        return imports

    def _extract_classes(self, code: str) -> List[Dict]:
        """提取 Java 类定义"""
        classes = []
        pattern = r"(?:public\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?"

        for i, line in enumerate(code.split('\n')):
            match = re.search(pattern, line)
            if match:
                class_name = match.group(1)
                extends = match.group(2)

                classes.append({
                    "type": SymbolType.CLASS.value,
                    "name": class_name,
                    "extends": extends,
                    "line": i + 1,
                })

        return classes

    def _extract_interfaces(self, code: str) -> List[Dict]:
        """提取 Java 接口定义"""
        interfaces = []
        pattern = r"(?:public\s+)?interface\s+(\w+)"

        for i, line in enumerate(code.split('\n')):
            match = re.search(pattern, line)
            if match:
                interface_name = match.group(1)

                interfaces.append({
                    "type": SymbolType.INTERFACE.value,
                    "name": interface_name,
                    "line": i + 1,
                })

        return interfaces

    def _extract_methods(self, code: str) -> List[Dict]:
        """提取 Java 方法定义"""
        methods = []
        pattern = r"(?:public|private|protected)?\s+(?:static\s+)?(?:\w+)\s+(\w+)\s*\((.*?)\)"

        for i, line in enumerate(code.split('\n')):
            match = re.search(pattern, line)
            if match:
                method_name = match.group(1)
                params = match.group(2)

                methods.append({
                    "type": SymbolType.METHOD.value,
                    "name": method_name,
                    "params": params,
                    "line": i + 1,
                })

        return methods


class CppSymbolExtractor(BaseLanguageExtractor):
    """C++ 符号提取器"""

    def extract(self, code: str) -> List[Dict]:
        """提取 C++ 代码中的符号"""
        symbols = []

        # 提取包含（导入）
        symbols.extend(self._extract_includes(code))

        # 提取类
        symbols.extend(self._extract_classes(code))

        # 提取函数
        symbols.extend(self._extract_functions(code))

        return symbols

    def _extract_includes(self, code: str) -> List[str]:
        """提取 C++ 包含语句"""
        includes = []
        pattern = r"#include\s+[<\"]([^>\"]+)[>\"]"

        for match in re.finditer(pattern, code):
            includes.append(match.group(1))

        return includes

    def _extract_classes(self, code: str) -> List[Dict]:
        """提取 C++ 类定义"""
        classes = []
        pattern = r"(?:class|struct)\s+(\w+)"

        for i, line in enumerate(code.split('\n')):
            match = re.search(pattern, line)
            if match:
                class_name = match.group(1)

                classes.append({
                    "type": SymbolType.CLASS.value,
                    "name": class_name,
                    "line": i + 1,
                })

        return classes

    def _extract_functions(self, code: str) -> List[Dict]:
        """提取 C++ 函数定义"""
        functions = []
        # 简化的函数匹配
        pattern = r"(?:\w+\s+)+(\w+)\s*\((.*?)\)\s*(?:const\s*)?(?:override\s*)?{?"

        for i, line in enumerate(code.split('\n')):
            match = re.search(pattern, line)
            if match:
                func_name = match.group(1)
                params = match.group(2)

                # 排除常见的非函数匹配
                if func_name.lower() not in ["if", "while", "for", "switch"]:
                    functions.append({
                        "type": SymbolType.FUNCTION.value,
                        "name": func_name,
                        "params": params,
                        "line": i + 1,
                    })

        return functions
