#!/usr/bin/env python3
"""
符号索引 - 函数/类/变量名索引

提取代码中的符号信息，支持精确匹配和模糊搜索。
支持增量索引 - 只索引修改过的文件。
"""

import re
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
import json
import hashlib
import os


@dataclass
class Symbol:
    """代码符号"""
    id: str
    name: str
    type: str  # function, class, method, variable
    file_path: str
    line_number: int
    end_line_number: int
    language: str
    signature: str = ""
    docstring: str = ""
    parent: str = ""  # 父类/父函数
    file_hash: str = ""  # 文件哈希，用于增量索引


class SymbolIndex:
    """符号索引 - 使用 SQLite 存储，支持增量索引"""

    def __init__(self, db_path: Path):
        self.db_path = db_path / "symbols.db"
        self.conn = None

    def initialize(self) -> bool:
        """初始化符号索引"""
        try:
            self.conn = sqlite3.connect(str(self.db_path))
            self._create_tables()
            return True
        except Exception as e:
            print(f"错误: 符号索引初始化失败: {e}")
            return False

    def _create_tables(self):
        """创建数据库表"""
        cursor = self.conn.cursor()

        # 符号表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER,
                end_line_number INTEGER,
                language TEXT,
                signature TEXT,
                docstring TEXT,
                parent TEXT,
                file_hash TEXT
            )
        """)

        # 文件追踪表（用于增量索引）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indexed_files (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_name
            ON symbols(name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_type
            ON symbols(type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_language
            ON symbols(language)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_path
            ON symbols(file_path)
        """)

        # 全文搜索表
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts
            USING fts5(name, type, signature, docstring, content=symbols)
        """)

        self.conn.commit()

    def _get_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _is_file_modified(self, file_path: str) -> bool:
        """检查文件是否已修改"""
        cursor = self.conn.cursor()
        current_hash = self._get_file_hash(file_path)

        cursor.execute("""
            SELECT file_hash FROM indexed_files
            WHERE file_path = ?
        """, (file_path,))

        result = cursor.fetchone()
        if not result:
            return True  # 新文件

        return result[0] != current_hash

    def add_symbols(self, symbols: List[Symbol], file_path: Optional[str] = None):
        """添加符号到索引"""
        cursor = self.conn.cursor()

        # 如果提供了文件路径，先删除该文件的旧符号
        if file_path:
            cursor.execute("DELETE FROM symbols WHERE file_path = ?", (file_path,))

        for symbol in symbols:
            # 计算文件哈希
            if not symbol.file_hash and file_path:
                symbol.file_hash = self._get_file_hash(file_path)

            cursor.execute("""
                INSERT OR REPLACE INTO symbols
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol.id,
                symbol.name,
                symbol.type,
                symbol.file_path,
                symbol.line_number,
                symbol.end_line_number,
                symbol.language,
                symbol.signature,
                symbol.docstring,
                symbol.parent,
                symbol.file_hash,
            ))

        # 更新文件追踪
        if file_path:
            file_hash = self._get_file_hash(file_path)
            cursor.execute("""
                INSERT OR REPLACE INTO indexed_files
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (file_path, file_hash))

        self.conn.commit()

    def update_file_symbols(self, file_path: str, symbols: List[Symbol]):
        """更新单个文件的符号（增量索引）"""
        if not self._is_file_modified(file_path):
            return  # 文件未修改，跳过

        self.add_symbols(symbols, file_path)

    def get_modified_files(self, file_paths: List[str]) -> List[str]:
        """获取已修改的文件列表"""
        modified = []
        for file_path in file_paths:
            if self._is_file_modified(file_path):
                modified.append(file_path)
        return modified

    def search_by_name(self, name: str, limit: int = 20) -> List[Dict]:
        """按名称搜索符号"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM symbols
            WHERE name LIKE ?
            ORDER BY
                CASE WHEN name = ? THEN 0 ELSE 1 END,
                length(name) ASC
            LIMIT ?
        """, (f"%{name}%", name, limit))

        columns = [
            "id", "name", "type", "file_path", "line_number",
            "end_line_number", "language", "signature", "docstring", "parent", "file_hash"
        ]

        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

    def search_by_type(self, symbol_type: str, limit: int = 20) -> List[Dict]:
        """按类型搜索符号"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM symbols
            WHERE type = ?
            LIMIT ?
        """, (symbol_type, limit))

        columns = [
            "id", "name", "type", "file_path", "line_number",
            "end_line_number", "language", "signature", "docstring", "parent", "file_hash"
        ]

        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

    def search_fulltext(self, query: str, limit: int = 20) -> List[Dict]:
        """全文搜索"""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT s.* FROM symbols s
            INNER JOIN symbols_fts fts ON s.id = fts.rowid
            WHERE symbols_fts MATCH ?
            LIMIT ?
        """, (query, limit))

        columns = [
            "id", "name", "type", "file_path", "line_number",
            "end_line_number", "language", "signature", "docstring", "parent", "file_hash"
        ]

        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))

        return results

    def get_stats(self) -> Dict:
        """获取索引统计"""
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM symbols")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT type, COUNT(*) as count FROM symbols GROUP BY type")
        by_type = dict(cursor.fetchall())

        cursor.execute("SELECT language, COUNT(*) as count FROM symbols GROUP BY language")
        by_language = dict(cursor.fetchall())

        cursor.execute("SELECT COUNT(*) FROM indexed_files")
        indexed_files = cursor.fetchone()[0]

        return {
            "total_symbols": total,
            "by_type": by_type,
            "by_language": by_language,
            "indexed_files": indexed_files,
        }

    def clear(self):
        """清空索引"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM symbols")
        cursor.execute("DELETE FROM indexed_files")
        self.conn.commit()

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()


class SymbolExtractor:
    """符号提取器 - 从代码中提取符号"""

    # Python 模式
    PYTHON_PATTERNS = {
        "function": r"^\s*(async\s+)?def\s+(\w+)\s*\((.*?)\)\s*(?:->\s*([^:]+))?\s*:",
        "class": r"^\s*class\s+(\w+)\s*(?:\((.*?)\))?\s*:",
        "method": r"^\s*(async\s+)?def\s+(\w+)\s*\(",
        "variable": r"^(\w+)\s*=\s*",
    }

    # Go 模式
    GO_PATTERNS = {
        "function": r"^\s*func\s+(?:\(\s*\w+\s+\*?\w+\s*\)\s*)?(\w+)\s*\((.*?)\)",
        "interface": r"^\s*type\s+(\w+)\s+interface",
        "struct": r"^\s*type\s+(\w+)\s+struct",
    }

    # JavaScript/TypeScript 模式
    JS_PATTERNS = {
        "function": r"(?:function\s+(\w+)\s*\(|const\s+(\w+)\s*=\s*(?:async\s+)?\(|(\w+)\s*(?::.*?)?\s*=\s*(?:async\s+)?\((?!.*=>))",
        "class": r"class\s+(\w+)",
        "method": r"(\w+)\s*(?::[^=]+)?\s*=\s*(?:\([^)]*\)\s*=>|function\s*\()",
    }

    @classmethod
    def extract_from_file(cls, file_path: Path) -> List[Symbol]:
        """从文件中提取符号"""
        language = cls._detect_language(file_path)
        if not language:
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return []

        patterns = cls._get_patterns(language)
        symbols = []

        for line_number, line in enumerate(content.split("\n"), 1):
            for symbol_type, pattern in patterns.items():
                matches = re.finditer(pattern, line)
                for match in matches:
                    symbol = cls._create_symbol(
                        file_path, line_number, symbol_type, match, language, line
                    )
                    if symbol:
                        symbols.append(symbol)

        return symbols

    @classmethod
    def _detect_language(cls, file_path: Path) -> Optional[str]:
        """检测文件语言"""
        ext = file_path.suffix
        mapping = {
            ".py": "python",
            ".go": "go",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".kt": "kotlin",
            ".rs": "rust",
            ".cpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".c": "c",
            ".h": "c",
            ".hpp": "cpp",
        }
        return mapping.get(ext)

    @classmethod
    def _get_patterns(cls, language: str) -> Dict[str, str]:
        """获取语言的模式"""
        if language == "python":
            return cls.PYTHON_PATTERNS
        elif language == "go":
            return cls.GO_PATTERNS
        elif language in ["javascript", "typescript"]:
            return cls.JS_PATTERNS
        return {}

    @classmethod
    def _create_symbol(
        cls,
        file_path: Path,
        line_number: int,
        symbol_type: str,
        match: re.Match,
        language: str,
        line: str,
    ) -> Optional[Symbol]:
        """创建符号对象"""
        # 提取名称
        name = None
        for group in match.groups():
            if group and group.strip():
                name = group.strip()
                break

        if not name:
            return None

        # 生成 ID
        symbol_id = f"{file_path}:{line_number}:{symbol_type}:{name}"

        return Symbol(
            id=symbol_id,
            name=name,
            type=symbol_type,
            file_path=str(file_path),
            line_number=line_number,
            end_line_number=line_number,  # TODO: 分析块结束位置
            language=language,
            signature=line.strip(),
        )
