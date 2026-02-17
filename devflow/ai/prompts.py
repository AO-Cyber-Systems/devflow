"""Prompt templates for AI tasks.

These templates are designed to work well with both on-device models
(Apple Foundation Models, Ollama) and cloud APIs (Claude, OpenAI).
"""

from dataclasses import dataclass


@dataclass
class PromptTemplates:
    """Centralized prompt templates for AI operations."""

    # =========================================================================
    # Document Summarization
    # =========================================================================

    SUMMARIZE_DOC = """Summarize the following documentation concisely.

Content:
{content}

Provide a response in this exact format:
TITLE: [A concise title if not obvious from content]
KEY_POINTS:
- [Key point 1]
- [Key point 2]
- [Key point 3]
- [Key point 4 if applicable]
- [Key point 5 if applicable]
SUMMARY: [A 2-3 sentence summary capturing the main purpose and content]"""

    SUMMARIZE_DOC_SHORT = """Summarize this text in 1-2 sentences:

{content}

SUMMARY:"""

    # =========================================================================
    # Entity Extraction
    # =========================================================================

    EXTRACT_ENTITIES = """Extract structured information from this technical documentation.

Content:
{content}

Identify and list the following categories (leave empty if none found):

APIS: [List API names, endpoints, interfaces mentioned]
COMPONENTS: [List components, modules, services, classes mentioned]
CONCEPTS: [List technical concepts, patterns, methodologies]
SUGGESTED_TAGS: [List 5-10 tags for categorization, comma-separated]"""

    EXTRACT_ENTITIES_CODE = """Analyze this code and extract key entities.

```{language}
{code}
```

Identify:
FUNCTIONS: [Function/method names defined]
CLASSES: [Class names defined]
IMPORTS: [Key dependencies/imports]
PATTERNS: [Design patterns or architectural patterns used]
CONCEPTS: [Technical concepts implemented]"""

    # =========================================================================
    # Code Explanation
    # =========================================================================

    EXPLAIN_CODE = """Explain this {language} code clearly and concisely.

```{language}
{code}
```

Provide explanation in this format:
SUMMARY: [One sentence describing what this code does]
ALGORITHM:
1. [First step]
2. [Second step]
3. [Continue as needed]
PARAMETERS:
- [param_name]: [description]
RETURNS: [What the function returns, or "N/A" if not applicable]
EXAMPLE: [Brief usage example or "N/A" if self-evident]"""

    EXPLAIN_CODE_BRIEF = """What does this {language} code do? Answer in one sentence.

```{language}
{code}
```

This code:"""

    EXPLAIN_CODE_DETAILED = """Provide a comprehensive explanation of this {language} code.

```{language}
{code}
```

Include:
1. Purpose and functionality
2. Step-by-step algorithm breakdown
3. Parameter documentation
4. Return value explanation
5. Time/space complexity if relevant
6. Example usage
7. Potential edge cases or gotchas
8. Suggestions for improvement (if any)"""

    # =========================================================================
    # Tag Generation
    # =========================================================================

    GENERATE_TAGS = """Generate relevant tags for categorizing this content.

Content:
{content}

Requirements:
- Generate {max_tags} tags maximum
- Tags should be lowercase, single words or hyphenated phrases
- Focus on technical terms, concepts, and categories
- Make tags useful for search and organization

TAGS:"""

    # =========================================================================
    # Query Expansion
    # =========================================================================

    EXPAND_QUERY = """Expand this search query to improve search results.

Original query: "{query}"
{context_section}

Generate an expanded query that includes:
- Synonyms and related terms
- Technical variations and abbreviations
- Common alternative phrasings

Return ONLY the expanded query as a single line, no explanation:"""

    EXPAND_QUERY_WITH_CONTEXT = """Expand this search query based on the project context.

Original query: "{query}"

Project context:
{context}

Generate an expanded query that includes relevant terms from this codebase.
Return ONLY the expanded query as a single line:"""

    # =========================================================================
    # Docstring Generation
    # =========================================================================

    GENERATE_DOCSTRING = """Generate a comprehensive docstring for this {language} code.

```{language}
{code}
```

Follow {language} docstring conventions. Include:
- Brief description
- Parameters with types and descriptions
- Return value description
- Raises section if exceptions are thrown
- Example usage if helpful

Docstring:"""

    GENERATE_DOCSTRING_PYTHON = """Generate a Google-style Python docstring for this function/class.

```python
{code}
```

Follow this format:
'''[Brief one-line description]

[Longer description if needed]

Args:
    param_name: Description of parameter.

Returns:
    Description of return value.

Raises:
    ExceptionType: When this exception is raised.

Example:
    >>> example_usage()
'''

Docstring:"""

    # =========================================================================
    # Code Improvement Suggestions
    # =========================================================================

    SUGGEST_IMPROVEMENTS = """Analyze this {language} code and suggest improvements.

```{language}
{code}
```

Focus on:
1. Code quality and readability
2. Performance optimizations
3. Error handling
4. Best practices for {language}
5. Potential bugs or edge cases

List 3-5 specific, actionable suggestions:
SUGGESTIONS:
1. [First suggestion]
2. [Second suggestion]
3. [Third suggestion]"""

    # =========================================================================
    # Language Detection
    # =========================================================================

    DETECT_LANGUAGE = """Identify the programming language of this code snippet.

```
{code}
```

Respond with ONLY the language name (e.g., "python", "javascript", "rust"):"""

    # =========================================================================
    # Document Quality Validation
    # =========================================================================

    VALIDATE_DOC_QUALITY = """Evaluate the quality and completeness of this documentation.

Title: {title}
Type: {doc_type}

Content:
{content}

Assess the following and provide scores (1-5) and suggestions:

COMPLETENESS: [1-5] - Does it cover the topic adequately?
CLARITY: [1-5] - Is it easy to understand?
STRUCTURE: [1-5] - Is it well-organized?
EXAMPLES: [1-5] - Does it include helpful examples?
ACCURACY: [1-5] - Does it appear technically accurate?

SUGGESTIONS:
- [Improvement suggestion 1]
- [Improvement suggestion 2]
- [Improvement suggestion 3]"""

    # =========================================================================
    # Related Content Discovery
    # =========================================================================

    FIND_RELATED_TOPICS = """Based on this content, identify related topics that might be useful.

Content:
{content}

List 5 related topics or concepts that someone reading this might also want to learn about:
RELATED_TOPICS:
1. [Topic 1]
2. [Topic 2]
3. [Topic 3]
4. [Topic 4]
5. [Topic 5]"""

    # =========================================================================
    # Translation (for multi-language doc support)
    # =========================================================================

    TRANSLATE = """Translate the following text from {source_lang} to {target_lang}.
Preserve technical terms and code references unchanged.

Text:
{text}

Translation:"""

    # =========================================================================
    # Helper Methods
    # =========================================================================

    @classmethod
    def format_summarize(cls, content: str, short: bool = False) -> str:
        """Format the summarization prompt."""
        template = cls.SUMMARIZE_DOC_SHORT if short else cls.SUMMARIZE_DOC
        return template.format(content=content[:8000])  # Limit for context window

    @classmethod
    def format_extract_entities(cls, content: str, is_code: bool = False, language: str = "") -> str:
        """Format the entity extraction prompt."""
        if is_code:
            return cls.EXTRACT_ENTITIES_CODE.format(code=content[:8000], language=language)
        return cls.EXTRACT_ENTITIES.format(content=content[:8000])

    @classmethod
    def format_explain_code(
        cls,
        code: str,
        language: str,
        detail_level: str = "basic"
    ) -> str:
        """Format the code explanation prompt."""
        templates = {
            "brief": cls.EXPLAIN_CODE_BRIEF,
            "basic": cls.EXPLAIN_CODE,
            "detailed": cls.EXPLAIN_CODE_DETAILED,
        }
        template = templates.get(detail_level, cls.EXPLAIN_CODE)
        return template.format(code=code[:8000], language=language)

    @classmethod
    def format_generate_tags(cls, content: str, max_tags: int = 10) -> str:
        """Format the tag generation prompt."""
        return cls.GENERATE_TAGS.format(content=content[:4000], max_tags=max_tags)

    @classmethod
    def format_expand_query(cls, query: str, context: str = "") -> str:
        """Format the query expansion prompt."""
        if context:
            return cls.EXPAND_QUERY_WITH_CONTEXT.format(query=query, context=context[:2000])
        context_section = ""
        return cls.EXPAND_QUERY.format(query=query, context_section=context_section)

    @classmethod
    def format_generate_docstring(cls, code: str, language: str) -> str:
        """Format the docstring generation prompt."""
        if language.lower() == "python":
            return cls.GENERATE_DOCSTRING_PYTHON.format(code=code[:4000])
        return cls.GENERATE_DOCSTRING.format(code=code[:4000], language=language)

    @classmethod
    def format_suggest_improvements(cls, code: str, language: str) -> str:
        """Format the improvement suggestions prompt."""
        return cls.SUGGEST_IMPROVEMENTS.format(code=code[:8000], language=language)

    @classmethod
    def format_translate(cls, text: str, source_lang: str, target_lang: str) -> str:
        """Format the translation prompt."""
        return cls.TRANSLATE.format(
            text=text[:8000],
            source_lang=source_lang,
            target_lang=target_lang
        )

    @classmethod
    def format_validate_quality(cls, title: str, doc_type: str, content: str) -> str:
        """Format the document quality validation prompt."""
        return cls.VALIDATE_DOC_QUALITY.format(
            title=title,
            doc_type=doc_type,
            content=content[:8000]
        )
