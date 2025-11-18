# PRD-009: AOSentry Integration

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)

---

## Overview

DevFlow routes all LLM operations through **AOSentry** (aosentry.aocodex.ai), a unified LLM gateway that provides OpenAI API compatibility, automatic retry/fallback, cost tracking, and enterprise features. This PRD defines how DevFlow integrates with AOSentry as a drop-in replacement for direct LLM provider access.

---

## Goals

### Primary Goals
1. **OpenAI API Compatibility**: Drop-in replacement for OpenAI SDK
2. **Single LLM Gateway**: All LLM calls routed through AOSentry
3. **Cost Optimization**: Leverage AOSentry's caching and routing
4. **Provider Flexibility**: Support multiple LLM providers via AOSentry
5. **On-Premise LLM Support**: Route to local LLMs when needed

### Secondary Goals
1. Automatic retry and fallback handling
2. Cost tracking per project/workflow
3. Token usage analytics
4. Model performance monitoring
5. Budget controls and alerts

---

## Architecture

### Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     DevFlow Services                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Knowledge    │  │ Workflow     │  │ MCP Gateway  │     │
│  │ Hub          │  │ Engine       │  │              │     │
│  │              │  │              │  │              │     │
│  │ Needs:       │  │ Needs:       │  │ Needs:       │     │
│  │ - Embeddings │  │ - Chat LLM   │  │ - Chat LLM   │     │
│  │ - Chat LLM   │  │ - Guardian   │  │              │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │             │
│         └─────────────────┼──────────────────┘             │
│                           │                                 │
│                  ┌────────▼────────┐                        │
│                  │  AOSentry SDK   │                        │
│                  │  (OpenAI compat)│                        │
│                  └────────┬────────┘                        │
└───────────────────────────┼─────────────────────────────────┘
                            │
                            │ HTTPS (OpenAI API format)
                            │ Authorization: Bearer ${AOSENTRY_API_KEY}
                            │
┌───────────────────────────▼─────────────────────────────────┐
│              AOSentry.aocodex.ai                            │
│              (Unified LLM Gateway)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ OpenAI API Compatible Endpoints                         │
│  ✅ Authentication & Rate Limiting                          │
│  ✅ Cost Tracking & Budgets                                │
│  ✅ Intelligent Caching                                     │
│  ✅ Automatic Retry & Fallback                              │
│  ✅ Model Routing (cost vs performance)                     │
│  ✅ Prompt Safety & Filtering                               │
│  ✅ Token Usage Analytics                                   │
│                                                             │
└─────────────┬───────────────────────────────────────────────┘
              │
       ┌──────┴──────┬──────────┬──────────┬──────────┐
       │             │          │          │          │
┌──────▼──────┐ ┌───▼────┐ ┌───▼────┐ ┌──▼─────┐ ┌──▼────────┐
│   OpenAI    │ │Anthropc│ │OpenRout│ │ Gemini │ │ On-Prem   │
│             │ │        │ │  er    │ │        │ │ LLMs      │
│ gpt-4-turbo │ │ claude │ │ mixtral│ │ gemini │ │ Ollama    │
│ gpt-3.5     │ │ sonnet │ │ llama  │ │ -pro   │ │ vLLM      │
└─────────────┘ └────────┘ └────────┘ └────────┘ └───────────┘
```

---

## OpenAI API Compatibility

### Drop-In Replacement

DevFlow uses the OpenAI SDK but points to AOSentry endpoint:

```python
# services/common/llm_client.py

from openai import OpenAI
from services.common.secrets_manager import get_secret

