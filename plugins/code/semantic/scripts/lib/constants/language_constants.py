"""
Language Constants - 编程语言和文件扩展名映射

这个模块定义了所有支持的编程语言及其对应的文件扩展名。
用于代码解析、语言识别、文件类型判断等场景。

重要：字典顺序很重要！
- 更具体的语言必须在更通用的语言之前定义
- 例如：java 和 kotlin 必须在 android 之前（Android 会复用 java/kotlin 文件）

支持的语言：
- 编译型语言：Java, Kotlin, C, C++, Rust, Go
- 脚本语言：Python, JavaScript, TypeScript, Ruby, PHP, Bash
- 其他语言：Swift, Dart, C#, SQL, Dockerfile
- 标记语言：Markdown

使用示例：
    from lib.constants import SUPPORTED_LANGUAGES

    # 获取Python文件扩展名
    py_extensions = SUPPORTED_LANGUAGES['python']  # ['.py']

    # 查找所有支持的语言
    all_languages = list(SUPPORTED_LANGUAGES.keys())

    # 检查某个文件是否被支持
    def is_supported_file(filename):
        file_ext = '.' + filename.split('.')[-1]
        return any(
            file_ext in exts
            for exts in SUPPORTED_LANGUAGES.values()
        )
"""

# 支持的编程语言及其文件扩展名
# 注意：字典顺序很重要！具体语言必须在通用语言之前定义
# 例如：java 和 kotlin 必须在 android 之前
SUPPORTED_LANGUAGES = {
    "python": [".py"],
    "golang": [".go"],
    "javascript": [".js", ".jsx", ".mjs"],
    "typescript": [".ts", ".tsx"],
    "rust": [".rs"],
    "flutter": [".dart"],
    "java": [".java"],          # 必须在 android 之前
    "kotlin": [".kt", ".kts"],  # 必须在 android 之前
    "android": [".java", ".kt"], # Android 会复用 java/kotlin 文件
    "bash": [".sh", ".bash"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp", ".h"],
    "csharp": [".cs"],
    "swift": [".swift"],
    "php": [".php"],
    "ruby": [".rb"],
    "markdown": [".md"],
    "sql": [".sql"],
    "dockerfile": ["Dockerfile", "dockerfile"],
    "powershell": [".ps1", ".psm1"],
}

__all__ = [
    "SUPPORTED_LANGUAGES",
]
