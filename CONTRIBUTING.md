# 贡献指南

感谢您对 AI Code Reviewer 的兴趣！以下是贡献指南。

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/yourusername/ai-code-reviewer.git
cd ai-code-reviewer

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"
```

## 代码规范

- 使用 [Black](https://black.readthedocs.io/) 格式化代码
- 使用 [Ruff](https://docs.astral.sh/ruff/) 进行代码检查
- 使用 [mypy](https://mypy.readthedocs.io/) 进行类型检查

```bash
# 格式化代码
black src tests

# 运行代码检查
ruff check src tests

# 运行类型检查
mypy src
```

## 提交 PR

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 行为准则

请保持友善和尊重，共同维护良好的开源社区氛围。
