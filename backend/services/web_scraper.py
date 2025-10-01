"""Web scraping utilities for crawler agent."""

import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper with robots.txt support."""

    def __init__(self):
        """Initialize web scraper."""
        settings = get_settings()
        self.user_agent = settings.crawler.user_agent
        self.timeout = settings.crawler.timeout
        self.respect_robots = settings.crawler.respect_robots_txt

        # Robots.txt cache
        self._robots_cache: Dict[str, RobotFileParser] = {}

        logger.info("WebScraper initialized")

    async def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if URL can be fetched
        """
        if not self.respect_robots:
            return True

        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"

            # Check cache
            if base_url not in self._robots_cache:
                robots_url = urljoin(base_url, "/robots.txt")

                # Fetch robots.txt
                async with httpx.AsyncClient() as client:
                    try:
                        response = await client.get(
                            robots_url,
                            headers={"User-Agent": self.user_agent},
                            timeout=self.timeout,
                            follow_redirects=True,
                        )

                        if response.status_code == 200:
                            rp = RobotFileParser()
                            rp.parse(response.text.splitlines())
                            self._robots_cache[base_url] = rp
                        else:
                            # No robots.txt, allow all
                            rp = RobotFileParser()
                            rp.parse([])
                            self._robots_cache[base_url] = rp

                    except Exception as e:
                        logger.warning(f"Failed to fetch robots.txt for {base_url}: {e}")
                        # On error, allow
                        rp = RobotFileParser()
                        rp.parse([])
                        self._robots_cache[base_url] = rp

            # Check if allowed
            return self._robots_cache[base_url].can_fetch(self.user_agent, url)

        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {e}")
            return True  # On error, allow

    async def fetch_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse a web page.

        Args:
            url: URL to fetch

        Returns:
            Dictionary with content, links, title, and metadata
        """
        try:
            # Check robots.txt
            if not await self.can_fetch(url):
                logger.warning(f"Blocked by robots.txt: {url}")
                return None

            # Fetch page
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                    follow_redirects=True,
                )

                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status_code}")
                    return None

                # Parse HTML
                soup = BeautifulSoup(response.text, "lxml")

                # Extract title
                title = soup.title.string if soup.title else url

                # Extract main content (simple heuristic)
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text content
                content = soup.get_text(separator="\n", strip=True)

                # Extract links
                links = []
                for link in soup.find_all("a", href=True):
                    href = link["href"]
                    # Convert to absolute URL
                    absolute_url = urljoin(url, href)

                    # Only include HTTP(S) links
                    if absolute_url.startswith(("http://", "https://")):
                        links.append(
                            {
                                "url": absolute_url,
                                "text": link.get_text(strip=True),
                            }
                        )

                # Extract metadata
                metadata = {
                    "url": str(response.url),  # Final URL after redirects
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                }

                logger.info(f"Fetched page: {url} ({len(content)} chars, {len(links)} links)")

                return {
                    "url": str(response.url),
                    "title": title,
                    "content": content,
                    "links": links,
                    "metadata": metadata,
                }

        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL.

        Args:
            url: URL to parse

        Returns:
            Domain name
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""

    def is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain.

        Args:
            url1: First URL
            url2: Second URL

        Returns:
            True if same domain
        """
        return self.extract_domain(url1) == self.extract_domain(url2)
