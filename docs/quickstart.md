# Quick Start Guide

## 安装

```bash
pip install ai-code-reviewer
```

## 配置

设置环境变量：

```bash
# OpenAI
export OPENAI_API_KEY="your-api-key"

# 或 Claude
export ANTHROPIC_API_KEY="your-api-key"
```

## 基本使用

### 审查单个文件

```bash
ai-review review src/main.py
```

### 审查 Git 变更

```bash
# 审查当前分支与 main 的差异
ai-review diff

# 审查特定提交范围
ai-review diff --base v1.0.0 --head v2.0.0
```

### 审查 PR

```bash
ai-review pr --repo owner/repo --number 123
```

## 输出格式

支持三种输出格式：

```bash
# Markdown (默认)
ai-review review src/ --format markdown --output report.md

# HTML
ai-review review src/ --format html --output report.html

# JSON
ai-review review src/ --format json --output report.json
```

## CI/CD 集成

详见 [CI/CD 集成指南](ci-cd.md)