class LLMClient:
    """
    Unified LLM client using AOSentry as OpenAI-compatible gateway.
    
    Usage is identical to OpenAI SDK, but all calls route through AOSentry.
    """
    
    def __init__(self):
        # AOSentry is OpenAI API compatible
        self.client = OpenAI(
            api_key=get_secret("AOSENTRY_API_KEY"),
            base_url="https://aosentry.aocodex.ai/v1"  # OpenAI-compatible endpoint
        )
        
        # Model preferences (AOSentry handles routing)
        self.default_chat_model = get_secret(
            "DEFAULT_CHAT_MODEL", 
            op_reference="op://DevFlow/LLM/default_chat_model"
        ) or "gpt-4-turbo"
        
        self.default_embedding_model = get_secret(
            "DEFAULT_EMBEDDING_MODEL",
            op_reference="op://DevFlow/LLM/default_embedding_model"
        ) or "text-embedding-3-large"
    
    def chat_completion(
        self, 
        messages: list,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        stream: bool = False,
        **kwargs
    ):
        """
        Create chat completion via AOSentry.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (defaults to configured default)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            **kwargs: Additional OpenAI API parameters
        
        Returns:
            OpenAI ChatCompletion object (or stream iterator)
        
        Example:
            >>> llm = LLMClient()
            >>> response = llm.chat_completion([
            ...     {"role": "system", "content": "You are a helpful assistant."},
            ...     {"role": "user", "content": "Hello!"}
            ... ])
            >>> print(response.choices[0].message.content)
        """
        
        # Use default model if not specified
        model = model or self.default_chat_model
        
        # AOSentry handles everything (retry, fallback, caching, etc.)
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            **kwargs
        )
        
        return response
    
    def embedding(
        self,
        input: str | list[str],
        model: str = None,
        **kwargs
    ):
        """
        Create embeddings via AOSentry.
        
        Args:
            input: Text string or list of strings to embed
            model: Embedding model name (defaults to configured default)
            **kwargs: Additional OpenAI API parameters
        
        Returns:
            OpenAI Embedding object
        
        Example:
            >>> llm = LLMClient()
            >>> result = llm.embedding("Hello, world!")
            >>> vector = result.data[0].embedding
            >>> print(len(vector))  # 3072 for text-embedding-3-large
        """
        
        # Use default embedding model if not specified
        model = model or self.default_embedding_model
        
        # AOSentry provides embeddings via OpenAI-compatible API
        response = self.client.embeddings.create(
            model=model,
            input=input,
            **kwargs
        )
        
        return response
    
    def stream_chat_completion(
        self,
        messages: list,
        model: str = None,
        temperature: float = 0.7,
        **kwargs
    ):
        """
        Stream chat completion via AOSentry.
        
        Yields chunks as they arrive.
        
        Example:
            >>> llm = LLMClient()
            >>> for chunk in llm.stream_chat_completion(messages):
            ...     if chunk.choices[0].delta.content:
            ...         print(chunk.choices[0].delta.content, end='')
        """
        
        model = model or self.default_chat_model
        
        stream = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
            **kwargs
        )
        
        for chunk in stream:
            yield chunk


# Global instance
llm_client = LLMClient()
```

### Endpoint Mapping

AOSentry provides OpenAI-compatible endpoints:

| OpenAI Endpoint | AOSentry Endpoint | Purpose |
|----------------|-------------------|---------|
| `/v1/chat/completions` | `https://aosentry.aocodex.ai/v1/chat/completions` | Chat completions |
| `/v1/embeddings` | `https://aosentry.aocodex.ai/v1/embeddings` | Text embeddings |
| `/v1/models` | `https://aosentry.aocodex.ai/v1/models` | List available models |
| `/v1/completions` | `https://aosentry.aocodex.ai/v1/completions` | Legacy completions |

---

## Configuration

### Environment Variables

```bash
# .env

# AOSentry Configuration (Required)
AOSENTRY_API_KEY=sk-aosentry-xxxxxxxxxxxxx
AOSENTRY_API_URL=https://aosentry.aocodex.ai

# Model Preferences (Optional - defaults shown)
DEFAULT_CHAT_MODEL=gpt-4-turbo
DEFAULT_EMBEDDING_MODEL=text-embedding-3-large
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096

# Cost Controls (Optional)
LLM_MONTHLY_BUDGET_USD=1000
LLM_ALERT_THRESHOLD_PCT=80
```

### Application Configuration

