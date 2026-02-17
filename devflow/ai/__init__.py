"""AI module for DevFlow.

Provides AI-powered features using Apple's on-device models with fallback
to local LLMs and optional cloud APIs.

Main components:
- providers: AI provider abstraction (Apple, Ollama, Claude, OpenAI)
- embeddings: Dual embedding system (Apple NLEmbedding + FastEmbed)
- prompts: Prompt templates for AI tasks
"""

from .providers import (
    AIProvider,
    AIProviderType,
    AppleAIProvider,
    OllamaProvider,
    ClaudeProvider,
    OpenAIProvider,
    get_ai_provider,
    get_available_providers,
)
from .embeddings import DualEmbedder, get_dual_embedder
from .prompts import PromptTemplates

__all__ = [
    # Providers
    "AIProvider",
    "AIProviderType",
    "AppleAIProvider",
    "OllamaProvider",
    "ClaudeProvider",
    "OpenAIProvider",
    "get_ai_provider",
    "get_available_providers",
    # Embeddings
    "DualEmbedder",
    "get_dual_embedder",
    # Prompts
    "PromptTemplates",
]
