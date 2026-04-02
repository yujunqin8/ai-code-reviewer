"""Git 差异分析模块"""

import os
import re
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

import httpx


@dataclass
class DiffHunk:
    """代码差异块"""
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    content: str
    changes: list["DiffLine"]


@dataclass
class DiffLine:
    """差异行"""
    type: str  # "add", "delete", "context"
    old_line: Optional[int]
    new_line: Optional[int]
    content: str


@dataclass
class FileDiff:
    """文件差异"""
    old_path: str
    new_path: str
    hunks: list[DiffHunk]
    is_new: bool = False
    is_deleted: bool = False
    is_renamed: bool = False


class GitAnalyzer:
    """Git 差异分析器"""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def get_diff(self, base: str = "main", head: str = "HEAD") -> list[FileDiff]:
        """获取两个提交之间的差异"""
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--unified=3", f"{base}...{head}"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"git diff failed: {result.stderr}")

        return self._parse_diff(result.stdout)

    def get_staged_diff(self) -> list[FileDiff]:
        """获取已暂存的差异"""
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--cached", "--unified=3"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"git diff failed: {result.stderr}")

        return self._parse_diff(result.stdout)

    def get_unstaged_diff(self) -> list[FileDiff]:
        """获取未暂存的差异"""
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--unified=3"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"git diff failed: {result.stderr}")

        return self._parse_diff(result.stdout)

    def get_changed_files(self, base: str = "main", head: str = "HEAD") -> list[str]:
        """获取变更的文件列表"""
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{head}"],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(f"git diff failed: {result.stderr}")

        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]

    def _parse_diff(self, diff_text: str) -> list[FileDiff]:
        """解析 git diff 输出"""
        file_diffs = []

        if not diff_text.strip():
            return file_diffs

        # 分割每个文件的差异
        file_pattern = re.compile(r'^diff --git a/(.+?) b/(.+)$', re.MULTILINE)
        file_matches = list(file_pattern.finditer(diff_text))

        for i, match in enumerate(file_matches):
            old_path = match.group(1)
            new_path = match.group(2)

            # 获取该文件的差异文本
            start = match.end()
            end = file_matches[i + 1].start() if i + 1 < len(file_matches) else len(diff_text)
            file_text = diff_text[start:end]

            # 检测文件状态
            is_new = old_path == "/dev/null" or "new file" in file_text
            is_deleted = new_path == "/dev/null" or "deleted file" in file_text
            is_renamed = old_path != new_path and not is_new and not is_deleted

            # 解析 hunk
            hunks = self._parse_hunks(file_text)

            file_diffs.append(FileDiff(
                old_path=old_path,
                new_path=new_path,
                hunks=hunks,
                is_new=is_new,
                is_deleted=is_deleted,
                is_renamed=is_renamed,
            ))

        return file_diffs

    def _parse_hunks(self, file_text: str) -> list[DiffHunk]:
        """解析差异块"""
        hunks = []

        hunk_pattern = re.compile(
            r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@',
            re.MULTILINE
        )

        matches = list(hunk_pattern.finditer(file_text))

        for i, match in enumerate(matches):
            old_start = int(match.group(1))
            old_lines = int(match.group(2) or 1)
            new_start = int(match.group(3))
            new_lines = int(match.group(4) or 1)

            # 获取 hunk 内容
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(file_text)
            content = file_text[start:end].strip()

            # 解析变更行
            changes = self._parse_lines(content, old_start, new_start)

            hunks.append(DiffHunk(
                old_start=old_start,
                old_lines=old_lines,
                new_start=new_start,
                new_lines=new_lines,
                content=content,
                changes=changes,
            ))

        return hunks

    def _parse_lines(self, content: str, old_start: int, new_start: int) -> list[DiffLine]:
        """解析差异行"""
        lines = []
        old_line = old_start
        new_line = new_start

        for line in content.split("\n"):
            if line.startswith("+"):
                lines.append(DiffLine(
                    type="add",
                    old_line=None,
                    new_line=new_line,
                    content=line[1:],
                ))
                new_line += 1
            elif line.startswith("-"):
                lines.append(DiffLine(
                    type="delete",
                    old_line=old_line,
                    new_line=None,
                    content=line[1:],
                ))
                old_line += 1
            elif line.startswith(" "):
                lines.append(DiffLine(
                    type="context",
                    old_line=old_line,
                    new_line=new_line,
                    content=line[1:],
                ))
                old_line += 1
                new_line += 1

        return lines


class GitHubClient:
    """GitHub API 客户端"""

    API_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def get_pull_request(
        self, owner: str, repo: str, number: int
    ) -> dict:
        """获取 PR 信息"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.API_URL}/repos/{owner}/{repo}/pulls/{number}",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_pull_request_files(
        self, owner: str, repo: str, number: int
    ) -> list[dict]:
        """获取 PR 变更文件"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.API_URL}/repos/{owner}/{repo}/pulls/{number}/files",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_pull_request_diff(
        self, owner: str, repo: str, number: int
    ) -> str:
        """获取 PR diff"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.API_URL}/repos/{owner}/{repo}/pulls/{number}",
                headers={**self.headers, "Accept": "application/vnd.github.v3.diff"},
            )
            response.raise_for_status()
            return response.text

    async def create_review_comment(
        self,
        owner: str,
        repo: str,
        number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int,
    ) -> dict:
        """创建 PR 审查评论"""
        if not self.token:
            raise ValueError("GITHUB_TOKEN not set")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.API_URL}/repos/{owner}/{repo}/pulls/{number}/comments",
                headers=self.headers,
                json={
                    "body": body,
                    "commit_id": commit_id,
                    "path": path,
                    "line": line,
                },
            )
            response.raise_for_status()
            return response.json()
