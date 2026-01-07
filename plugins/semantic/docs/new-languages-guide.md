# 新增编程语言支持指南

本文档说明如何为 Semantic 插件添加新的编程语言支持。

## 概述

Semantic 插件使用 **AST（抽象语法树）** 进行代码解析，确保 100% 的准确性。所有语言解析器都基于 `tree-sitter` 或 Python 标准库 `ast` 模块。

**核心原则**：
- ✅ 必须使用 AST 解析
- ❌ 禁止使用正则表达式
- ❌ 禁止使用块匹配

## 当前支持的语言

### 已实现语言（12 种）

| 语言 | AST 引擎 | 解析器类型 | 支持的定义类型 |
|------|---------|-----------|---------------|
| Python | `ast` 标准库 | PythonParser | class, function, async_function |
| Go | tree-sitter | GoParser | function, method, interface |
| Rust | tree-sitter | RustParser | function, struct, trait, impl, module |
| Java | tree-sitter | JavaParser | class, interface, enum, field, method |
| Kotlin | tree-sitter | KotlinParser | class, function, object, data_class |
| JavaScript | tree-sitter | TreeSitterParser | class, function, arrow_function |
| TypeScript | tree-sitter | TreeSitterParser | class, interface, function, type_alias |
| Dart/Flutter | tree-sitter | DartParser | class, function, method, mixin, extension |
| C | tree-sitter | TreeSitterParser | function, struct, enum |
| C++ | tree-sitter | TreeSitterParser | class, struct, function, enum, namespace |
| Ruby | tree-sitter | TreeSitterParser | class, function, module |
| PHP | tree-sitter | TreeSitterParser | class, interface, function, trait |

### 预留支持（4 种）

| 语言 | 状态 | 说明 |
|------|------|------|
| C# | 已安装 | 需单独配置 `tree-sitter-c-sharp` |
| Swift | 已支持 | 使用 tree-sitter-language-pack |
| Scala | 已支持 | 使用 tree-sitter-language-pack |
| Lua | 已支持 | 使用 tree-sitter-language-pack |

## 添加新语言的步骤

### 步骤 1: 验证 tree-sitter 支持

首先检查 `tree-sitter-language-pack` 是否支持该语言：

```python
from tree_sitter_language_pack import get_language, get_parser

# 测试语言支持
try:
    parser = get_parser("language_id")
    print("✓ 语言支持可用")
except Exception as e:
    print("✗ 语言不支持")
```

### 步骤 2: 确定节点类型

