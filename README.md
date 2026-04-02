# 🧠 AI Code Reviewer

> 智能代码审查助手 —— 让 AI 成为你的代码审查伙伴

[![Stars](https://img.shields.io/github/stars/yujunqin8/ai-code-reviewer?style=social)](https://github.com/yujunqin8/ai-code-reviewer/stargazers)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/yujunqin8/ai-code-reviewer/CI.svg)](https://github.com/yujunqin8/ai-code-reviewer/actions)

## ✨ 特性

- 🤖 **多模型支持** - 支持 OpenAI GPT-4/GPT-3.5、Claude、本地 LLM (Ollama)
- 📁 **多格式支持** - Python、JavaScript、TypeScript、Go、Rust、Java 等 20+ 语言
- 🎯 **智能分析** - 代码质量、安全漏洞、性能优化建议
- 🔄 **CI/CD 集成** - GitHub Actions、GitLab CI、Jenkins 支持
- 📊 **详细报告** - Markdown/HTML/JSON 多种报告格式
- ⚡ **极速响应** - 增量审查，只分析变更代码
- 🎨 **美观输出** - 彩色终端输出，清晰直观

## 🚀 快速开始

### 安装

```bash
# 从 PyPI 安装
pip install ai-code-reviewer

# 或从源码安装
pip install git+https://github.com/yujunqin8/ai-code-reviewer.git
```

### 基本使用

```bash
# 审查单个文件
ai-review review src/main.py

# 审查目录
ai-review review ./src

# 审查 Git 变更
ai-review diff

# 审查特定分支差异
ai-review diff --base main --head feature-branch

# 审查 GitHub PR
ai-review pr --repo owner/repo --number 123
```

### 输出报告

```bash
# 生成 Markdown 报告
ai-review review ./src --output report.md --format markdown

# 生成 HTML 报告
ai-review review ./src --output report.html --format html

# 生成 JSON 报告（便于程序处理）
ai-review review ./src --output report.json --format json
```

## 🔧 配置

### 环境变量

```bash
# OpenAI API Key
export OPENAI_API_KEY="sk-..."

# Claude API Key
export ANTHROPIC_API_KEY="sk-ant-..."

# GitHub Token (用于 PR 审查)
export GITHUB_TOKEN="ghp_..."
```

### 选择模型

```bash
# 使用 GPT-4 (默认)
ai-review review ./src --model gpt-4

# 使用 GPT-3.5
ai-review review ./src --model gpt-3.5-turbo

# 使用 Claude
ai-review review ./src --model claude-3-5-sonnet-20241022

# 使用本地 LLM (Ollama)
ai-review review ./src --model codellama
```

## 📁 支持的语言

Python, JavaScript, TypeScript, React, Vue, Go, Rust, Java, Kotlin, Swift, C, C++, C#, Ruby, PHP, Scala, HTML, CSS, SQL, Bash 等 20+ 语言。

## 🔌 GitHub Actions 集成

```yaml
# .github/workflows/code-review.yml
name: AI Code Review

on:
  pull_request:
    branches: [main]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install ai-code-reviewer
        run: pip install ai-code-reviewer
      
      - name: Run AI Code Review
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          ai-review diff --base ${{ github.base_ref }} --head ${{ github.head_ref }} \
            --output review-report.md --format markdown
      
      - name: Post review comment
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## AI Code Review Report\n\n' + require('fs').readFileSync('review-report.md', 'utf8')
            })
```

## 📖 文档

- [快速开始指南](docs/quickstart.md)
- [配置说明](docs/configuration.md)
- [CI/CD 集成](docs/ci-cd.md)
- [API 参考](docs/api.md)
- [贡献指南](CONTRIBUTING.md)

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=yujunqin8/ai-code-reviewer&type=Date)](https://star-history.com/#yujunqin8/ai-code-reviewer&Date)

## 🤝 贡献

欢迎提交 Issue 和 PR！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解更多。

## 📄 许可

MIT License - 详见 [LICENSE](LICENSE)

---

⭐ 如果这个项目对你有帮助，请给它一个 Star！
