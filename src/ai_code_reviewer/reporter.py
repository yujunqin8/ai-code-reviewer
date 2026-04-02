"""报告生成器模块"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from jinja2 import Environment, PackageLoader, select_autoescape
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from ai_code_reviewer.analyzer import ReviewResult, ReviewIssue, ReviewSeverity


console = Console()


@dataclass
class ReportConfig:
    """报告配置"""
    title: str = "AI Code Review Report"
    output_format: str = "markdown"
    show_snippets: bool = True
    max_snippet_lines: int = 10
    group_by_severity: bool = True
    show_summary: bool = True


class ReportGenerator:
    """报告生成器"""

    def __init__(self, config: Optional[ReportConfig] = None):
        self.config = config or ReportConfig()
        self.env = Environment(
            loader=PackageLoader("ai_code_reviewer", "templates"),
            autoescape=select_autoescape(["html"]),
        )

    def generate(
        self,
        results: dict[str, ReviewResult],
        output_path: Optional[str] = None,
    ) -> str:
        """生成报告"""
        if self.config.output_format == "markdown":
            report = self._generate_markdown(results)
        elif self.config.output_format == "html":
            report = self._generate_html(results)
        elif self.config.output_format == "json":
            report = self._generate_json(results)
        else:
            raise ValueError(f"Unsupported format: {self.config.output_format}")

        if output_path:
            Path(output_path).write_text(report, encoding="utf-8")
            console.print(f"[green]Report saved to: {output_path}[/green]")

        return report

    def _generate_markdown(self, results: dict[str, ReviewResult]) -> str:
        """生成 Markdown 报告"""
        lines = [
            f"# {self.config.title}",
            f"\n> Generated: {datetime.now().isoformat()}",
            "",
        ]

        # 总体摘要
        total_issues = sum(len(r.issues) for r in results.values())
        total_errors = sum(r.error_count for r in results.values())
        total_warnings = sum(r.warning_count for r in results.values())
        avg_score = sum(r.score for r in results.values()) / len(results) if results else 0

        lines.extend([
            "## 📊 Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Files Reviewed | {len(results)} |",
            f"| Total Issues | {total_issues} |",
            f"| 🔴 Errors | {total_errors} |",
            f"| 🟡 Warnings | {total_warnings} |",
            f"| 📈 Score | {avg_score:.1f}/100 |",
            "",
        ])

        # 按文件分组的问题列表
        lines.extend(["## 📝 Issues", ""])

        for file_path, result in results.items():
            if not result.issues:
                continue

            lines.extend([
                f"### `{file_path}`",
                "",
                f"Score: **{result.score:.1f}**/100",
                "",
            ])

            # 按严重程度分组
            if self.config.group_by_severity:
                for severity in [ReviewSeverity.ERROR, ReviewSeverity.WARNING, ReviewSeverity.INFO, ReviewSeverity.SUGGESTION]:
                    severity_issues = [i for i in result.issues if i.severity == severity]
                    if not severity_issues:
                        continue

                    icon = self._get_severity_icon(severity)
                    lines.extend([
                        f"#### {icon} {severity.value.upper()}",
                        "",
                    ])

                    for issue in severity_issues:
                        lines.extend([
                            f"- **Line {issue.line}**: {issue.message}",
                            f"  - Rule: `{issue.rule}`",
                            f"  - Suggestion: {issue.suggestion}",
                            "",
                        ])
            else:
                for issue in result.issues:
                    icon = self._get_severity_icon(issue.severity)
                    lines.extend([
                        f"### {icon} Line {issue.line}",
                        "",
                        f"**{issue.message}**",
                        "",
                        f"- Severity: `{issue.severity.value}`",
                        f"- Rule: `{issue.rule}`",
                        f"- Suggestion: {issue.suggestion}",
                        "",
                    ])

            if result.summary:
                lines.extend([
                    "**Summary:**",
                    "",
                    result.summary,
                    "",
                ])

        return "\n".join(lines)

    def _generate_html(self, results: dict[str, ReviewResult]) -> str:
        """生成 HTML 报告"""
        template = self.env.get_template("report.html")
        return template.render(
            title=self.config.title,
            generated=datetime.now().isoformat(),
            results=results,
            config=self.config,
        )

    def _generate_json(self, results: dict[str, ReviewResult]) -> str:
        """生成 JSON 报告"""
        data = {
            "title": self.config.title,
            "generated": datetime.now().isoformat(),
            "summary": {
                "files_reviewed": len(results),
                "total_issues": sum(len(r.issues) for r in results.values()),
                "total_errors": sum(r.error_count for r in results.values()),
                "total_warnings": sum(r.warning_count for r in results.values()),
                "average_score": sum(r.score for r in results.values()) / len(results) if results else 0,
            },
            "files": {
                path: {
                    "score": result.score,
                    "summary": result.summary,
                    "issues": [
                        {
                            "line": issue.line,
                            "column": issue.column,
                            "severity": issue.severity.value,
                            "rule": issue.rule,
                            "message": issue.message,
                            "suggestion": issue.suggestion,
                        }
                        for issue in result.issues
                    ],
                }
                for path, result in results.items()
            },
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _get_severity_icon(self, severity: ReviewSeverity) -> str:
        """获取严重程度图标"""
        icons = {
            ReviewSeverity.ERROR: "🔴",
            ReviewSeverity.WARNING: "🟡",
            ReviewSeverity.INFO: "🔵",
            ReviewSeverity.SUGGESTION: "💡",
        }
        return icons.get(severity, "⚪")


def print_console_report(results: dict[str, ReviewResult]) -> None:
    """在终端打印审查报告"""
    # 打印摘要
    total_issues = sum(len(r.issues) for r in results.values())
    avg_score = sum(r.score for r in results.values()) / len(results) if results else 0

    console.print(Panel(
        f"Files: {len(results)} | Issues: {total_issues} | Score: {avg_score:.1f}/100",
        title="📊 Review Summary",
        border_style="blue",
    ))

    # 打印每个文件的问题
    for file_path, result in results.items():
        console.print(f"\n[bold cyan]📄 {file_path}[/bold cyan]")
        console.print(f"Score: [bold]{result.score:.1f}[/bold]/100")

        if not result.issues:
            console.print("[green]✓ No issues found[/green]")
            continue

        table = Table(show_header=True, header_style="bold")
        table.add_column("Line", justify="right", style="cyan")
        table.add_column("Severity", style="bold")
        table.add_column("Rule", style="magenta")
        table.add_column("Message")

        for issue in result.issues:
            severity_style = {
                ReviewSeverity.ERROR: "red",
                ReviewSeverity.WARNING: "yellow",
                ReviewSeverity.INFO: "blue",
                ReviewSeverity.SUGGESTION: "green",
            }.get(issue.severity, "white")

            table.add_row(
                str(issue.line),
                f"[{severity_style}]{issue.severity.value.upper()}[/{severity_style}]",
                issue.rule,
                issue.message[:50] + ("..." if len(issue.message) > 50 else ""),
            )

        console.print(table)

        if result.summary:
            console.print(f"\n[dim]{result.summary}[/dim]")
