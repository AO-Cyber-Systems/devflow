"""AI provider abstraction for DevFlow.

Supports multiple AI backends with graceful fallback:
1. Apple (via Swift bridge) - On-device Foundation Models
2. Ollama - Local LLM server
3. Claude - Anthropic API (optional)
4. OpenAI - OpenAI API (optional)
"""

import asyncio
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any, AsyncIterator

from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


class AIProviderType(str, Enum):
    """Available AI provider types."""

    APPLE = "apple"      # Via Swift bridge (Foundation Models)
    OLLAMA = "ollama"    # Local Ollama server
    CLAUDE = "claude"    # Anthropic API
    OPENAI = "openai"    # OpenAI API


@dataclass
class AIResult:
    """Result from an AI operation."""

    success: bool
    content: str
    provider: str
    model: str | None = None
    usage: dict | None = None
    error: str | None = None


@dataclass
class SummaryResult:
    """Structured result from summarization."""

    title: str | None
    key_points: list[str]
    summary: str


@dataclass
class EntitiesResult:
    """Structured result from entity extraction."""

    apis: list[str]
    components: list[str]
    concepts: list[str]
    suggested_tags: list[str]


@dataclass
class CodeExplanationResult:
    """Structured result from code explanation."""

    summary: str
    algorithm_steps: list[str]
    parameters: dict[str, str]
    returns: str | None
    example: str | None


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass

    @abstractmethod
    async def complete(self, prompt: str, max_tokens: int = 1000) -> AIResult:
        """Generate a completion for the given prompt."""
        pass

    async def summarize(self, content: str, max_length: int = 500) -> SummaryResult:
        """Summarize content.

        Args:
            content: Content to summarize.
            max_length: Maximum summary length.

        Returns:
            SummaryResult with title, key points, and summary.
        """
        prompt = PromptTemplates.format_summarize(content)
        result = await self.complete(prompt, max_tokens=max_length * 2)

        if not result.success:
            return SummaryResult(title=None, key_points=[], summary=content[:max_length])

        return self._parse_summary(result.content)

    async def extract_entities(self, content: str) -> EntitiesResult:
        """Extract entities from content.

        Args:
            content: Content to analyze.

        Returns:
            EntitiesResult with APIs, components, concepts, and tags.
        """
        prompt = PromptTemplates.format_extract_entities(content)
        result = await self.complete(prompt, max_tokens=1000)

        if not result.success:
            return EntitiesResult(apis=[], components=[], concepts=[], suggested_tags=[])

        return self._parse_entities(result.content)

    async def explain_code(
        self,
        code: str,
        language: str,
        detail_level: str = "basic"
    ) -> CodeExplanationResult:
        """Explain code.

        Args:
            code: Code to explain.
            language: Programming language.
            detail_level: One of "brief", "basic", "detailed".

        Returns:
            CodeExplanationResult with explanation.
        """
        prompt = PromptTemplates.format_explain_code(code, language, detail_level)
        max_tokens = {"brief": 200, "basic": 500, "detailed": 1500}.get(detail_level, 500)
        result = await self.complete(prompt, max_tokens=max_tokens)

        if not result.success:
            return CodeExplanationResult(
                summary="Unable to explain code",
                algorithm_steps=[],
                parameters={},
                returns=None,
                example=None
            )

        return self._parse_code_explanation(result.content, detail_level)

    async def generate_tags(self, content: str, max_tags: int = 10) -> list[str]:
        """Generate tags for content.

        Args:
            content: Content to tag.
            max_tags: Maximum number of tags.

        Returns:
            List of generated tags.
        """
        prompt = PromptTemplates.format_generate_tags(content, max_tags)
        result = await self.complete(prompt, max_tokens=200)

        if not result.success:
            return []

        return self._parse_tags(result.content, max_tags)

    async def expand_query(self, query: str, context: str = "") -> str:
        """Expand a search query with related terms.

        Args:
            query: Original query.
            context: Optional context for expansion.

        Returns:
            Expanded query string.
        """
        prompt = PromptTemplates.format_expand_query(query, context)
        result = await self.complete(prompt, max_tokens=200)

        if not result.success:
            return query

        # Clean up the response - just take the first non-empty line
        lines = result.content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith(("EXPANDED", "Query:", "Original")):
                return line

        return query

    async def generate_docstring(self, code: str, language: str) -> str:
        """Generate docstring for code.

        Args:
            code: Code to document.
            language: Programming language.

        Returns:
            Generated docstring.
        """
        prompt = PromptTemplates.format_generate_docstring(code, language)
        result = await self.complete(prompt, max_tokens=500)

        if not result.success:
            return ""

        return result.content.strip()

    async def suggest_improvements(self, code: str, language: str) -> list[str]:
        """Suggest code improvements.

        Args:
            code: Code to analyze.
            language: Programming language.

        Returns:
            List of improvement suggestions.
        """
        prompt = PromptTemplates.format_suggest_improvements(code, language)
        result = await self.complete(prompt, max_tokens=800)

        if not result.success:
            return []

        return self._parse_improvements(result.content)

    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text.

        Args:
            text: Text to translate.
            source_lang: Source language.
            target_lang: Target language.

        Returns:
            Translated text.
        """
        prompt = PromptTemplates.format_translate(text, source_lang, target_lang)
        result = await self.complete(prompt, max_tokens=len(text) * 2)

        if not result.success:
            return text

        return result.content.strip()

    async def detect_language(self, code: str) -> str:
        """Detect programming language of code.

        Args:
            code: Code snippet.

        Returns:
            Detected language name.
        """
        prompt = PromptTemplates.DETECT_LANGUAGE.format(code=code[:2000])
        result = await self.complete(prompt, max_tokens=50)

        if not result.success:
            return "unknown"

        # Take first word/line as the language
        lang = result.content.strip().split()[0].lower()
        # Remove any punctuation
        lang = re.sub(r'[^\w]', '', lang)
        return lang or "unknown"

    # =========================================================================
    # Parsing helpers
    # =========================================================================

    def _parse_summary(self, content: str) -> SummaryResult:
        """Parse summary response into structured result."""
        title = None
        key_points = []
        summary = ""

        lines = content.strip().split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("TITLE:"):
                title = line[6:].strip()
            elif line.startswith("KEY_POINTS:"):
                current_section = "key_points"
            elif line.startswith("SUMMARY:"):
                current_section = "summary"
                summary = line[8:].strip()
            elif current_section == "key_points" and line.startswith("-"):
                key_points.append(line[1:].strip())
            elif current_section == "summary":
                summary += " " + line

        # If parsing failed, use the whole content as summary
        if not summary:
            summary = content.strip()

        return SummaryResult(title=title, key_points=key_points, summary=summary.strip())

    def _parse_entities(self, content: str) -> EntitiesResult:
        """Parse entity extraction response."""
        apis = []
        components = []
        concepts = []
        tags = []

        lines = content.strip().split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("APIS:"):
                current_section = "apis"
                rest = line[5:].strip()
                if rest and rest != "[]":
                    apis.extend(self._parse_list_line(rest))
            elif line.startswith("COMPONENTS:"):
                current_section = "components"
                rest = line[11:].strip()
                if rest and rest != "[]":
                    components.extend(self._parse_list_line(rest))
            elif line.startswith("CONCEPTS:"):
                current_section = "concepts"
                rest = line[9:].strip()
                if rest and rest != "[]":
                    concepts.extend(self._parse_list_line(rest))
            elif line.startswith("SUGGESTED_TAGS:"):
                current_section = "tags"
                rest = line[15:].strip()
                if rest and rest != "[]":
                    tags.extend(self._parse_list_line(rest))
            elif line.startswith("-"):
                item = line[1:].strip()
                if current_section == "apis":
                    apis.append(item)
                elif current_section == "components":
                    components.append(item)
                elif current_section == "concepts":
                    concepts.append(item)
                elif current_section == "tags":
                    tags.append(item)

        return EntitiesResult(
            apis=apis,
            components=components,
            concepts=concepts,
            suggested_tags=tags
        )

    def _parse_list_line(self, line: str) -> list[str]:
        """Parse a comma-separated or bracketed list."""
        # Remove brackets
        line = line.strip("[]")
        # Split by comma
        items = [item.strip().strip("'\"") for item in line.split(",")]
        return [item for item in items if item]

    def _parse_code_explanation(self, content: str, detail_level: str) -> CodeExplanationResult:
        """Parse code explanation response."""
        summary = ""
        steps = []
        parameters = {}
        returns = None
        example = None

        if detail_level == "brief":
            # For brief, the whole response is the summary
            return CodeExplanationResult(
                summary=content.strip(),
                algorithm_steps=[],
                parameters={},
                returns=None,
                example=None
            )

        lines = content.strip().split("\n")
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("SUMMARY:"):
                summary = line[8:].strip()
            elif line.startswith("ALGORITHM:"):
                current_section = "algorithm"
            elif line.startswith("PARAMETERS:"):
                current_section = "parameters"
            elif line.startswith("RETURNS:"):
                returns = line[8:].strip()
                if returns.lower() == "n/a":
                    returns = None
            elif line.startswith("EXAMPLE:"):
                current_section = "example"
                example = line[8:].strip()
                if example.lower() == "n/a":
                    example = None
            elif current_section == "algorithm":
                # Parse numbered steps
                match = re.match(r'^\d+\.\s*(.+)$', line)
                if match:
                    steps.append(match.group(1))
            elif current_section == "parameters":
                # Parse parameter descriptions
                if line.startswith("-"):
                    line = line[1:].strip()
                if ":" in line:
                    param, desc = line.split(":", 1)
                    parameters[param.strip()] = desc.strip()
            elif current_section == "example" and example:
                example += "\n" + line

        return CodeExplanationResult(
            summary=summary or content[:200],
            algorithm_steps=steps,
            parameters=parameters,
            returns=returns,
            example=example
        )

    def _parse_tags(self, content: str, max_tags: int) -> list[str]:
        """Parse generated tags."""
        tags = []

        # Try to find tags after "TAGS:" line
        if "TAGS:" in content:
            content = content.split("TAGS:")[-1]

        # Split by common separators
        for sep in ["\n", ",", ";", "|"]:
            if sep in content:
                parts = content.split(sep)
                for part in parts:
                    tag = part.strip().strip("-•").strip()
                    # Clean up the tag
                    tag = re.sub(r'^\d+\.\s*', '', tag)  # Remove numbering
                    tag = tag.lower()
                    tag = re.sub(r'[^\w\-]', '', tag)  # Keep only word chars and hyphens
                    if tag and len(tag) <= 30:  # Reasonable tag length
                        tags.append(tag)
                break

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags[:max_tags]

    def _parse_improvements(self, content: str) -> list[str]:
        """Parse improvement suggestions."""
        suggestions = []

        lines = content.strip().split("\n")
        in_suggestions = False

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if "SUGGESTIONS:" in line:
                in_suggestions = True
                continue

            if in_suggestions or line.startswith(("1.", "2.", "3.", "4.", "5.", "-")):
                # Remove numbering or bullet
                suggestion = re.sub(r'^[\d\.\-\*•]+\s*', '', line)
                if suggestion:
                    suggestions.append(suggestion)

        return suggestions[:5]


class AppleAIProvider(AIProvider):
    """Apple Foundation Models provider via Swift bridge.

    Uses on-device LLM available on macOS 15+ with Apple Silicon.
    Communicates with Swift AIService via reverse RPC.
    """

    def __init__(self):
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "apple"

    @property
    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        # Check for macOS and Apple Silicon
        import platform
        if platform.system() != "Darwin":
            self._available = False
            return False

        # Check for ARM64 (Apple Silicon)
        if platform.machine() != "arm64":
            self._available = False
            return False

        # For now, mark as unavailable until Swift bridge is complete
        # The Swift app will enable this via reverse RPC
        self._available = False
        return self._available

    async def complete(self, prompt: str, max_tokens: int = 1000) -> AIResult:
        if not self.is_available:
            return AIResult(
                success=False,
                content="",
                provider=self.name,
                error="Apple AI not available"
            )

        try:
            # This will be implemented via Swift reverse RPC
            # For now, return failure to trigger fallback
            return AIResult(
                success=False,
                content="",
                provider=self.name,
                error="Swift bridge not connected"
            )
        except Exception as e:
            return AIResult(
                success=False,
                content="",
                provider=self.name,
                error=str(e)
            )


class OllamaProvider(AIProvider):
    """Ollama local LLM provider.

    Connects to a local Ollama server for AI inference.
    Default model: llama3.2 (or configured model)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2"
    ):
        self._base_url = base_url
        self._model = model
        self._available: bool | None = None

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        try:
            import urllib.request
            req = urllib.request.Request(f"{self._base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as response:
                self._available = response.status == 200
        except Exception:
            self._available = False

        return self._available

    async def complete(self, prompt: str, max_tokens: int = 1000) -> AIResult:
        if not self.is_available:
            return AIResult(
                success=False,
                content="",
                provider=self.name,
                error="Ollama not available"
            )

        try:
            import urllib.request

            data = json.dumps({
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                }
            }).encode()

            req = urllib.request.Request(
                f"{self._base_url}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                lambda: self._make_request(req)
            )

            response = json.loads(response_text)
            return AIResult(
                success=True,
                content=response.get("response", ""),
                provider=self.name,
                model=self._model,
                usage={"total_duration": response.get("total_duration")}
            )

        except Exception as e:
            logger.warning(f"Ollama request failed: {e}")
            return AIResult(
                success=False,
                content="",
                provider=self.name,
                error=str(e)
            )

    def _make_request(self, req) -> str:
        """Make HTTP request (runs in thread pool)."""
        import urllib.request
        with urllib.request.urlopen(req, timeout=120) as response:
            return response.read().decode()


