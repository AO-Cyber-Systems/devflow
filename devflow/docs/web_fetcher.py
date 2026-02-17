"""
Web documentation fetcher.

Fetches documentation from URLs, extracts content, and stores
it in the documentation system with semantic indexing.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# Try to import optional dependencies
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    BeautifulSoup = None

try:
    import html2text
    HTML2TEXT_AVAILABLE = True
except ImportError:
    HTML2TEXT_AVAILABLE = False
    html2text = None


@dataclass
class FetchedPage:
    """A fetched web page."""

    url: str
    title: str
    content: str  # Markdown content
    html: str  # Original HTML
    links: list[str] = field(default_factory=list)
    fetched_at: datetime = field(default_factory=datetime.now)
    content_type: str = "text/html"
    status_code: int = 200

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "links": self.links,
            "fetched_at": self.fetched_at.isoformat(),
            "content_type": self.content_type,
            "status_code": self.status_code,
        }


@dataclass
class FetchResult:
    """Result of a fetch operation."""

    success: bool
    pages: list[FetchedPage] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total_fetched: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "pages": [p.to_dict() for p in self.pages],
            "errors": self.errors[:10],
            "total_fetched": self.total_fetched,
        }


class WebDocFetcher:
    """Fetches and processes web documentation."""

    # Common documentation site patterns
    DOC_PATTERNS = [
        r"/docs/",
        r"/documentation/",
        r"/guide/",
        r"/tutorial/",
        r"/api/",
        r"/reference/",
        r"/manual/",
        r"/learn/",
    ]

    # Content selectors for common doc sites
    CONTENT_SELECTORS = [
        "article",
        "main",
        "[role='main']",
        ".documentation",
        ".docs-content",
        ".markdown-body",
        ".content",
        "#content",
        ".post-content",
        ".article-content",
    ]

    # Elements to remove
    REMOVE_SELECTORS = [
        "nav",
        "header",
        "footer",
        "aside",
        ".sidebar",
        ".navigation",
        ".menu",
        ".toc",
        ".table-of-contents",
        ".ads",
        ".advertisement",
        "script",
        "style",
        "noscript",
        ".cookie-banner",
        ".newsletter",
    ]

    def __init__(
        self,
        max_pages: int = 50,
        max_depth: int = 3,
        timeout: float = 30.0,
        follow_links: bool = True,
    ):
        """
        Initialize the fetcher.

        Args:
            max_pages: Maximum pages to fetch
            max_depth: Maximum link depth to follow
            timeout: Request timeout in seconds
            follow_links: Whether to follow links
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.timeout = timeout
        self.follow_links = follow_links

        self._html2text = None
        if HTML2TEXT_AVAILABLE:
            self._html2text = html2text.HTML2Text()
            self._html2text.ignore_links = False
            self._html2text.ignore_images = True
            self._html2text.ignore_emphasis = False
            self._html2text.body_width = 0  # No wrapping

    def fetch_url(self, url: str) -> FetchResult:
        """
        Fetch a single URL.

        Args:
            url: URL to fetch

        Returns:
            FetchResult with the fetched page
        """
        if not HTTPX_AVAILABLE:
            return FetchResult(
                success=False,
                errors=["httpx not installed. Run: pip install httpx"],
            )

        if not BS4_AVAILABLE:
            return FetchResult(
                success=False,
                errors=["beautifulsoup4 not installed. Run: pip install beautifulsoup4"],
            )

        try:
            page = self._fetch_single_page(url)
            if page:
                return FetchResult(
                    success=True,
                    pages=[page],
                    total_fetched=1,
                )
            else:
                return FetchResult(
                    success=False,
                    errors=[f"Failed to fetch {url}"],
                )
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return FetchResult(
                success=False,
                errors=[str(e)],
            )

    def fetch_docs_site(
        self,
        url: str,
        include_patterns: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
    ) -> FetchResult:
        """
        Fetch an entire documentation site.

        Args:
            url: Starting URL
            include_patterns: URL patterns to include
            exclude_patterns: URL patterns to exclude

        Returns:
            FetchResult with all fetched pages
        """
        if not HTTPX_AVAILABLE or not BS4_AVAILABLE:
            return FetchResult(
                success=False,
                errors=["Required packages not installed. Run: pip install httpx beautifulsoup4"],
            )

        pages: list[FetchedPage] = []
        errors: list[str] = []
        visited: set[str] = set()
        to_visit: list[tuple[str, int]] = [(url, 0)]  # (url, depth)

        base_domain = urlparse(url).netloc

        while to_visit and len(pages) < self.max_pages:
            current_url, depth = to_visit.pop(0)

            # Normalize URL
            current_url = self._normalize_url(current_url)

            if current_url in visited:
                continue

            visited.add(current_url)

            # Check domain
            if urlparse(current_url).netloc != base_domain:
                continue

            # Check patterns
            if include_patterns:
                if not any(re.search(p, current_url) for p in include_patterns):
                    continue

            if exclude_patterns:
                if any(re.search(p, current_url) for p in exclude_patterns):
                    continue

            # Fetch page
            try:
                page = self._fetch_single_page(current_url)
                if page:
                    pages.append(page)

                    # Add links to visit
                    if self.follow_links and depth < self.max_depth:
                        for link in page.links:
                            if link not in visited:
                                to_visit.append((link, depth + 1))

            except Exception as e:
                errors.append(f"{current_url}: {str(e)}")
                logger.debug(f"Error fetching {current_url}: {e}")

        return FetchResult(
            success=len(pages) > 0,
            pages=pages,
            errors=errors,
            total_fetched=len(pages),
        )

    def _fetch_single_page(self, url: str) -> FetchedPage | None:
        """Fetch and process a single page."""
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, headers={
                    "User-Agent": "DevFlow Documentation Fetcher/1.0",
                    "Accept": "text/html,application/xhtml+xml",
                })

                if response.status_code != 200:
                    logger.debug(f"Non-200 status for {url}: {response.status_code}")
                    return None

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type and "application/xhtml" not in content_type:
                    logger.debug(f"Non-HTML content for {url}: {content_type}")
                    return None

                html = response.text

        except Exception as e:
            logger.debug(f"Request failed for {url}: {e}")
            return None

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = self._extract_title(soup, url)

        # Extract links
        links = self._extract_links(soup, url)

        # Extract and clean content
        content_html = self._extract_content(soup)

        # Convert to markdown
        if self._html2text:
            content = self._html2text.handle(str(content_html))
        else:
            content = content_html.get_text(separator="\n\n")

        # Clean up content
        content = self._clean_content(content)

        return FetchedPage(
            url=url,
            title=title,
            content=content,
            html=html,
            links=links,
            status_code=200,
        )

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract page title."""
        # Try title tag
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        # Try h1
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()

        # Try og:title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Fallback to URL path
        path = urlparse(url).path
        return path.split("/")[-1] or "Untitled"

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> list[str]:
        """Extract links from page."""
        links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Skip anchors, javascript, mailto
            if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            # Resolve relative URLs
            full_url = urljoin(base_url, href)

            # Remove fragment
            full_url = full_url.split("#")[0]

            # Skip non-http
            if not full_url.startswith(("http://", "https://")):
                continue

            links.append(full_url)

        return list(set(links))

    def _extract_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Extract main content from page."""
        # Remove unwanted elements
        for selector in self.REMOVE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()

        # Try to find main content area
        for selector in self.CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content:
                return content

        # Fallback to body
        body = soup.find("body")
        if body:
            return body

        return soup

    def _clean_content(self, content: str) -> str:
        """Clean up extracted content."""
        # Remove excessive whitespace
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = re.sub(r" {2,}", " ", content)

        # Remove empty links
        content = re.sub(r"\[]\([^)]*\)", "", content)

        # Clean up list formatting
        content = re.sub(r"\n\s*\*\s*\n", "\n", content)

        return content.strip()

    def _normalize_url(self, url: str) -> str:
        """Normalize a URL."""
        # Remove fragment
        url = url.split("#")[0]

        # Remove trailing slash
        url = url.rstrip("/")

        return url


def get_web_fetcher(**kwargs) -> WebDocFetcher:
    """Get a web documentation fetcher instance."""
    return WebDocFetcher(**kwargs)
