"""Tests for AI bridge handler."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from dataclasses import dataclass

from bridge.handlers.ai import AIHandler


class TestAIHandler:
    """Tests for AIHandler class."""

    def test_init(self):
        """Test handler initialization."""
        handler = AIHandler()

        assert handler._provider is None
        assert handler._embedder is None

    def test_get_ai_status_success(self):
        """Test get_ai_status with mocked providers."""
        handler = AIHandler()

        with patch("devflow.ai.get_available_providers") as mock_providers:
            mock_providers.return_value = {"ollama": True, "apple": False}

            # Mock the embedder
            mock_embedder = MagicMock()
            mock_embedder.get_status.return_value = {
                "active_backend": "fastembed",
                "dimensions": 384,
            }
            handler._embedder = mock_embedder

            # Mock the provider
            mock_provider = MagicMock()
            mock_provider.name = "ollama"
            handler._provider = mock_provider

            result = handler.get_ai_status()

            assert result["available"] is True
            assert "ollama" in result["providers"]
            assert result["embeddings"]["active_backend"] == "fastembed"

    def test_get_ai_status_error(self):
        """Test get_ai_status handles errors."""
        handler = AIHandler()

        with patch.object(handler, "_get_embedder", side_effect=Exception("Test error")):
            with patch("devflow.ai.get_available_providers", side_effect=Exception("Test")):
                result = handler.get_ai_status()

                assert result["available"] is False
                assert "error" in result


class TestSummarize:
    """Tests for summarize method."""

    def test_summarize_success(self):
        """Test successful summarization."""
        handler = AIHandler()

        @dataclass
        class MockSummary:
            title: str
            key_points: list
            summary: str

        mock_provider = MagicMock()
        mock_provider.summarize = AsyncMock(return_value=MockSummary(
            title="Test Title",
            key_points=["Point 1", "Point 2"],
            summary="Test summary",
        ))
        handler._provider = mock_provider

        result = handler.summarize("Test content", max_length=100)

        assert result["success"] is True
        assert result["title"] == "Test Title"
        assert len(result["key_points"]) == 2
        assert result["summary"] == "Test summary"

    def test_summarize_error(self):
        """Test summarization error handling."""
        handler = AIHandler()

        mock_provider = MagicMock()
        mock_provider.summarize = AsyncMock(side_effect=Exception("AI error"))
        handler._provider = mock_provider

        result = handler.summarize("Test content")

        assert result["success"] is False
        assert "error" in result


class TestExtractEntities:
    """Tests for extract_entities method."""

    def test_extract_entities_success(self):
        """Test successful entity extraction."""
        handler = AIHandler()

        @dataclass
        class MockEntities:
            apis: list
            components: list
            concepts: list
            suggested_tags: list

        mock_provider = MagicMock()
        mock_provider.extract_entities = AsyncMock(return_value=MockEntities(
            apis=["API1"],
            components=["Component1"],
            concepts=["Concept1"],
            suggested_tags=["tag1"],
        ))
        handler._provider = mock_provider

        result = handler.extract_entities("Test content")

        assert result["success"] is True
        assert "apis" in result
        assert "components" in result
        assert "concepts" in result
        assert "suggested_tags" in result


class TestExplainCode:
    """Tests for explain_code method."""

    def test_explain_code_success(self):
        """Test successful code explanation."""
        handler = AIHandler()

        @dataclass
        class MockExplanation:
            summary: str
            algorithm_steps: list
            parameters: dict
            returns: str
            example: str

        mock_provider = MagicMock()
        mock_provider.explain_code = AsyncMock(return_value=MockExplanation(
            summary="Adds numbers",
            algorithm_steps=["Step 1"],
            parameters={"a": "first"},
            returns="Sum",
            example="add(1,2)",
        ))
        handler._provider = mock_provider

        result = handler.explain_code("def add(a, b): return a + b", "python")

        assert result["success"] is True
        assert result["summary"] == "Adds numbers"
        assert "algorithm_steps" in result


class TestGenerateTags:
    """Tests for generate_tags method."""

    def test_generate_tags_success(self):
        """Test successful tag generation."""
        handler = AIHandler()

        mock_provider = MagicMock()
        mock_provider.generate_tags = AsyncMock(return_value=["tag1", "tag2", "tag3"])
        handler._provider = mock_provider

        result = handler.generate_tags("Test content", max_tags=5)

        assert result["success"] is True
        assert len(result["tags"]) == 3


class TestExpandQuery:
    """Tests for expand_query method."""

    def test_expand_query_success(self):
        """Test successful query expansion."""
        handler = AIHandler()

        mock_provider = MagicMock()
        mock_provider.expand_query = AsyncMock(return_value="expanded query terms")
        handler._provider = mock_provider

        result = handler.expand_query("search", context="code")

        assert result["success"] is True
        assert result["original_query"] == "search"
        assert result["expanded_query"] == "expanded query terms"


class TestGetEmbedding:
    """Tests for get_embedding method."""

    def test_get_embedding_success(self):
        """Test successful embedding."""
        handler = AIHandler()

        mock_embedder = MagicMock()
        mock_embedder.embed.return_value = [0.1, 0.2, 0.3]
        mock_embedder.active_backend = "fastembed"
        handler._embedder = mock_embedder

        result = handler.get_embedding("Test text")

        assert result["success"] is True
        assert len(result["embedding"]) == 3
        assert result["dimensions"] == 3
        assert result["backend"] == "fastembed"


class TestBatchEmbeddings:
    """Tests for batch_embeddings method."""

    def test_batch_embeddings_success(self):
        """Test successful batch embeddings."""
        handler = AIHandler()

        mock_embedder = MagicMock()
        mock_embedder.embed_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
        mock_embedder.dimensions = 2
        mock_embedder.active_backend = "fastembed"
        handler._embedder = mock_embedder

        result = handler.batch_embeddings(["Text 1", "Text 2"])

        assert result["success"] is True
        assert result["count"] == 2
        assert result["dimensions"] == 2


class TestFindSimilar:
    """Tests for find_similar method."""

    def test_find_similar_success(self):
        """Test successful similarity search."""
        handler = AIHandler()

        mock_embedder = MagicMock()
        mock_embedder.find_similar.return_value = [
            (0, "text 1", 0.9),
            (1, "text 2", 0.8),
        ]
        mock_embedder.active_backend = "fastembed"
        handler._embedder = mock_embedder

        result = handler.find_similar("query", ["text 1", "text 2"], limit=2)

        assert result["success"] is True
        assert len(result["results"]) == 2
        assert result["results"][0]["similarity"] == 0.9


class TestDetectLanguage:
    """Tests for detect_language method."""

    def test_detect_language_success(self):
        """Test successful language detection."""
        handler = AIHandler()

        mock_provider = MagicMock()
        mock_provider.detect_language = AsyncMock(return_value="python")
        handler._provider = mock_provider

        result = handler.detect_language("def hello(): pass")

        assert result["success"] is True
        assert result["language"] == "python"


class TestTranslate:
    """Tests for translate method."""

    def test_translate_success(self):
        """Test successful translation."""
        handler = AIHandler()

        mock_provider = MagicMock()
        mock_provider.translate = AsyncMock(return_value="Hola")
        handler._provider = mock_provider

        result = handler.translate("Hello", "english", "spanish")

        assert result["success"] is True
        assert result["original"] == "Hello"
        assert result["translated"] == "Hola"


class TestOCRMethods:
    """Tests for OCR methods."""

    def test_extract_text_from_image_file_not_found(self):
        """Test image OCR with non-existent file."""
        handler = AIHandler()

        result = handler.extract_text_from_image("/nonexistent/path.png")

        assert result["success"] is False
        assert "not found" in result["error"].lower() or "not yet implemented" in result["error"].lower()

    def test_extract_text_from_pdf_file_not_found(self):
        """Test PDF OCR with non-existent file."""
        handler = AIHandler()

        result = handler.extract_text_from_pdf("/nonexistent/path.pdf")

        assert result["success"] is False
        assert "not found" in result["error"].lower() or "pymupdf" in result["error"].lower()
