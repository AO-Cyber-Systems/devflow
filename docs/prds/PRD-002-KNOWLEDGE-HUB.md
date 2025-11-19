# PRD-002: Knowledge Hub Service

**Version:** 1.0  
**Status:** Draft  
**Last Updated:** November 18, 2025  
**Parent PRD:** PRD-001 (System Overview)

---

## Overview

The Knowledge Hub Service is DevFlow's central repository for all project-related information. It provides intelligent ingestion, storage, and retrieval of documentation, code examples, decisions, and patterns. This service acts as the "memory" of the development process, making information accessible to both human users and AI agents through advanced search capabilities.

---

## Goals

### Primary Goals
1. Enable AI agents to access comprehensive project context for informed decision-making
2. Provide fast, accurate semantic search across all project knowledge
3. Automate knowledge ingestion from multiple sources (web, docs, code)
4. Maintain knowledge freshness through incremental updates

### Secondary Goals
1. Support multiple embedding models and LLM providers
2. Enable knowledge organization by source, type, and tags
3. Provide knowledge quality metrics and validation
4. Support knowledge versioning and history

---

## User Stories

### As a Developer
- I want to crawl documentation websites so that agents have access to framework docs
- I want to upload PDFs and documents so that design decisions are searchable
- I want to tag and organize knowledge sources so that I can manage information effectively
- I want to see what knowledge is available so that I can verify completeness

### As an AI Agent
- I want to search for relevant information semantically so that I can find answers efficiently
- I want to access code examples so that I can follow project patterns
- I want to see source metadata so that I can assess information credibility
- I want to get ranked results so that the most relevant information comes first

### As a Team Lead
- I want to see knowledge coverage metrics so that I can identify documentation gaps
- I want to control what knowledge is indexed so that I can maintain quality
- I want to track knowledge usage so that I can optimize what we document
- I want to ensure knowledge freshness so that information stays current

---

## Architecture

### Component Diagram

```
┌────────────────────────────────────────────────────────────┐
│              Knowledge Hub Service                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Crawler    │  │   Document   │  │    Code      │   │
│  │   Engine     │  │   Processor  │  │   Indexer    │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                  │            │
│         └─────────────────┼──────────────────┘            │
│                           │                               │
│                  ┌────────▼────────┐                      │
│                  │   Chunking      │                      │
│                  │   Strategy      │                      │
│                  └────────┬────────┘                      │
│                           │                               │
│                  ┌────────▼────────┐                      │
│                  │   Embedding     │                      │
│                  │   Generation    │                      │
│                  └────────┬────────┘                      │
│                           │                               │
│         ┌─────────────────┼─────────────────┐            │
│         │                 │                 │            │
│  ┌──────▼───────┐  ┌──────▼──────┐  ┌──────▼──────┐    │
│  │   Qdrant     │  │  PostgreSQL  │  │    Cache    │    │
│  │ Vector Store │  │   Metadata   │  │   (Redis)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │            Search & Retrieval API                 │    │
│  ├──────────────────────────────────────────────────┤    │
│  │  - Semantic Search                                │    │
│  │  - Hybrid Search (Vector + Keyword)               │    │
│  │  - Reranking                                      │    │
│  │  - Code Example Extraction                        │    │
│  │  - Source Filtering                               │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. INGESTION:
   Web URL/Document → Crawler/Parser → Content Extraction
                    ↓
   Content → Chunking Strategy → Chunks (with metadata)
                    ↓
   Chunks → Embedding Model → Vector Embeddings
                    ↓
   Embeddings + Metadata → Storage (Qdrant + PostgreSQL)

2. RETRIEVAL:
   Query → Embedding → Vector Search (Qdrant)
                    ↓
   Initial Results → Hybrid Ranking → Reranking (LLM)
                    ↓
   Ranked Results → Context Assembly → Response
```

---

## Core Features

### 1. Web Crawling & Confluence Integration

**Description**: Intelligent web crawling that automatically detects documentation structure and extracts content, plus native Confluence integration for enterprise knowledge bases.

**Capabilities**:
- Sitemap detection and parsing
- Automatic link discovery and following
- Content extraction from HTML (clean text)
- Respect for robots.txt
- Rate limiting and politeness
- Incremental updates (detect changes)
- **Confluence Integration** (via PRD-006):
  - OAuth-based authentication per user
  - Crawl Confluence spaces as knowledge sources
  - Sync pages, comments, and attachments
  - Bidirectional sync: DevFlow updates → Confluence pages
  - Maintain links and structure from Confluence