```yaml
# config/llm.yaml

llm:
  provider: aosentry
  
  # AOSentry connection
  api_key_source: "op://DevFlow/AOSentry/api_key"  # or env: AOSENTRY_API_KEY
  endpoint: https://aosentry.aocodex.ai
  
  # Model routing preferences
  # AOSentry handles actual provider selection
  models:
    chat:
      default: gpt-4-turbo
      fast: gpt-3.5-turbo      # For simple tasks
      smart: gpt-4-turbo       # For complex reasoning
      fallback: claude-3-sonnet  # If primary fails
    
    embedding:
      default: text-embedding-3-large
      fallback: text-embedding-3-small
    
    guardian:
      model: gpt-4-turbo  # Guardian needs strong reasoning
      temperature: 0.3    # Lower temp for consistency
  
  # Generation parameters
  defaults:
    temperature: 0.7
    max_tokens: 4096
    top_p: 1.0
    frequency_penalty: 0.0
    presence_penalty: 0.0
  
  # Timeout and retry (handled by AOSentry, but can override)
  timeout_seconds: 60
  max_retries: 3  # AOSentry does this automatically
  
  # Caching (leverages AOSentry's built-in cache)
  caching:
    enabled: true
    ttl_seconds: 3600  # 1 hour
    aggressive_mode: false  # Set true to maximize cache hits
  
  # Cost management
  budget:
    monthly_limit_usd: 1000
    alert_thresholds:
      - 50  # 50% of budget
      - 75  # 75% of budget
      - 90  # 90% of budget
    auto_disable_at_limit: false  # Continue but alert
  
  # On-premise LLM support
  on_prem:
    enabled: false
    # When enabled, AOSentry routes to these endpoints
    endpoints:
      ollama: http://localhost:11434
      vllm: http://localhost:8000
    models:
      chat: "llama3:70b"
      embedding: "mxbai-embed-large"
```

---

## Key Features Leveraged from AOSentry

### 1. Automatic Caching

AOSentry automatically caches responses for identical requests:

```python
# First call - goes to LLM provider
response1 = llm_client.chat_completion([
    {"role": "user", "content": "Explain RAG in one sentence"}
])
# Response time: ~2 seconds
# Cost: $0.002

# Second identical call - served from cache
response2 = llm_client.chat_completion([
    {"role": "user", "content": "Explain RAG in one sentence"}
])
# Response time: ~50ms (40x faster!)
# Cost: $0.000 (free!)
```

**Benefits:**
- Faster response times
- Reduced costs
- Improved reliability (cache serves even if provider down)

### 2. Automatic Retry & Fallback

AOSentry handles transient failures automatically:

```python
# DevFlow code - no error handling needed!
response = llm_client.chat_completion(messages)

# Behind the scenes, AOSentry:
# 1. Tries primary model (gpt-4-turbo)
# 2. If rate limited, waits and retries (3 attempts)
# 3. If provider down, falls back to configured fallback (claude-3-sonnet)
# 4. If fallback fails, tries tertiary option (gemini-pro)
# 5. Returns best available response
```

**Benefits:**
- No error handling code needed in DevFlow
- Higher success rate (99.9% vs ~95% without fallback)
- Automatic model degradation under load

### 3. Intelligent Model Routing

AOSentry can route based on cost vs performance:

```python
# config/llm.yaml

models:
  chat:
    routing_strategy: cost_optimized  # or: performance_optimized, balanced
    
    # AOSentry automatically chooses:
    # - gpt-3.5-turbo for simple tasks (cheap)
    # - gpt-4-turbo for complex reasoning (expensive but better)
    # - claude-3-sonnet if OpenAI unavailable
```

### 4. Cost Tracking & Analytics

AOSentry provides detailed cost analytics:

```python
# services/analytics/llm_usage.py

async def get_llm_costs(
    start_date: datetime,
    end_date: datetime,
    group_by: str = "project"  # project, user, model, workflow
):
    """
    Query AOSentry analytics API for cost breakdown.
    
    Returns detailed cost metrics from AOSentry.
    """
    
    # AOSentry analytics API
    response = await http_client.get(
        "https://aosentry.aocodex.ai/v1/analytics/costs",
        headers={"Authorization": f"Bearer {AOSENTRY_API_KEY}"},
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "group_by": group_by
        }
    )
    
    return response.json()
    # Returns:
    # {
    #   "total_cost_usd": 127.45,
    #   "total_tokens": 5234890,
    #   "by_project": {
    #     "project-123": {
    #       "cost_usd": 45.30,
    #       "tokens": 1823456,
    #       "by_model": {
    #         "gpt-4-turbo": {"cost": 40.20, "tokens": 402000},
    #         "gpt-3.5-turbo": {"cost": 5.10, "tokens": 1421456}
    #       }
    #     }
    #   },
    #   "cache_savings_usd": 23.12,
    #   "cache_hit_rate": 0.35
    # }
```

