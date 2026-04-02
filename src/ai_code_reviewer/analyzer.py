"""AI 分析器模块"""

import os
import json
from typing import Optional
from dataclasses import dataclass, field
from enum import Enum

import httpx
from rich.console import Console

console = Console()


class ReviewSeverity(Enum):
    """问题严重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


@dataclass
class ReviewIssue:
    """代码审查问题"""
    file: str
    line: int
    column: int = 1
    severity: ReviewSeverity = ReviewSeverity.INFO
    rule: str = ""
    message: str = ""
    suggestion: str = ""
    code_snippet: str = ""


@dataclass
class ReviewResult:
    """审查结果"""
    files_reviewed: int = 0
    issues: list[ReviewIssue] = field(default_factory=list)
    summary: str = ""
    score: float = 0.0

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ReviewSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ReviewSeverity.WARNING)


class AIProvider:
    """AI 提供者基类"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

    async def analyze(self, code: str, language: str) -> str:
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI API 提供者"""

    API_URL = "https://api.openai.com/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        super().__init__(api_key or os.environ.get("OPENAI_API_KEY"), model)

    async def analyze(self, code: str, language: str) -> str:
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set. Please set the environment variable.")

        prompt = self._build_prompt(code, language)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    def _build_prompt(self, code: str, language: str) -> str:
        return f"""请审查以下 {language} 代码，从以下方面进行分析：

1. **代码质量** - 命名规范、代码结构、可读性
2. **潜在 Bug** - 逻辑错误、边界条件、异常处理
3. **安全漏洞** - SQL 注入、XSS、敏感信息泄露等
4. **性能问题** - 时间复杂度、内存使用、不必要的操作
5. **最佳实践** - 是否遵循语言/框架的最佳实践

请以 JSON 格式返回结果：
```json
{{
  "issues": [
    {{
      "line": <行号>,
      "severity": "error|warning|info|suggestion",
      "rule": "<规则名称>",
      "message": "<问题描述>",
      "suggestion": "<改进建议>"
    }}
  ],
  "summary": "<整体评价>",
  "score": <0-100的评分>
}}
```

代码：
```{language}
{code}
```"""


class ClaudeProvider(AIProvider):
    """Claude API 提供者"""

    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        super().__init__(api_key or os.environ.get("ANTHROPIC_API_KEY"), model)

    async def analyze(self, code: str, language: str) -> str:
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Please set the environment variable.")

        prompt = self._build_prompt(code, language)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]

    def _build_prompt(self, code: str, language: str) -> str:
        return f"""{SYSTEM_PROMPT}

请审查以下 {language} 代码，以 JSON 格式返回结果。

代码：
```{language}
{code}
```"""


class LocalLLMProvider(AIProvider):
    """本地 LLM 提供者（Ollama 等）"""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "codellama"):
        super().__init__(None, model)
        self.base_url = base_url

    async def analyze(self, code: str, language: str) -> str:
        prompt = f"Review this {language} code and provide feedback:\n\n```{language}\n{code}\n```"

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["response"]


SYSTEM_PROMPT = """你是一位资深的代码审查专家，拥有丰富的软件开发经验。
你的任务是审查代码并提供专业、建设性的反馈。

审查原则：
1. 关注实际问题，避免吹毛求疵
2. 提供具体的改进建议，而不仅仅是指出问题
3. 考虑代码的上下文和业务场景
4. 平衡代码质量和开发效率
5. 对安全问题零容忍"""


def get_provider(model: str, api_key: Optional[str] = None) -> AIProvider:
    """根据模型名称获取对应的 AI 提供者"""
    if model.startswith("gpt") or model.startswith("o1"):
        return OpenAIProvider(api_key, model)
    elif model.startswith("claude"):
        return ClaudeProvider(api_key, model)
    else:
        # 默认使用本地 LLM
        return LocalLLMProvider(model=model)


def parse_review_result(response: str, file_path: str) -> ReviewResult:
    """解析 AI 返回的审查结果"""
    result = ReviewResult()

    # 尝试提取 JSON
    try:
        # 查找 JSON 块
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            json_str = response[json_start:json_end]
            data = json.loads(json_str)

            for issue_data in data.get("issues", []):
                issue = ReviewIssue(
                    file=file_path,
                    line=issue_data.get("line", 1),
                    severity=ReviewSeverity(issue_data.get("severity", "info")),
                    rule=issue_data.get("rule", ""),
                    message=issue_data.get("message", ""),
                    suggestion=issue_data.get("suggestion", ""),
                )
                result.issues.append(issue)

            result.summary = data.get("summary", "")
            result.score = float(data.get("score", 0))
    except (json.JSONDecodeError, ValueError) as e:
        console.print(f"[yellow]Warning: Failed to parse AI response as JSON: {e}[/yellow]")
        # 如果无法解析 JSON，将整个响应作为摘要
        result.summary = response
        result.score = 50.0

    return result
