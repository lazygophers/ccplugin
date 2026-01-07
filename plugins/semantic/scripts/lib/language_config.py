#!/usr/bin/env python3
"""
语言特定配置 - 为不同编程语言提供优化的索引策略

每个语言都有特定的代码结构、命名约定和最佳实践。
此模块提供针对性的分块策略、解析选项和模型推荐。
"""

from typing import Dict, List, Optional, Set


# ========================================
# 语言特定配置
# ========================================

LANGUAGE_CONFIGS: Dict[str, Dict] = {
    # ========================================
    # Python - AST 完整解析
    # ========================================
    "python": {
        "chunk_size": 500,
        "chunk_overlap": 50,
        "description": "Python 代码，支持 AST 解析",
        "features": {
            "functions": True,
            "classes": True,
            "methods": True,
            "decorators": True,
            "type_hints": True,
            "docstrings": True,
            "async_functions": True,
        },
        "parser_type": "ast",
        "recommended_models": {
            "fastembed": "codet5+",          # 代码理解最佳
            "codemodel": "codet5+",
        },
        "indexing_priority": "high",        # 函数/类优先
        "metadata_extraction": {
            "args": True,
            "return_type": True,
            "decorators": True,
            "bases": True,
        },
    },

    # ========================================
    # Golang - 函数/结构体解析
    # ========================================
    "golang": {
        "chunk_size": 400,
        "chunk_overlap": 40,
        "description": "Go 代码，支持函数/接口/结构体解析",
        "features": {
            "functions": True,
            "methods": True,
            "interfaces": True,
            "structs": True,
            "receivers": True,
        },
        "parser_type": "regex",
        "recommended_models": {
            "fastembed": "jina-code",        # Go 代码理解
            "codemodel": "unixcoder",
        },
        "indexing_priority": "high",
        "metadata_extraction": {
            "receivers": True,
            "signature": True,
        },
    },

    # ========================================
    # Rust - 所有权/生命周期/特质解析
    # ========================================
    "rust": {
        "chunk_size": 300,
        "chunk_overlap": 30,
        "description": "Rust 代码，支持函数/结构体/特质/impl解析",
        "features": {
            "functions": True,
            "structs": True,
            "traits": True,
            "impls": True,
            "macros": True,
            "lifetimes": True,
        },
        "parser_type": "regex",               # 使用正则解析（syn 是 Rust 库）
        "recommended_models": {
            "fastembed": "unixcoder",        # Rust 支持好
            "codemodel": "unixcoder",
        },
        "indexing_priority": "high",
        "metadata_extraction": {
            "generics": True,
            "lifetimes": True,
            "traits": True,
            "macros": True,
        },
        "parsing_notes": "使用正则解析（syn 是 Rust 原生库，Python 端回退）",
    },

    # ========================================
    # Flutter/Dart - 类/方法/Widget 解析
    # ========================================
    "flutter": {
        "chunk_size": 450,
        "chunk_overlap": 45,
        "description": "Flutter/Dart 代码，支持 Widget/类/方法解析",
        "features": {
            "widgets": True,
            "classes": True,
            "methods": True,
            "extensions": True,
            "mixins": True,
        },
        "parser_type": "analyzer",            # 使用 Dart analyzer
        "recommended_models": {
            "fastembed": "jina-code",
            "codemodel": "codet5+",
        },
        "indexing_priority": "high",
        "metadata_extraction": {
            "widget_type": True,
            "build_methods": True,
            "state_management": True,
        },
        "parsing_notes": "需要安装 dart 库或使用简单正则解析",
    },

    # ========================================
    # JavaScript/TypeScript - 函数/类/组件解析
    # ========================================
    "javascript": {
        "chunk_size": 400,
        "chunk_overlap": 40,
        "description": "JavaScript 代码，支持多种函数定义模式",
        "features": {
            "functions": True,
            "classes": True,
            "arrow_functions": True,
            "async_functions": True,
        },
        "parser_type": "regex",
        "recommended_models": {
            "fastembed": "jina-code",
            "codemodel": "codet5+",
        },
        "indexing_priority": "medium",
    },

    "typescript": {
        "chunk_size": 400,
        "chunk_overlap": 40,
        "description": "TypeScript 代码，支持类型/接口解析",
        "features": {
            "functions": True,
            "classes": True,
            "interfaces": True,
            "types": True,
            "enums": True,
        },
        "parser_type": "regex",
        "recommended_models": {
            "fastembed": "jina-code",
            "codemodel": "codet5+",
        },
        "indexing_priority": "high",
        "metadata_extraction": {
            "types": True,
            "interfaces": True,
            "generics": True,
        },
    },

    # ========================================
    # Java - 类/接口/注解解析
    # ========================================
    "java": {
        "chunk_size": 450,
        "chunk_overlap": 45,
        "description": "Java 代码，支持类/接口/注解解析",
        "features": {
            "classes": True,
            "interfaces": True,
            "methods": True,
            "annotations": True,
            "enums": True,
        },
        "parser_type": "javaparser",          # 使用 JavaParser
        "recommended_models": {
            "fastembed": "codet5+",
            "codemodel": "codet5+",
        },
        "indexing_priority": "high",
        "metadata_extraction": {
            "annotations": True,
            "generics": True,
            "exceptions": True,
        },
        "parsing_notes": "需要安装 javalang 库：uv pip install javalang",
    },

    # ========================================
    # Kotlin - 类/函数/扩展解析
    # ========================================
    "kotlin": {
        "chunk_size": 420,
        "chunk_overlap": 42,
        "description": "Kotlin 代码，支持类/扩展/协程解析",
        "features": {
            "classes": True,
            "functions": True,
            "extensions": True,
            "coroutines": True,
            "data_classes": True,
        },
        "parser_type": "regex",
        "recommended_models": {
            "fastembed": "codet5+",
            "codemodel": "unixcoder",
        },
        "indexing_priority": "high",
        "metadata_extraction": {
            "extensions": True,
            "coroutines": True,
        },
    },

    # ========================================
    # C/C++ - 函数/类/模板解析
    # ========================================
    "c": {
        "chunk_size": 350,
        "chunk_overlap": 35,
        "description": "C 代码，简单分块",
        "features": {
            "functions": True,
            "structs": True,
        },
        "parser_type": "simple",
        "recommended_models": {
            "fastembed": "unixcoder",
        },
        "indexing_priority": "low",
    },

    "cpp": {
        "chunk_size": 380,
        "chunk_overlap": 38,
        "description": "C++ 代码，支持类/模板解析",
        "features": {
            "functions": True,
            "classes": True,
            "templates": True,
            "namespaces": True,
        },
        "parser_type": "simple",
        "recommended_models": {
            "fastembed": "unixcoder",
        },
        "indexing_priority": "medium",
    },

    "csharp": {
        "chunk_size": 420,
        "chunk_overlap": 42,
        "description": "C# 代码，支持类/接口解析",
        "features": {
            "classes": True,
            "interfaces": True,
            "methods": True,
        },
        "parser_type": "simple",
        "recommended_models": {
            "fastembed": "codet5+",
        },
        "indexing_priority": "medium",
    },

    # ========================================
    # Swift - 类/结构体/协议解析
    # ========================================
    "swift": {
        "chunk_size": 400,
        "chunk_overlap": 40,
        "description": "Swift 代码，支持类/结构体/协议解析",
        "features": {
            "classes": True,
            "structs": True,
            "protocols": True,
            "extensions": True,
        },
        "parser_type": "simple",
        "recommended_models": {
            "fastembed": "codet5+",
        },
        "indexing_priority": "medium",
    },

    # ========================================
    # PHP - 类/函数/命名空间解析
    # ========================================
    "php": {
        "chunk_size": 380,
        "chunk_overlap": 38,
        "description": "PHP 代码，支持类/函数解析",
        "features": {
            "classes": True,
            "functions": True,
            "namespaces": True,
        },
        "parser_type": "simple",
        "recommended_models": {
            "fastembed": "codet5+",
        },
        "indexing_priority": "low",
    },

    # ========================================
    # Ruby - 类/模块/方法解析
    # ========================================
    "ruby": {
        "chunk_size": 350,
        "chunk_overlap": 35,
        "description": "Ruby 代码，支持类/模块解析",
        "features": {
            "classes": True,
            "modules": True,
            "methods": True,
        },
        "parser_type": "simple",
        "recommended_models": {
            "fastembed": "codet5+",
        },
        "indexing_priority": "low",
    },

    # ========================================
    # Bash - 脚本函数解析
    # ========================================
    "bash": {
        "chunk_size": 200,
        "chunk_overlap": 20,
        "description": "Bash 脚本，支持函数解析",
        "features": {
            "functions": True,
        },
        "parser_type": "simple",
        "recommended_models": {
            "fastembed": "multilingual-e5-small",
        },
        "indexing_priority": "low",
    },

    # ========================================
    # Markdown - 文档分块
    # ========================================
    "markdown": {
        "chunk_size": 1000,
        "chunk_overlap": 100,
        "description": "Markdown 文档，按标题分块",
        "features": {
            "headings": True,
            "code_blocks": True,
        },
        "parser_type": "simple",
        "recommended_models": {
            "fastembed": "multilingual-e5-large",
        },
        "indexing_priority": "medium",
        "special_handling": "按 # ## ### 标题分块",
    },

    # ========================================
    # Android (Java/Kotlin)
    # ========================================
    "android": {
        "chunk_size": 450,
        "chunk_overlap": 45,
        "description": "Android 开发 (Java/Kotlin)",
        "features": {
            "activities": True,
            "fragments": True,
            "services": True,
            "adapters": True,
        },
        "parser_type": "multi",              # 多语言混合
        "recommended_models": {
            "fastembed": "codet5+",
        },
        "indexing_priority": "high",
    },
}


