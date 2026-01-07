"""语义搜索常量定义"""

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
