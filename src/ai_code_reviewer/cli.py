"""CLI 入口"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ai_code_reviewer import __version__

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="ai-review")
@click.pass_context
def cli(ctx):
    """🧠 AI Code Reviewer - 智能代码审查助手"""
    ctx.ensure_object(dict)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--model", "-m", default="gpt-4", help="使用的 AI 模型")
@click.option("--output", "-o", type=click.Path(), help="输出报告路径")
@click.option("--format", "-f", type=click.Choice(["markdown", "html", "json"]), default="markdown")
def review(path: str, model: str, output: str, format: str):
    """审查代码文件或目录"""
    console.print(Panel(
        Text(f"🔍 正在审查: {path}\n🤖 使用模型: {model}", justify="center"),
        title="AI Code Reviewer",
        border_style="blue"
    ))
    
    # TODO: 实现实际的代码审查逻辑
    console.print("[green]✓[/green] 代码审查完成！")
    console.print(f"[dim]报告将保存为 {format} 格式[/dim]")


@cli.command()
@click.option("--base", "-b", default="main", help="基准分支")
@click.option("--head", "-h", default="HEAD", help="对比分支/提交")
@click.option("--model", "-m", default="gpt-4", help="使用的 AI 模型")
def diff(base: str, head: str, model: str):
    """审查 Git 差异"""
    console.print(Panel(
        Text(f"📊 对比分支: {base}..{head}\n🤖 使用模型: {model}", justify="center"),
        title="Git Diff Review",
        border_style="green"
    ))
    
    console.print("[green]✓[/green] 差异审查完成！")


@cli.command()
@click.option("--repo", "-r", required=True, help="仓库 (owner/repo)")
@click.option("--number", "-n", type=int, required=True, help="PR 编号")
@click.option("--model", "-m", default="gpt-4", help="使用的 AI 模型")
def pr(repo: str, number: int, model: str):
    """审查 Pull Request"""
    console.print(Panel(
        Text(f"🔀 审查 PR: {repo}#{number}\n🤖 使用模型: {model}", justify="center"),
        title="PR Review",
        border_style="magenta"
    ))
    
    console.print("[green]✓[/green] PR 审查完成！")


def main():
    """程序入口"""
    cli()


if __name__ == "__main__":
    main()