### 5. Prompt Safety & Filtering

AOSentry can filter sensitive data before sending to LLMs:

```yaml
# config/llm.yaml

safety:
  enabled: true
  
  # Filter patterns (regex)
  filters:
    - pattern: '\b\d{3}-\d{2}-\d{4}\b'  # SSN
      replacement: '[SSN REDACTED]'
    
    - pattern: '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email
      replacement: '[EMAIL REDACTED]'
    
    - pattern: 'sk-[a-zA-Z0-9]{48}'  # API keys
      replacement: '[API_KEY REDACTED]'
  
  # PII detection (AOSentry feature)
  detect_pii: true
  block_pii: false  # Just log, don't block
```

---

## On-Premise LLM Support

DevFlow can route LLM calls to on-premise models via AOSentry:

### Configuration

```yaml
# config/llm.yaml (on-premise mode)

llm:
  provider: aosentry
  
  # AOSentry will route to on-prem models
  on_prem:
    enabled: true
    
    # Ollama for chat
    ollama:
      endpoint: http://ollama.company.internal:11434
      models:
        chat: "llama3:70b"
        code: "codellama:34b"
    
    # vLLM for embeddings
    vllm:
      endpoint: http://vllm.company.internal:8000
      models:
        embedding: "BAAI/bge-large-en-v1.5"
    
    # Fallback to cloud if on-prem unavailable
    fallback_to_cloud: true
```

### Routing Logic

```python
# AOSentry handles routing automatically

# Request goes to AOSentry with metadata
response = llm_client.chat_completion(
    messages=messages,
    model="gpt-4-turbo",  # Logical model name
    extra_headers={
        "X-DevFlow-Deployment": "onprem",
        "X-DevFlow-Prefer-Local": "true"
    }
)

# AOSentry routing decision:
# 1. Check if on-prem enabled for this customer
# 2. Route to Ollama llama3:70b (closest equivalent)
# 3. If Ollama down, fallback to cloud gpt-4-turbo
# 4. Return response (DevFlow doesn't know which was used)
```

---

## Usage Examples

### Example 1: Knowledge Hub Embeddings

```python
# services/knowledge/embedding_service.py

from services.common.llm_client import llm_client

class EmbeddingService:
    """Generate embeddings for knowledge chunks."""
    
    async def embed_chunks(self, chunks: list[str]) -> list[list[float]]:
        """
        Generate embeddings for text chunks.
        
        Uses AOSentry for:
        - Automatic batching (up to 2048 inputs)
        - Caching (identical chunks)
        - Retry on failure
        - Cost tracking
        """
        
        # Single call to AOSentry (handles batching)
        response = llm_client.embedding(
            input=chunks,
            model="text-embedding-3-large"
        )
        
        # Extract vectors
        embeddings = [item.embedding for item in response.data]
        
        return embeddings
```

### Example 2: Workflow Engine - Guardian

```python
# services/workflow/guardian_monitor.py

from services.common.llm_client import llm_client

class GuardianMonitor:
    """Monitor agent coherence with phase goals."""
    
    async def analyze_coherence(
        self,
        agent_trajectory: list[str],
        phase_instructions: str,
        done_definitions: list[str]
    ) -> float:
        """
        Analyze if agent is aligned with phase goals.
        
        Returns coherence score (0-1).
        """
        
        prompt = f"""
        Analyze if the agent's recent actions are aligned with the phase goals.
        
        Phase Instructions:
        {phase_instructions}
        
        Done Definitions (must complete):
        {chr(10).join(f"- {d}" for d in done_definitions)}
        
        Agent's Recent Actions:
        {chr(10).join(f"- {action}" for action in agent_trajectory[-10:])}
        
        Respond with JSON:
        {{
          "coherence_score": 0.0-1.0,
          "reasoning": "Brief explanation",
          "recommendation": "continue | intervene | redirect"
        }}
        """
        
        # AOSentry handles retry, fallback, caching
        response = llm_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a workflow guardian. Analyze agent behavior objectively."},
                {"role": "user", "content": prompt}
            ],
            model="gpt-4-turbo",  # Guardian needs strong reasoning
            temperature=0.3,  # Lower temp for consistency
            response_format={"type": "json_object"}  # Ensure JSON response
        )
        
        # Parse response
        import json
        analysis = json.loads(response.choices[0].message.content)
        
        return analysis["coherence_score"]
```