class ClaudeProvider(AIProvider):
    """Anthropic Claude API provider.

    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self, model: str = "claude-3-haiku-20240307"):
        self._model = model
        self._api_key = os.environ.get("ANTHROPIC_API_KEY")

    @property
    def name(self) -> str:
        return "claude"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    async def complete(self, prompt: str, max_tokens: int = 1000) -> AIResult:
        if not self.is_available:
            return AIResult(
                success=False,
                content="",
                provider=self.name,
                error="ANTHROPIC_API_KEY not set"
            )

        try:
            import urllib.request

            data = json.dumps({
                "model": self._model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }).encode()

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01"
                },
                method="POST"
            )

            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                lambda: self._make_request(req)
            )

            response = json.loads(response_text)
            content = response.get("content", [{}])[0].get("text", "")

            return AIResult(
                success=True,
                content=content,
                provider=self.name,
                model=self._model,
                usage=response.get("usage")
            )

        except Exception as e:
            logger.warning(f"Claude request failed: {e}")
            return AIResult(
                success=False,
                content="",
                provider=self.name,
                error=str(e)
            )

    def _make_request(self, req) -> str:
        """Make HTTP request (runs in thread pool)."""
        import urllib.request
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read().decode()


class OpenAIProvider(AIProvider):
    """OpenAI API provider.

    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self._model = model
        self._api_key = os.environ.get("OPENAI_API_KEY")

    @property
    def name(self) -> str:
        return "openai"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    async def complete(self, prompt: str, max_tokens: int = 1000) -> AIResult:
        if not self.is_available:
            return AIResult(
                success=False,
                content="",
                provider=self.name,
                error="OPENAI_API_KEY not set"
            )

        try:
            import urllib.request

            data = json.dumps({
                "model": self._model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            }).encode()

            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self._api_key}"
                },
                method="POST"
            )

            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                lambda: self._make_request(req)
            )

            response = json.loads(response_text)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")

            return AIResult(
                success=True,
                content=content,
                provider=self.name,
                model=self._model,
                usage=response.get("usage")
            )

        except Exception as e:
            logger.warning(f"OpenAI request failed: {e}")
            return AIResult(
                success=False,
                content="",
                provider=self.name,
                error=str(e)
            )

    def _make_request(self, req) -> str:
        """Make HTTP request (runs in thread pool)."""
        import urllib.request
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read().decode()