使用 [tree-sitter 官方文档](https://tree-sitter.github.io/tree-sitter/playing-with-parsers) 查看该语言的 AST 节点类型。

常用节点类型示例：
- 函数: `function_declaration`, `function_definition`, `function_item`
- 类: `class_declaration`, `class_definition`, `class_specifier`
- 接口: `interface_declaration`
- 结构体: `struct_specifier`, `struct_item`
- 枚举: `enum_specifier`, `enum_declaration`

### 步骤 3: 更新 `tree_sitter_base.py`

在 `lib/parsers/tree_sitter_base.py` 中添加语言映射：

```python
# 1. 在 LANGUAGE_MAP 中添加
LANGUAGE_MAP = {
    # ... 现有语言
    "newlang": "newlang",
}

# 2. 在 NODE_TYPE_MAPS 中添加节点类型映射
NODE_TYPE_MAPS = {
    # ... 现有语言
    "newlang": {
        "function": "function_declaration",
        "class": "class_declaration",
        "interface": "interface_declaration",
    },
}
```

### 步骤 4: 添加解析方法（如需要）

如果该语言有特殊的定义类型（如 Rust 的 impl、Go 的 receiver），在 `tree_sitter_base.py` 中添加对应的解析方法：

```python
def _parse_special_type(self, node, code: str, file_path: str) -> Optional[Dict]:
    """解析特殊定义类型"""
    try:
        # 获取名称
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = name_node.text.decode("utf8")

        # 获取代码范围
        start_line = node.start_point[0]
        end_line = node.end_point[0]
        lines = code.split("\n")
        code_snippet = "\n".join(lines[start_line : end_line + 1])

        return {
            "type": "special_type",
            "name": name,
            "code": code_snippet,
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
```

### 步骤 5: 更新 `_extract_definitions` 方法

在 `_extract_definitions` 方法中添加对新节点类型的处理：

```python
# 检查是否是特殊定义
elif child.type == node_type_map.get("special_type"):
    chunk = self._parse_special_type(child, code, file_path)
    if chunk:
        chunks.append(chunk)
```

### 步骤 6: 更新 `parsers/__init__.py`

在 `lib/parsers/__init__.py` 中注册新语言：

```python
tree_sitter_languages = [
    # ... 现有语言
    "newlang",
]
```

### 步骤 7: 创建专用解析器（如需要）

如果该语言有特殊需求（如 Kotlin 的 simple_identifier、Go 的 receiver），创建专用解析器：

```python
# lib/parsers/newlang_parser.py

from typing import List, Dict, Optional
from .tree_sitter_base import TreeSitterParser


class NewLangParser(TreeSitterParser):
    """NewLang 代码解析器"""

    def __init__(self, language: str = "newlang"):
        super().__init__("newlang")
        self.language = language

    def _extract_definitions(self, node, code: str, file_path: str, depth: int = 0) -> List[Dict]:
        """提取 NewLang 特定的定义"""
        chunks = []

        for child in node.children:
            try:
                # 语言特定的节点处理
                if child.type == "special_node":
                    chunk = self._parse_special(child, code, file_path)
                    if chunk:
                        chunks.append(chunk)

                # ... 其他节点类型

            except Exception:
                pass

        return chunks
```

然后在 `__init__.py` 中注册：

```python
from .newlang_parser import NewLangParser

def create_parser(language: str) -> CodeParser:
    language_lower = language.lower()

    if language_lower == "newlang":
        return NewLangParser()

    # ... 其他语言
```

### 步骤 8: 创建测试文件

创建测试样本：`scripts/test_samples/test.newlang`

```python
# newlang 测试文件

class Example:
    def method():
        pass

function example():
    return 42
```

### 步骤 9: 运行验证测试

```bash
# 测试新语言
python3 scripts/test_new_languages.py

# 完整验证
python3 scripts/test_all_languages.py
```

## 验证清单

添加新语言后，确保满足以下要求：

- [ ] 使用 AST 解析（tree-sitter 或 ast）
- [ ] 无正则表达式匹配
- [ ] 无块匹配
- [ ] 提取至少一种定义类型（function/class）
- [ ] 测试文件创建成功
- [ ] 解析器正常工作
- [ ] 完整验证测试通过

## 常见问题

### Q: 如何处理语言的特殊语法？

A: 创建专用解析器类，重写 `_extract_definitions` 方法。参考 `KotlinParser` 和 `GoParser`。

### Q: 如何调试 AST 节点？

A: 使用以下代码打印 AST 结构：

```python
from tree_sitter_language_pack import get_language, get_parser

parser = get_parser("language_id")
tree = parser.parse(code_bytes)

def print_tree(node, indent=0):
    print("  " * indent + node.type)
    for child in node.children:
        print_tree(child, indent + 1)

print_tree(tree.root_node)
```

### Q: tree-sitter-language-pack 不支持的语言怎么办？

A: 可以：
1. 安装单独的 tree-sitter 语言包（如 `tree-sitter-c-sharp`）
2. 手动编译 tree-sitter 语法
3. 使用其他 AST 解析库

### Q: 如何测试解析器准确性？

A:
1. 查看测试样本是否正确提取定义
2. 检查代码行号是否准确
3. 验证定义类型是否正确
4. 运行 `test_all_languages.py` 查看覆盖率

## 参考资源

- [tree-sitter 官方文档](https://tree-sitter.github.io/tree-sitter/)
- [tree-sitter-language-pack](https://github.com/grantjenks/tree-sitter-language-pack)
- [tree-sitter 在线演练](https://tree-sitter.github.io/tree-sitter/playing-with-parsers)
- [项目代码](https://github.com/your-repo/semantic-plugin)

## 更新日志

### 2025-01-07
- ✅ 添加 C 语言支持（function, struct, enum）
- ✅ 添加 C++ 语言支持（class, struct, namespace, enum）
- ✅ 添加 Ruby 语言支持（class, function, module）
- ✅ 添加 PHP 语言支持（class, interface, function, trait）
- ✅ 更新所有解析器使用 AST
- ✅ 验证 12 种语言 100% AST 覆盖