### Example 3: Streaming Chat for MCP

```python
# services/mcp/chat_handler.py

from services.common.llm_client import llm_client

async def handle_chat_request(messages: list) -> AsyncIterator[str]:
    """
    Stream chat response via MCP.
    
    AOSentry supports streaming (OpenAI compatible).
    """
    
    # Stream from AOSentry
    stream = llm_client.stream_chat_completion(
        messages=messages,
        model="gpt-4-turbo",
        temperature=0.7
    )
    
    # Yield chunks as they arrive
    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

---

## Monitoring & Analytics

### Cost Dashboard

```python
# routes/api/analytics.py

from fastapi import APIRouter
from services.analytics.llm_usage import get_llm_costs
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/analytics/llm")


@router.get("/costs/summary")
async def get_cost_summary(days: int = 30):
    """
    Get LLM cost summary for last N days.
    
    Data sourced from AOSentry analytics API.
    """
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    costs = await get_llm_costs(start_date, end_date, group_by="project")
    
    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days
        },
        "total_cost_usd": costs["total_cost_usd"],
        "total_tokens": costs["total_tokens"],
        "cache_savings_usd": costs["cache_savings_usd"],
        "cache_hit_rate": costs["cache_hit_rate"],
        "by_project": costs["by_project"],
        "budget_status": {
            "monthly_limit": 1000,
            "current_spend": costs["total_cost_usd"],
            "remaining": 1000 - costs["total_cost_usd"],
            "percent_used": (costs["total_cost_usd"] / 1000) * 100
        }
    }
```

### UI Dashboard Integration

```typescript
// ui/src/views/LLMAnalyticsView.tsx

import { useQuery } from '@tanstack/react-query';
import { LineChart, BarChart } from '@/components/charts';

export function LLMAnalyticsView() {
  const { data: costs } = useQuery({
    queryKey: ['llm-costs', 30],
    queryFn: () => fetch('/api/analytics/llm/costs/summary?days=30').then(r => r.json())
  });
  
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">LLM Usage & Costs</h1>
      
      {/* Cost Summary Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard
          title="Total Spend"
          value={`$${costs.total_cost_usd.toFixed(2)}`}
          subtitle="Last 30 days"
        />
        <MetricCard
          title="Cache Savings"
          value={`$${costs.cache_savings_usd.toFixed(2)}`}
          subtitle={`${(costs.cache_hit_rate * 100).toFixed(1)}% hit rate`}
        />
        <MetricCard
          title="Budget Used"
          value={`${costs.budget_status.percent_used.toFixed(1)}%`}
          subtitle={`$${costs.budget_status.remaining.toFixed(2)} remaining`}
        />
        <MetricCard
          title="Total Tokens"
          value={formatNumber(costs.total_tokens)}
          subtitle="Processed"
        />
      </div>
      
      {/* Cost Trends Chart */}
      <LineChart
        title="Daily Costs"
        data={costs.daily_breakdown}
        xKey="date"
        yKey="cost_usd"
      />
      
      {/* Cost by Project */}
      <BarChart
        title="Cost by Project"
        data={Object.entries(costs.by_project).map(([name, data]) => ({
          name,
          cost: data.cost_usd
        }))}
        xKey="name"
        yKey="cost"
      />
    </div>
  );
}
```

---

## Error Handling

### AOSentry Error Responses

```python
# services/common/llm_client.py (error handling)

from openai import OpenAIError, RateLimitError, APIError