class FallbackProvider(AIProvider):
    """Provider that tries multiple backends in order."""

    def __init__(self, providers: list[AIProvider]):
        self._providers = providers

    @property
    def name(self) -> str:
        return "fallback"

    @property
    def is_available(self) -> bool:
        return any(p.is_available for p in self._providers)

    async def complete(self, prompt: str, max_tokens: int = 1000) -> AIResult:
        last_error = None

        for provider in self._providers:
            if not provider.is_available:
                continue

            result = await provider.complete(prompt, max_tokens)
            if result.success:
                return result
            last_error = result.error

        return AIResult(
            success=False,
            content="",
            provider=self.name,
            error=last_error or "No providers available"
        )


def get_available_providers() -> dict[str, bool]:
    """Get availability status of all providers."""
    return {
        "apple": AppleAIProvider().is_available,
        "ollama": OllamaProvider().is_available,
        "claude": ClaudeProvider().is_available,
        "openai": OpenAIProvider().is_available,
    }


@lru_cache(maxsize=1)
def get_ai_provider(provider_type: AIProviderType | None = None) -> AIProvider:
    """Get an AI provider instance.

    If no provider type is specified, returns a fallback provider that
    tries providers in order: Apple -> Ollama -> Claude -> OpenAI

    Args:
        provider_type: Specific provider to use, or None for auto-fallback.

    Returns:
        AIProvider instance.
    """
    if provider_type == AIProviderType.APPLE:
        return AppleAIProvider()
    elif provider_type == AIProviderType.OLLAMA:
        return OllamaProvider()
    elif provider_type == AIProviderType.CLAUDE:
        return ClaudeProvider()
    elif provider_type == AIProviderType.OPENAI:
        return OpenAIProvider()
    else:
        # Return fallback provider with priority order
        return FallbackProvider([
            AppleAIProvider(),
            OllamaProvider(),
            ClaudeProvider(),
            OpenAIProvider(),
        ])