**Technical Details**:
```python
class WebCrawler:
    """Crawls websites and extracts documentation."""
    
    def crawl_site(self, url: str) -> CrawlResult:
        """
        Crawl a website starting from the given URL.
        
        Steps:
        1. Detect sitemap (sitemap.xml)
        2. If no sitemap, discover links recursively
        3. Extract content from each page
        4. Clean HTML → Markdown
        5. Store with metadata (URL, title, last_modified)
        """
        pass
    
    def detect_sitemap(self, base_url: str) -> Optional[str]:
        """Check for sitemap.xml at common locations."""
        pass
    
    def extract_content(self, html: str) -> str:
        """Convert HTML to clean markdown."""
        pass
```

**Configuration**:
```yaml
crawler:
  max_depth: 3
  max_pages: 1000
  rate_limit_ms: 1000
  user_agent: "DevFlow Knowledge Crawler"
  respect_robots: true
  follow_external_links: false
```

### 2. Document Processing

**Description**: Upload and process various document formats with intelligent parsing.

**Supported Formats**:
- PDF (including OCR for scanned documents)
- Microsoft Word (.docx)
- Markdown (.md)
- Plain text (.txt)
- Code files (.py, .js, .java, etc.)
- Jupyter Notebooks (.ipynb)

**Processing Pipeline**:
```python
class DocumentProcessor:
    """Processes uploaded documents."""
    
    def process_document(self, file: UploadFile) -> ProcessResult:
        """
        Process a document through the pipeline.
        
        Steps:
        1. Detect file type
        2. Extract text content
        3. Extract metadata (author, date, title)
        4. Identify sections and structure
        5. Extract code blocks
        6. Chunk content appropriately
        """
        pass
    
    def extract_pdf(self, file: bytes) -> str:
        """Extract text from PDF."""
        pass
    
    def extract_code_blocks(self, content: str) -> List[CodeBlock]:
        """Extract and label code examples."""
        pass
```

### 3. Code Example Extraction

**Description**: Automatically identify, extract, and index code examples with language detection.

**Features**:
- Language detection (Python, JavaScript, Java, etc.)
- Syntax validation
- Context extraction (surrounding explanation)
- API endpoint detection
- Function/class extraction

