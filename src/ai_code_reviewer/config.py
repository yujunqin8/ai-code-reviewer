"""配置管理"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import os


class ModelProvider(Enum):
    """AI 模型提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    LOCAL = "local"


@dataclass
class Config:
    """配置类"""
    
    # AI 模型配置
    provider: ModelProvider = ModelProvider.OPENAI
    model: str = "gpt-4"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    
    # 审查配置
    max_tokens: int = 4000
    temperature: float = 0.3
    language: str = "zh-CN"
    
    # 输出配置
    output_format: str = "markdown"
    output_path: Optional[str] = None
    
    # 分析配置
    check_security: bool = True
    check_performance: bool = True
    check_quality: bool = True
    check_style: bool = True
    
    # 忽略规则
    ignore_patterns: list = field(default_factory=lambda: [
        "*.min.js",
        "*.min.css",
        "node_modules/**",
        "venv/**",
        ".venv/**",
        "__pycache__/**",
        "*.pyc",
        "*.pyo",
        "dist/**",
        "build/**",
    ])
    
    def __post_init__(self):
        """从环境变量加载配置"""
        if not self.api_key:
            if self.provider == ModelProvider.OPENAI:
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider == ModelProvider.ANTHROPIC:
                self.api_key = os.getenv("ANTHROPIC_API_KEY")
            elif self.provider == ModelProvider.AZURE:
                self.api_key = os.getenv("AZURE_OPENAI_API_KEY")


# 语言映射
LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".jsx": "JavaScript React",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".scala": "Scala",
    ".vue": "Vue",
    ".svelte": "Svelte",
}

# 审查提示词模板
REVIEW_PROMPT_TEMPLATE = """你是一位资深的代码审查专家。请审查以下 {language} 代码，从以下几个方面进行分析：

## 代码内容
```
{code}
```

## 审查要点

### 1. 安全性问题 (Security)
- SQL 注入、XSS、CSRF 等漏洞
- 敏感信息泄露
- 不安全的依赖使用
- 权限控制问题

### 2. 性能问题 (Performance)
- 时间复杂度过高
- 内存泄漏风险
- 不必要的计算
- I/O 优化建议

### 3. 代码质量 (Quality)
- 可读性
- 可维护性
- 设计模式应用
- 错误处理

### 4. 代码风格 (Style)
- 命名规范
- 注释完整性
- 代码格式
- 最佳实践

## 输出格式

请以 Markdown 格式输出审查报告，包括：
1. **总体评分** (1-10)
2. **问题列表**（按严重程度排序：🔴 严重 🟡 警告 🔵 建议）
3. **修复建议**（包含代码示例）
4. **优点**（值得肯定的地方）

请用{language_name}输出报告。
"""

DIFF_REVIEW_PROMPT_TEMPLATE = """你是一位资深的代码审查专家。请审查以下 Git 变更：

## 变更内容
```diff
{diff}
```

## 文件信息
- 文件: {filename}
- 变更类型: {change_type}

## 审查要点

请重点关注：
1. 新增代码的安全性
2. 变更是否会破坏现有功能
3. 代码质量是否改进
4. 是否有遗漏的边界情况

## 输出格式

请以 Markdown 格式输出：
1. **变更概述**
2. **发现的问题**（🔴 严重 🟡 警告 🔵 建议）
3. **改进建议**
4. **总体评价**

请用{language_name}输出报告。
"""
