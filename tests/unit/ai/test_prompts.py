"""Tests for AI prompts module."""

import pytest

from devflow.ai.prompts import PromptTemplates


class TestPromptTemplates:
    """Tests for PromptTemplates class."""

    def test_summarize_doc_template(self):
        """Test summarize doc template formatting."""
        template = PromptTemplates.SUMMARIZE_DOC

        # Should contain placeholder
        assert "{content}" in template
        assert "summarize" in template.lower()

        # Should format correctly
        formatted = template.format(content="Test content here")
        assert "Test content here" in formatted
        assert "{content}" not in formatted

    def test_extract_entities_template(self):
        """Test extract entities template formatting."""
        template = PromptTemplates.EXTRACT_ENTITIES

        assert "{content}" in template
        assert "api" in template.lower()
        assert "component" in template.lower()

        formatted = template.format(content="API endpoint documentation")
        assert "API endpoint documentation" in formatted

    def test_explain_code_template(self):
        """Test explain code template formatting."""
        template = PromptTemplates.EXPLAIN_CODE

        assert "{code}" in template
        assert "{language}" in template

        formatted = template.format(
            code="def hello(): pass",
            language="python",
        )
        assert "def hello(): pass" in formatted
        assert "python" in formatted

    def test_generate_tags_template(self):
        """Test generate tags template formatting."""
        template = PromptTemplates.GENERATE_TAGS

        assert "{content}" in template
        assert "{max_tags}" in template

        formatted = template.format(content="Test doc", max_tags=5)
        assert "Test doc" in formatted
        assert "5" in formatted

    def test_expand_query_template(self):
        """Test expand query template formatting."""
        template = PromptTemplates.EXPAND_QUERY

        assert "{query}" in template
        assert "{context_section}" in template

        formatted = template.format(query="search term", context_section="Context: project context")
        assert "search term" in formatted
        assert "project context" in formatted

    def test_generate_docstring_template(self):
        """Test generate docstring template formatting."""
        template = PromptTemplates.GENERATE_DOCSTRING

        assert "{code}" in template
        assert "{language}" in template

    def test_suggest_improvements_template(self):
        """Test suggest improvements template formatting."""
        template = PromptTemplates.SUGGEST_IMPROVEMENTS

        assert "{code}" in template
        assert "{language}" in template

    def test_detect_language_template(self):
        """Test detect language template formatting."""
        template = PromptTemplates.DETECT_LANGUAGE

        assert "{code}" in template

        formatted = template.format(code="console.log('hello')")
        assert "console.log('hello')" in formatted

    def test_translate_template(self):
        """Test translate template formatting."""
        template = PromptTemplates.TRANSLATE

        assert "{text}" in template
        assert "{source_lang}" in template
        assert "{target_lang}" in template

        formatted = template.format(
            text="Hello",
            source_lang="english",
            target_lang="spanish",
        )
        assert "Hello" in formatted
        assert "english" in formatted
        assert "spanish" in formatted