# ========================================
# 工具函数
# ========================================

def get_language_config(language: str) -> Dict:
    """获取语言配置"""
    return LANGUAGE_CONFIGS.get(language.lower(), {})


def get_chunk_size(language: str, default: int = 500) -> int:
    """获取语言推荐的分块大小"""
    config = get_language_config(language)
    return config.get("chunk_size", default)


def get_chunk_overlap(language: str, default: int = 50) -> int:
    """获取语言推荐的重叠大小"""
    config = get_language_config(language)
    return config.get("chunk_overlap", default)


def get_recommended_model(language: str, engine: str = "fastembed") -> Optional[str]:
    """获取语言推荐的模型"""
    config = get_language_config(language)
    models = config.get("recommended_models", {})
    return models.get(engine)


def get_parser_type(language: str) -> str:
    """获取语言解析器类型"""
    config = get_language_config(language)
    return config.get("parser_type", "simple")


def get_features(language: str) -> Dict[str, bool]:
    """获取语言支持的特性"""
    config = get_language_config(language)
    return config.get("features", {})


def should_extract_metadata(language: str, key: str) -> bool:
    """检查是否应该提取特定元数据"""
    config = get_language_config(language)
    metadata_config = config.get("metadata_extraction", {})
    return metadata_config.get(key, False)


