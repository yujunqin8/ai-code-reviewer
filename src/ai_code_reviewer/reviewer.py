"""代码审查器"""

import asyncio
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from ai_code_reviewer.analyzer import (
    AIProvider,
    OpenAIProvider,
    ClaudeProvider,
    LocalLLMProvider,
    ReviewResult,
    parse_review_result,
)
from ai_code_reviewer.parser import CodeFile, collect_files, detect_language
from ai_code_reviewer.git_analyzer import GitAnalyzer, FileDiff
from ai_code_reviewer.reporter import ReportGenerator, ReportConfig, print_console_report


console = Console()


class CodeReviewer:
    """代码审查器"""

    def __init__(
        self,
        model: str = "gpt-4",
        api_key: Optional[str] = None,
        max_file_size: int = 100 * 1024,  # 100KB
    ):
        self.model = model
        self.provider = self._get_provider(model, api_key)
        self.max_file_size = max_file_size

    def _get_provider(self, model: str, api_key: Optional[str]) -> AIProvider:
        """获取 AI 提供者"""
        if model.startswith("gpt") or model.startswith("o1"):
            return OpenAIProvider(api_key, model)
        elif model.startswith("claude"):
            return ClaudeProvider(api_key, model)
        else:
            return LocalLLMProvider(model=model)

    async def review_file(self, file_path: str) -> ReviewResult:
        """审查单个文件"""
        code_file = CodeFile.from_path(file_path)

        # 检查文件大小
        if len(code_file.content) > self.max_file_size:
            console.print(f"[yellow]Skipping large file: {file_path}[/yellow]")
            return ReviewResult(
                files_reviewed=1,
                summary="File too large to review",
                score=0.0,
            )

        # 调用 AI 分析
        console.print(f"[dim]Analyzing: {file_path}[/dim]")
        response = await self.provider.analyze(code_file.content, code_file.language)

        # 解析结果
        result = parse_review_result(response, file_path)
        result.files_reviewed = 1

        return result

    async def review_directory(
        self,
        directory: str,
        include_patterns: Optional[list[str]] = None,
        exclude_patterns: Optional[list[str]] = None,
    ) -> dict[str, ReviewResult]:
        """审查目录中的所有代码文件"""
        files = collect_files(directory, include_patterns, exclude_patterns)
        results = {}

        console.print(f"[bold]Found {len(files)} files to review[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Reviewing...", total=len(files))

            for file_path in files:
                try:
                    result = await self.review_file(file_path)
                    results[file_path] = result
                except Exception as e:
                    console.print(f"[red]Error reviewing {file_path}: {e}[/red]")
                    results[file_path] = ReviewResult(
                        files_reviewed=1,
                        summary=f"Error: {str(e)}",
                        score=0.0,
                    )

                progress.advance(task)

        return results

    async def review_git_diff(
        self,
        base: str = "main",
        head: str = "HEAD",
        repo_path: str = ".",
    ) -> dict[str, ReviewResult]:
        """审查 Git 差异"""
        analyzer = GitAnalyzer(repo_path)
        diffs = analyzer.get_diff(base, head)
        results = {}

        console.print(f"[bold]Found {len(diffs)} changed files[/bold]")

        for diff in diffs:
            if diff.is_deleted:
                continue

            # 获取新文件路径
            file_path = diff.new_path
            full_path = Path(repo_path) / file_path

            if not full_path.exists():
                continue

            # 只审查变更部分
            changed_content = self._extract_changed_content(diff, full_path)
            if not changed_content.strip():
                continue

            try:
                language = detect_language(file_path)
                response = await self.provider.analyze(changed_content, language)
                result = parse_review_result(response, file_path)
                result.files_reviewed = 1
                results[file_path] = result
            except Exception as e:
                console.print(f"[red]Error reviewing {file_path}: {e}[/red]")

        return results

    def _extract_changed_content(self, diff: FileDiff, file_path: Path) -> str:
        """提取变更内容"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            changed_line_nums = set()
            for hunk in diff.hunks:
                for change in hunk.changes:
                    if change.type == "add" and change.new_line:
                        changed_line_nums.add(change.new_line)

            # 提取变更行及其上下文
            context_lines = 3
            extracted_lines = []
            for i, line in enumerate(lines, 1):
                if any(abs(i - n) <= context_lines for n in changed_line_nums):
                    extracted_lines.append(f"{i:4d} | {line}")

            return "".join(extracted_lines)
        except Exception:
            return ""

    async def review_pr(
        self,
        repo: str,
        number: int,
        github_token: Optional[str] = None,
    ) -> dict[str, ReviewResult]:
        """审查 GitHub PR"""
        from ai_code_reviewer.git_analyzer import GitHubClient

        client = GitHubClient(github_token)

        # 获取 PR 信息
        pr = await client.get_pull_request(repo.split("/")[0], repo.split("/")[1], number)
        diff_text = await client.get_pull_request_diff(repo.split("/")[0], repo.split("/")[1], number)

        # 解析差异
        analyzer = GitAnalyzer()
        diffs = analyzer._parse_diff(diff_text)

        results = {}
        for diff in diffs:
            if diff.is_deleted:
                continue

            file_path = diff.new_path
            changed_content = "\n".join(
                line.content
                for hunk in diff.hunks
                for line in hunk.changes
                if line.type == "add"
            )

            if not changed_content.strip():
                continue

            try:
                language = detect_language(file_path)
                response = await self.provider.analyze(changed_content, language)
                result = parse_review_result(response, file_path)
                result.files_reviewed = 1
                results[file_path] = result
            except Exception as e:
                console.print(f"[red]Error reviewing {file_path}: {e}[/red]")

        return results


async def review_command(
    path: str,
    model: str = "gpt-4",
    output: Optional[str] = None,
    format: str = "markdown",
    api_key: Optional[str] = None,
) -> None:
    """审查命令入口"""
    reviewer = CodeReviewer(model=model, api_key=api_key)

    path_obj = Path(path)
    if path_obj.is_file():
        results = {path: await reviewer.review_file(path)}
    else:
        results = await reviewer.review_directory(path)

    # 打印终端报告
    print_console_report(results)

    # 生成文件报告
    if output:
        config = ReportConfig(output_format=format)
        generator = ReportGenerator(config)
        generator.generate(results, output)


async def diff_command(
    base: str = "main",
    head: str = "HEAD",
    model: str = "gpt-4",
    output: Optional[str] = None,
    format: str = "markdown",
    api_key: Optional[str] = None,
) -> None:
    """差异审查命令入口"""
    reviewer = CodeReviewer(model=model, api_key=api_key)
    results = await reviewer.review_git_diff(base, head)

    # 打印终端报告
    print_console_report(results)

    # 生成文件报告
    if output:
        config = ReportConfig(output_format=format)
        generator = ReportGenerator(config)
        generator.generate(results, output)


async def pr_command(
    repo: str,
    number: int,
    model: str = "gpt-4",
    output: Optional[str] = None,
    format: str = "markdown",
    api_key: Optional[str] = None,
    github_token: Optional[str] = None,
) -> None:
    """PR 审查命令入口"""
    reviewer = CodeReviewer(model=model, api_key=api_key)
    results = await reviewer.review_pr(repo, number, github_token)

    # 打印终端报告
    print_console_report(results)

    # 生成文件报告
    if output:
        config = ReportConfig(output_format=format)
        generator = ReportGenerator(config)
        generator.generate(results, output)
