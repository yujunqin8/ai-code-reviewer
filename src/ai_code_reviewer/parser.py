"""代码解析器模块"""

import os
import ast
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class CodeFile:
    """代码文件"""
    path: str
    language: str
    content: str
    lines: int

    @classmethod
    def from_path(cls, path: str) -> "CodeFile":
        """从文件路径创建 CodeFile"""
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        language = detect_language(path)
        lines = content.count("\n") + 1

        return cls(path=path, language=language, content=content, lines=lines)


# 语言检测映射
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".scala": "scala",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".m": "objective-c",
    ".mm": "objective-cpp",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",
    ".ps1": "powershell",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".less": "less",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".xml": "xml",
    ".md": "markdown",
    ".vue": "vue",
    ".svelte": "svelte",
}


def detect_language(file_path: str) -> str:
    """检测文件语言"""
    ext = Path(file_path).suffix.lower()
    return LANGUAGE_MAP.get(ext, "text")


def collect_files(
    path: str,
    include_patterns: Optional[list[str]] = None,
    exclude_patterns: Optional[list[str]] = None,
) -> list[str]:
    """收集要审查的文件"""
    if include_patterns is None:
        include_patterns = list(LANGUAGE_MAP.keys())

    if exclude_patterns is None:
        exclude_patterns = [
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "dist",
            "build",
            ".idea",
            ".vscode",
            "*.min.js",
            "*.min.css",
            "package-lock.json",
            "poetry.lock",
            "Cargo.lock",
        ]

    files = []
    path_obj = Path(path)

    if path_obj.is_file():
        return [str(path_obj)]

    for root, dirs, filenames in os.walk(path):
        # 过滤排除目录
        dirs[:] = [d for d in dirs if not any(
            pattern in d for pattern in exclude_patterns
            if not pattern.startswith("*")
        )]

        for filename in filenames:
            file_path = Path(root) / filename

            # 检查文件扩展名
            ext = file_path.suffix.lower()
            if ext not in include_patterns:
                continue

            # 检查排除模式
            skip = False
            for pattern in exclude_patterns:
                if pattern.startswith("*") and file_path.name.endswith(pattern[1:]):
                    skip = True
                    break
                elif pattern in str(file_path):
                    skip = True
                    break

            if not skip:
                files.append(str(file_path))

    return files


def parse_python_ast(code: str) -> dict:
    """解析 Python 代码的 AST"""
    try:
        tree = ast.parse(code)
        return {
            "functions": [
                {
                    "name": node.name,
                    "line": node.lineno,
                    "args": [arg.arg for arg in node.args.args],
                    "docstring": ast.get_docstring(node),
                }
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ],
            "classes": [
                {
                    "name": node.name,
                    "line": node.lineno,
                    "bases": [ast.unparse(base) for base in node.bases],
                    "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                }
                for node in ast.walk(tree)
                if isinstance(node, ast.ClassDef)
            ],
            "imports": [
                {
                    "line": node.lineno,
                    "module": node.module,
                    "names": [alias.name for alias in node.names],
                }
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
            ],
        }
    except SyntaxError:
        return {}


def get_code_context(code: str, line: int, context_lines: int = 3) -> str:
    """获取代码上下文"""
    lines = code.split("\n")
    start = max(0, line - context_lines - 1)
    end = min(len(lines), line + context_lines)
    return "\n".join(
        f"{i+1:4d} | {lines[i]}"
        for i in range(start, end)
    )