def get_indexing_priority(language: str) -> str:
    """获取索引优先级"""
    config = get_language_config(language)
    return config.get("indexing_priority", "medium")


def is_high_priority_language(language: str) -> bool:
    """检查是否是高优先级语言（需要完整解析）"""
    return get_indexing_priority(language) == "high"


def get_all_supported_languages() -> List[str]:
    """获取所有支持的语言列表"""
    return list(LANGUAGE_CONFIGS.keys())


def get_languages_by_parser_type(parser_type: str) -> List[str]:
    """根据解析器类型获取语言列表"""
    return [
        lang for lang, config in LANGUAGE_CONFIGS.items()
        if config.get("parser_type") == parser_type
    ]


def get_language_description(language: str) -> str:
    """获取语言描述"""
    config = get_language_config(language)
    return config.get("description", "")


def get_parsing_notes(language: str) -> Optional[str]:
    """获取解析器注意事项"""
    config = get_language_config(language)
    return config.get("parsing_notes")


# ========================================
# 语言扩展名映射（辅助函数）
# ========================================

LANGUAGE_EXTENSIONS: Dict[str, Set[str]] = {
    "python": {".py", ".pyi"},
    "golang": {".go"},
    "rust": {".rs"},
    "flutter": {".dart"},
    "javascript": {".js", ".jsx"},
    "typescript": {".ts", ".tsx"},
    "java": {".java"},
    "kotlin": {".kt", ".kts"},
    "c": {".c", ".h"},
    "cpp": {".cpp", ".cc", ".cxx", ".hpp", ".hxx"},
    "csharp": {".cs"},
    "swift": {".swift"},
    "php": {".php"},
    "ruby": {".rb"},
    "bash": {".sh", ".bash"},
    "markdown": {".md", ".markdown"},
    "android": {".java", ".kt"},  # Android 特殊处理
}


def detect_language_from_extension(extension: str) -> Optional[str]:
    """根据扩展名检测语言"""
    ext = extension.lower()
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if ext in extensions:
            return language
    return None


def get_extensions_for_language(language: str) -> Set[str]:
    """获取语言支持的所有扩展名"""
    return LANGUAGE_EXTENSIONS.get(language.lower(), set())