**Implementation**:
```python
class CodeExtractor:
    """Extracts and indexes code examples."""
    
    def extract_examples(self, content: str) -> List[CodeExample]:
        """
        Extract code examples from content.
        
        Identifies:
        - Fenced code blocks (```python)
        - Inline code (`code`)
        - Interactive examples
        - API endpoints (REST, GraphQL)
        """
        pass
    
    def detect_language(self, code: str) -> str:
        """Detect programming language."""
        pass
    
    def validate_syntax(self, code: str, language: str) -> bool:
        """Check if code is syntactically valid."""
        pass
```

### 4. Intelligent Chunking

**Description**: Split content into optimal chunks for embedding and retrieval.

**Strategies**:
- **Semantic Chunking**: Split by topic/section
- **Fixed Size**: Split by token count
- **Sliding Window**: Overlapping chunks
- **Hierarchical**: Parent-child chunk relationships

**Implementation**:
```python
class ChunkingStrategy:
    """Strategies for splitting content into chunks."""
    
    def chunk_by_semantics(
        self, 
        content: str, 
        max_tokens: int = 512
    ) -> List[Chunk]:
        """
        Split content by semantic boundaries.
        
        Looks for:
        - Section headers (# ## ###)
        - Paragraph breaks
        - Natural topic transitions
        """
        pass
    
    def chunk_with_overlap(
        self, 
        content: str, 
        chunk_size: int = 512,
        overlap: int = 50
    ) -> List[Chunk]:
        """Create overlapping chunks."""
        pass
```

### 5. Vector Search & RAG

**Description**: Advanced semantic search with multiple retrieval strategies.

**Search Modes**:

**A. Pure Semantic Search**
```python
def semantic_search(query: str, top_k: int = 10) -> List[Result]:
    """
    Vector similarity search via AOSentry.
    
    Steps:
    1. Embed query using AOSentry (handles caching & provider routing)
    2. Search Qdrant for similar vectors
    3. Return top-k results
    """
    pass
```

**B. Hybrid Search**
```python
def hybrid_search(query: str, top_k: int = 10) -> List[Result]:
    """
    Combined vector + keyword search.
    
    Steps:
    1. Vector search (semantic)
    2. Keyword search (BM25)
    3. Merge and rank results
    """
    pass
```

**C. Reranked Search**
```python
def reranked_search(query: str, top_k: int = 10) -> List[Result]:
    """
    Search with LLM reranking via AOSentry.
    
    Steps:
    1. Initial retrieval (hybrid search)
    2. Get top-50 candidates
    3. Rerank with LLM based on relevance
    4. Return top-k
    """
    pass
```

**D. Contextual Embeddings**
```python
def contextual_search(query: str, context: str) -> List[Result]:
    """
    Search with additional context.
    
    Uses:
    - Previous conversation
    - Current task context
    - Project-specific context
    """
    pass
```

**B. Hybrid Search**
```python
def hybrid_search(query: str, top_k: int = 10) -> List[Result]:
    """
    Combined vector + keyword search.
    
    Steps:
    1. Vector search (semantic)
    2. Keyword search (BM25)
    3. Merge and rank results
    """
    pass
```

**C. Reranked Search**
```python
def reranked_search(query: str, top_k: int = 10) -> List[Result]:
    """
    Search with LLM reranking via AOSentry.
    
    Steps:
    1. Initial retrieval (hybrid search)
    2. Get top-50 candidates
    3. Rerank with LLM based on relevance
    4. Return top-k
    """
    pass
```

**D. Contextual Embeddings**
```python
def contextual_search(query: str, context: str) -> List[Result]:
    """
    Search with additional context.
    
    Uses:
    - Previous conversation
    - Current task context
    - Project-specific context
    """
    pass
```

### 6. Source Management

**Description**: Organize and manage knowledge sources.

**Features**:
- Source categorization (docs, code, decisions, etc.)
- Tagging system
- Source priority/credibility scoring
- Update tracking
- Source deletion and re-indexing

**Data Model**:
```python
class KnowledgeSource:
    id: str
    type: SourceType  # web, document, code, manual
    url: Optional[str]
    title: str
    description: str
    tags: List[str]
    priority: int  # 1-10, affects search ranking
    created_at: datetime
    updated_at: datetime
    chunk_count: int
    status: SourceStatus  # active, indexing, error

class Chunk:
    id: str
    source_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    position: int  # position in source
    parent_chunk_id: Optional[str]  # for hierarchical chunks
```

---

## Deployment (Docker Only)

To ensure consistency and performance, the Knowledge Hub is designed to run on Docker (Local/Prod). SQLite is **not supported**.

### Docker Compose Stack

```yaml
services:
  knowledge-hub:
    image: devflow/knowledge-hub:latest
    depends_on:
      - qdrant
      - postgres
      - redis
    environment:
      - EMBEDDING_PROVIDER=aosentry
      - DATABASE_URL=postgresql://user:pass@postgres:5432/devflow

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage

  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
```

---

## API Specification

### REST Endpoints

#### 1. Crawl Website
```
POST /api/knowledge/crawl
Content-Type: application/json

Request:
{
  "url": "https://docs.example.com",
  "max_depth": 3,
  "max_pages": 1000,
  "tags": ["documentation", "api"]
}

Response:
{
  "crawl_id": "crawl_123",
  "status": "started",
  "estimated_pages": 250
}
```

#### 2. Upload Document
```
POST /api/knowledge/upload
Content-Type: multipart/form-data

Request:
file: <binary>
metadata: {
  "title": "Architecture Decision Record",
  "tags": ["architecture", "adr"],
  "priority": 8
}

Response:
{
  "source_id": "src_456",
  "status": "processing",
  "chunks_created": 42
}
```

#### 3. Search Knowledge
```
POST /api/knowledge/search
Content-Type: application/json

Request:
{
  "query": "How to implement authentication?",
  "mode": "hybrid",  // semantic, hybrid, reranked
  "filters": {
    "tags": ["authentication", "security"],
    "sources": ["src_123", "src_456"]
  },
  "top_k": 10,
  "include_code_examples": true
}

Response:
{
  "results": [
    {
      "chunk_id": "chunk_789",
      "source_id": "src_123",
      "source_title": "Auth Documentation",
      "content": "To implement authentication...",
      "score": 0.89,
      "metadata": {
        "url": "https://docs.example.com/auth",
        "section": "Getting Started"
      },
      "code_examples": [
        {
          "language": "python",
          "code": "def authenticate(user, password): ..."
        }
      ]
    }
  ],
  "total_results": 47,
  "search_time_ms": 123
}
```

#### 4. List Sources
```
GET /api/knowledge/sources?tags=documentation&status=active

Response:
{
  "sources": [
    {
      "id": "src_123",
      "title": "Framework Documentation",
      "type": "web",
      "url": "https://docs.example.com",
      "tags": ["documentation", "framework"],
      "chunk_count": 342,
      "last_updated": "2025-11-18T10:30:00Z"
    }
  ]
}
```

#### 5. Update Source
```
PUT /api/knowledge/sources/{source_id}
Content-Type: application/json

Request:
{
  "tags": ["documentation", "framework", "v2"],
  "priority": 9,
  "recrawl": true
}

Response:
{
  "source_id": "src_123",
  "status": "updated",
  "recrawl_started": true
}
```

#### 6. Delete Source
```
DELETE /api/knowledge/sources/{source_id}

Response:
{
  "source_id": "src_123",
  "status": "deleted",
  "chunks_removed": 342
}
```

### MCP Tools

```python
# Available to AI agents via MCP

@mcp_tool
def search_knowledge(
    query: str,
    mode: str = "hybrid",
    top_k: int = 10,
    filters: Optional[Dict] = None
) -> List[SearchResult]:
    """
    Search the knowledge base.
    
    Args:
        query: Search query
        mode: "semantic", "hybrid", or "reranked"
        top_k: Number of results
        filters: Optional filters (tags, sources)
    
    Returns:
        List of relevant knowledge chunks
    """
    pass

@mcp_tool
def get_code_examples(
    language: str,
    topic: str,
    top_k: int = 5
) -> List[CodeExample]:
    """
    Get code examples for a specific topic.
    
    Args:
        language: Programming language
        topic: What the code should demonstrate
        top_k: Number of examples
    
    Returns:
        List of code examples with context
    """
    pass

@mcp_tool
def get_source_info(source_id: str) -> SourceInfo:
    """
    Get information about a knowledge source.
    
    Args:
        source_id: ID of the source
    
    Returns:
        Source metadata and statistics
    """
    pass
```

---

## Data Storage

### Qdrant Collections

```python
# Vector embeddings
collection_name = "devflow_knowledge"
vector_size = 3072  # text-embedding-3-large

# Schema:
{
    "id": "chunk_123",
    "vector": [0.1, 0.2, ...],  # 3072 dimensions
    "payload": {
        "source_id": "src_456",
        "content": "Full chunk text...",
        "metadata": {
            "url": "https://...",
            "title": "...",
            "section": "...",
            "position": 5
        },
        "tags": ["documentation", "api"],
        "language": "en",
        "has_code": true
    }
}
```

### PostgreSQL Tables

```sql
-- Knowledge sources
CREATE TABLE knowledge_sources (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,  -- web, document, code, manual
    url TEXT,
    title TEXT NOT NULL,
    description TEXT,
    tags TEXT[],
    priority INTEGER DEFAULT 5,
    status VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    chunk_count INTEGER DEFAULT 0,
    metadata JSONB
);

-- Chunks (metadata only, vectors in Qdrant)
CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY,
    source_id UUID REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    position INTEGER,
    parent_chunk_id UUID REFERENCES knowledge_chunks(id),
    token_count INTEGER,
    has_code BOOLEAN DEFAULT FALSE,
    language VARCHAR(10),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- Code examples
CREATE TABLE code_examples (
    id UUID PRIMARY KEY,
    chunk_id UUID REFERENCES knowledge_chunks(id) ON DELETE CASCADE,
    language VARCHAR(50) NOT NULL,
    code TEXT NOT NULL,
    context TEXT,
    is_valid BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Search analytics
CREATE TABLE search_logs (
    id UUID PRIMARY KEY,
    query TEXT NOT NULL,
    mode VARCHAR(50),
    filters JSONB,
    result_count INTEGER,
    search_time_ms INTEGER,
    user_id UUID,
    agent_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_sources_tags ON knowledge_sources USING GIN(tags);
CREATE INDEX idx_sources_status ON knowledge_sources(status);
CREATE INDEX idx_chunks_source ON knowledge_chunks(source_id);
CREATE INDEX idx_chunks_has_code ON knowledge_chunks(has_code);
CREATE INDEX idx_examples_language ON code_examples(language);
```

---

## Configuration

### Environment Variables

```bash
# LLM Configuration (via AOSentry)
AOSENTRY_API_KEY=ae-...
AOSENTRY_URL=https://aosentry.aocodex.ai/v1

# Embedding Provider (hosted or local)
EMBEDDING_PROVIDER=aosentry  # or 'local'
EMBEDDING_MODEL=text-embedding-3-large  # or 'bge-m3' for local
EMBEDDING_BATCH_SIZE=100

# Vector Store (Qdrant via Docker)
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION=devflow_knowledge
QDRANT_API_KEY=  # optional

# Database (PostgreSQL via Docker)
DATABASE_URL=postgresql://user:pass@postgres:5432/devflow
REDIS_URL=redis://redis:6379/0

# Crawler
CRAWLER_MAX_WORKERS=5
CRAWLER_RATE_LIMIT_MS=1000
CRAWLER_USER_AGENT=DevFlow Knowledge Crawler

# Processing
CHUNK_SIZE=512
CHUNK_OVERLAP=50
MAX_FILE_SIZE_MB=50
```

### Service Configuration (YAML)

```yaml
knowledge_hub:
  crawler:
    max_depth: 3
    max_pages: 1000
    rate_limit_ms: 1000
    respect_robots: true
    timeout_seconds: 30
  
  document_processing:
    max_file_size_mb: 50
    supported_formats:
      - pdf
      - docx
      - md
      - txt
      - ipynb
    ocr_enabled: true
  
  chunking:
    strategy: semantic  # semantic, fixed, sliding, hierarchical
    max_tokens: 512
    overlap_tokens: 50
    min_chunk_length: 100
  
  embedding:
    model: text-embedding-3-large
    dimensions: 3072
    batch_size: 100
    cache_ttl_hours: 24
  
  search:
    default_mode: hybrid  # semantic, hybrid, reranked
    rerank_enabled: true
    rerank_model: gpt-4-turbo-preview
    max_initial_results: 50
    cache_results: true
    cache_ttl_minutes: 30
  
  code_extraction:
    enabled: true
    validate_syntax: true
    extract_apis: true
    supported_languages:
      - python
      - javascript
      - typescript
      - java
      - go
```

---

## Performance Requirements

| Metric | Target | Critical Path |
|--------|--------|---------------|
| Search latency (p95) | < 200ms | Embedding + Vector search |
| Crawl throughput | > 10 pages/sec | Concurrent requests |
| Document processing | < 5 sec/doc | Parsing + Chunking |
| Embedding generation | < 1 sec/chunk | API call + batching |
| Storage efficiency | < 2KB/chunk | Compression |

---

## Security Considerations

1. **Content Sanitization**: Remove scripts, sanitize HTML
2. **Access Control**: Source-level permissions
3. **Rate Limiting**: Prevent abuse of search API
4. **Content Validation**: Verify uploaded files are safe
5. **PII Detection**: Scan for sensitive information
6. **Audit Logging**: Track all knowledge modifications

---

## Testing Strategy

### Unit Tests
- Crawler: URL parsing, content extraction
- Processor: Document parsing, chunking
- Search: Embedding, ranking algorithms

### Integration Tests
- End-to-end crawl and search
- Multi-format document processing
- Embedding pipeline

### Performance Tests
- Search latency under load
- Concurrent crawling capacity
- Large document handling

---

## Success Metrics

### Functional
- Search relevance (measured by click-through rate): > 80%
- Knowledge coverage (documented vs. undocumented): > 90%
- Code example accuracy: > 95%

### Performance
- Search latency (p95): < 200ms
- Indexing throughput: > 1000 chunks/minute
- System availability: > 99.9%

### Usage
- Daily searches per user: > 20
- Knowledge source growth rate: > 10 sources/week
- Agent knowledge access rate: > 100 queries/hour

---

## Confluence as Knowledge Source

With the **Atlassian Integration** (PRD-006), Confluence becomes a first-class knowledge source:

1. **Add Confluence Space as Source**:
   - User authenticates via OAuth
   - Select Confluence space to sync
   - DevFlow crawls all pages in the space
   - Pages indexed as knowledge chunks

2. **Bidirectional Knowledge Sync**:
   - DevFlow can read Confluence pages for context
   - Agents can update Confluence pages with findings
   - Updates maintain page structure and formatting

3. **Automatic Updates**:
   - Webhook notifications when Confluence pages change
   - Incremental re-indexing of changed content
   - Preserves knowledge freshness

See **PRD-006: SDLC Tool Integrations** for complete Confluence integration details.

---

## Future Enhancements

1. **Knowledge Graph**: Connect related concepts
2. **Active Learning**: Improve search from user feedback
3. **Multi-modal**: Support images, videos, diagrams
4. **Real-time Sync**: Watch files for changes
5. **Collaborative Curation**: Team-based knowledge management
6. **Knowledge Quality Scoring**: Automatic quality assessment
7. **Differential Updates**: Smart re-indexing of changed content

---

**End of PRD-002**
