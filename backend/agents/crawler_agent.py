"""Crawler Agent with Ollama-powered intelligent crawling and user steering."""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional, Set
from datetime import datetime
from urllib.parse import urlparse

import ollama

from backend.core.config import get_settings
from backend.services.web_scraper import WebScraper
from backend.services.chroma_service import get_chroma_service

logger = logging.getLogger(__name__)


class CrawlerAgent:
    """Intelligent crawler agent with Ollama-powered link filtering and user steering."""

    def __init__(self):
        """Initialize Crawler Agent."""
        settings = get_settings()

        self.scraper = WebScraper()
        self.chroma = get_chroma_service()

        # Ollama settings
        self.ollama_base_url = settings.ollama.base_url
        self.chat_model = settings.ollama.chat_model
        self.temperature = settings.ollama.temperature

        # Crawler settings
        self.max_depth = settings.crawler.max_depth
        self.max_pages = settings.crawler.max_pages
        self.delay = settings.crawler.delay_between_requests

        # Track crawled URLs
        self.visited_urls: Set[str] = set()

        logger.info("Crawler Agent initialized")

    async def _should_crawl_link(
        self, link: str, link_text: str, intent: str, base_domain: str
    ) -> tuple[bool, str, float]:
        """Use Ollama to determine if a link should be crawled.

        Args:
            link: URL to evaluate
            link_text: Anchor text
            intent: Crawl intent
            base_domain: Base domain for context

        Returns:
            Tuple of (should_crawl, reasoning, confidence)
        """
        try:
            # Simple heuristics first
            parsed = urlparse(link)

            # Skip non-HTTP links
            if not link.startswith(("http://", "https://")):
                return False, "Non-HTTP link", 1.0

            # Skip common non-content files
            skip_extensions = [
                ".pdf",
                ".zip",
                ".tar",
                ".gz",
                ".jpg",
                ".png",
                ".gif",
                ".mp4",
                ".mp3",
            ]
            if any(link.lower().endswith(ext) for ext in skip_extensions):
                return False, "Binary/media file", 1.0

            # Always crawl same-domain links
            link_domain = parsed.netloc
            if link_domain == base_domain:
                same_domain_score = 0.9
            else:
                same_domain_score = 0.3

            # Use Ollama to evaluate relevance
            prompt = f"""Given this crawl intent: "{intent}"

Link URL: {link}
Link text: {link_text}
Domain: {link_domain}

Should this link be crawled? Consider:
1. Is it relevant to the intent?
2. Is it likely to contain useful content?
3. Is it documentation, tutorial, or reference material?

Respond with a JSON object:
{{
    "should_crawl": true/false,
    "reasoning": "brief explanation",
    "confidence": 0.0-1.0
}}"""

            response = ollama.chat(
                model=self.chat_model,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": self.temperature},
            )

            # Parse response
            try:
                result = json.loads(response["message"]["content"])
                should_crawl = result.get("should_crawl", False)
                reasoning = result.get("reasoning", "No reason provided")
                confidence = result.get("confidence", 0.5)

                # Adjust confidence based on domain match
                if link_domain == base_domain:
                    confidence = max(confidence, same_domain_score)

                return should_crawl, reasoning, confidence

            except json.JSONDecodeError:
                # Fallback: Use simple heuristics
                logger.warning(f"Failed to parse Ollama response, using heuristics")
                return same_domain_score > 0.5, "Same domain heuristic", same_domain_score

        except Exception as e:
            logger.error(f"Error evaluating link {link}: {e}")
            # On error, use conservative approach
            return False, f"Error: {str(e)}", 0.0

    async def crawl_with_steering(
        self,
        start_url: str,
        intent: str,
        steering_queue: Optional[asyncio.Queue] = None,
    ) -> AsyncGenerator[str, None]:
        """Crawl with intelligent link filtering and optional user steering.

        Args:
            start_url: Starting URL
            intent: Crawl intent/purpose
            steering_queue: Optional queue for user steering decisions

        Yields:
            SSE-formatted events
        """
        try:
            self.visited_urls = set()
            queue = [(start_url, 0)]  # (url, depth)
            total_pages = 0
            total_chunks = 0

            base_domain = self.scraper.extract_domain(start_url)

            logger.info(f"Starting crawl: {start_url} with intent: {intent}")

            while queue and total_pages < self.max_pages:
                url, depth = queue.pop(0)

                # Check if already visited
                if url in self.visited_urls:
                    continue

                # Check max depth
                if depth > self.max_depth:
                    continue

                # Mark as visited
                self.visited_urls.add(url)

                # Emit crawling event
                yield self._format_sse(
                    "crawling",
                    {"url": url, "progress": total_pages / self.max_pages},
                )

                # Fetch page
                page_data = await self.scraper.fetch_page(url)

                if not page_data:
                    continue

                # Store in knowledge base
                doc_id = self.chroma.store_knowledge(
                    content=page_data["content"],
                    url=page_data["url"],
                    title=page_data["title"],
                    chunk_index=0,
                    total_chunks=1,
                    domain=base_domain,
                )

                total_pages += 1
                total_chunks += 1

                # Emit stored event
                yield self._format_sse("stored", {"url": url, "chunks": 1})

                # Discover new links
                discovered_links = []
                for link_data in page_data["links"]:
                    link_url = link_data["url"]
                    link_text = link_data["text"]

                    # Skip if already visited
                    if link_url in self.visited_urls:
                        continue

                    # Evaluate link
                    should_crawl, reasoning, confidence = await self._should_crawl_link(
                        link_url, link_text, intent, base_domain
                    )

                    # High confidence: crawl automatically
                    if should_crawl and confidence > 0.8:
                        queue.append((link_url, depth + 1))
                        discovered_links.append(link_url)

                    # Medium confidence: ask user
                    elif should_crawl and 0.5 < confidence <= 0.8 and steering_queue:
                        # Emit steering_needed event
                        yield self._format_sse(
                            "steering_needed",
                            {
                                "link": link_url,
                                "reasoning": reasoning,
                                "confidence": confidence,
                                "waiting": True,
                            },
                        )

                        # Wait for user decision
                        try:
                            decision = await asyncio.wait_for(
                                steering_queue.get(), timeout=60.0
                            )

                            if decision.get("approve", False):
                                queue.append((link_url, depth + 1))
                                discovered_links.append(link_url)

                        except asyncio.TimeoutError:
                            logger.warning(
                                f"Steering timeout for {link_url}, skipping"
                            )

                # Emit discovered event
                if discovered_links:
                    yield self._format_sse(
                        "discovered",
                        {"links": discovered_links, "count": len(discovered_links)},
                    )

                # Delay between requests
                await asyncio.sleep(self.delay)

            # Emit completed event
            yield self._format_sse(
                "completed",
                {
                    "total_pages": total_pages,
                    "total_chunks": total_chunks,
                    "duration": 0.0,  # TODO: Track actual duration
                },
            )

            logger.info(f"Crawl completed: {total_pages} pages, {total_chunks} chunks")

        except Exception as e:
            logger.error(f"Crawler error: {e}", exc_info=True)
            yield self._format_sse("error", {"error": str(e)})

    def _format_sse(self, event_type: str, data: Dict[str, Any]) -> str:
        """Format data as Server-Sent Event.

        Args:
            event_type: Event type
            data: Event data

        Returns:
            SSE-formatted string
        """
        event_data = {"type": event_type, **data}
        return f"event: {event_type}\ndata: {json.dumps(event_data)}\n\n"
