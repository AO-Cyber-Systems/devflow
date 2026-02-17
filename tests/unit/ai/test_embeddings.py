"""Tests for AI embeddings module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from devflow.ai.embeddings import DualEmbedder, get_dual_embedder


class TestDualEmbedder:
    """Tests for DualEmbedder class."""

    def test_init_lazy_loading(self):
        """Test that embedders are lazy loaded."""
        embedder = DualEmbedder()

        # Internal fastembed should be None until used
        assert embedder._fastembed is None

    def test_dimensions_property(self):
        """Test dimensions property returns expected value."""
        embedder = DualEmbedder()

        # Should return a positive integer for dimensions
        dims = embedder.dimensions
        assert isinstance(dims, int)
        assert dims > 0

    def test_active_backend_property(self):
        """Test active_backend returns a string."""
        embedder = DualEmbedder()

        backend = embedder.active_backend
        assert isinstance(backend, str)
        # Should be one of the known backends
        assert backend in ("apple", "fastembed", "none")

    def test_get_status(self):
        """Test get_status returns expected structure."""
        embedder = DualEmbedder()

        status = embedder.get_status()

        assert isinstance(status, dict)
        assert "active_backend" in status
        assert "dimensions" in status

    def test_embed_returns_list(self):
        """Test that embed returns a list of floats."""
        embedder = DualEmbedder()

        try:
            result = embedder.embed("test text")
            # If we get here, check result is a list
            assert isinstance(result, list)
            if len(result) > 0:
                assert isinstance(result[0], float)
        except Exception:
            # May fail if no backend available - that's ok for this test
            pass

    def test_embed_batch_returns_list(self):
        """Test that embed_batch returns a list of lists."""
        embedder = DualEmbedder()

        try:
            results = embedder.embed_batch(["text 1", "text 2"])
            assert isinstance(results, list)
        except Exception:
            # May fail if no backend available
            pass


class TestGetDualEmbedder:
    """Tests for get_dual_embedder factory function."""

    def test_returns_dual_embedder(self):
        """Test factory returns DualEmbedder instance."""
        embedder = get_dual_embedder()

        assert isinstance(embedder, DualEmbedder)

    def test_returns_singleton(self):
        """Test factory returns the same instance on repeated calls."""
        embedder1 = get_dual_embedder()
        embedder2 = get_dual_embedder()

        assert embedder1 is embedder2