class LLMClient:
    # ... existing code ...
    
    def chat_completion_with_error_handling(self, messages: list, **kwargs):
        """
        Chat completion with explicit error handling.
        
        Note: AOSentry handles most errors automatically (retry, fallback),
        but some errors should be handled by DevFlow.
        """
        
        try:
            response = self.chat_completion(messages, **kwargs)
            return response
            
        except RateLimitError as e:
            # AOSentry already retried, but still rate limited
            # This means we've exceeded our AOSentry quota
            logger.error(f"AOSentry rate limit exceeded: {e}")
            raise DevFlowLLMQuotaExceeded(
                "LLM quota exceeded. Please upgrade your plan or wait for reset."
            )
        
        except APIError as e:
            # AOSentry couldn't complete request after all retries/fallbacks
            logger.error(f"AOSentry API error: {e}")
            raise DevFlowLLMUnavailable(
                "LLM service temporarily unavailable. Please try again later."
            )
        
        except Exception as e:
            # Unexpected error
            logger.exception(f"Unexpected LLM error: {e}")
            raise
```

---

## Testing

### Unit Tests

```python
# tests/test_llm_client.py

import pytest
from unittest.mock import patch, MagicMock
from services.common.llm_client import LLMClient

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client (AOSentry uses OpenAI SDK)."""
    with patch('services.common.llm_client.OpenAI') as mock:
        yield mock


def test_chat_completion(mock_openai_client):
    """Test basic chat completion."""
    
    # Setup mock
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Hello!"))
    ]
    mock_openai_client.return_value.chat.completions.create.return_value = mock_response
    
    # Test
    llm = LLMClient()
    response = llm.chat_completion([
        {"role": "user", "content": "Hi"}
    ])
    
    # Verify
    assert response.choices[0].message.content == "Hello!"
    mock_openai_client.return_value.chat.completions.create.assert_called_once()


def test_embedding(mock_openai_client):
    """Test embedding generation."""
    
    # Setup mock
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(embedding=[0.1, 0.2, 0.3])
    ]
    mock_openai_client.return_value.embeddings.create.return_value = mock_response
    
    # Test
    llm = LLMClient()
    response = llm.embedding("Test text")
    
    # Verify
    assert response.data[0].embedding == [0.1, 0.2, 0.3]
```

### Integration Tests

```python
# tests/integration/test_aosentry_integration.py

import pytest
import os

@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("AOSENTRY_API_KEY"), reason="AOSentry not configured")
def test_real_aosentry_chat():
    """Test real call to AOSentry (integration test)."""
    
    from services.common.llm_client import llm_client
    
    response = llm_client.chat_completion([
        {"role": "user", "content": "Say 'test successful' and nothing else."}
    ])
    
    assert "test successful" in response.choices[0].message.content.lower()


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("AOSENTRY_API_KEY"), reason="AOSentry not configured")
def test_real_aosentry_embedding():
    """Test real embedding via AOSentry."""
    
    from services.common.llm_client import llm_client
    
    response = llm_client.embedding("Hello, world!")
    
    # text-embedding-3-large returns 3072-dimensional vectors
    assert len(response.data[0].embedding) == 3072
```

---

## Success Metrics

### Integration Health

| Metric | Target | Critical |
|--------|--------|----------|
| AOSentry availability | > 99.9% | Yes |
| Response time (p95) | < 2s | Yes |
| Cache hit rate | > 30% | No |
| Cost savings via cache | > 20% | No |
| Failed requests | < 0.1% | Yes |

### Cost Optimization

| Metric | Target | Impact |
|--------|--------|--------|
| Cost per 1K tokens (vs direct) | -30% | High |
| Cache hit rate | > 35% | High |
| Avg tokens per request | < 2000 | Medium |
| Budget adherence | 100% | High |

---

## Future Enhancements

### Phase 1 (Q2 2026)
1. **Prompt Templates** - Reusable prompt library via AOSentry
2. **A/B Testing** - Test multiple models simultaneously
3. **Custom Models** - Fine-tuned models via AOSentry
4. **Advanced Routing** - AI-based model selection

### Phase 2 (Q3 2026)
1. **Prompt Engineering IDE** - Visual prompt editor
2. **Model Performance Comparison** - Side-by-side benchmarks
3. **Cost Prediction** - Estimate costs before execution
4. **Custom Caching Strategies** - Per-use-case cache policies

---

**End of PRD-009**
