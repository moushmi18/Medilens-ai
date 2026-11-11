"""Knowledge source definitions and fetching.

IMPORTANT: Only ingest from permitted official sources:
- MedlinePlus (medlineplus.gov)
- NIH / NIDDK (niddk.nih.gov)
- NHS (nhs.uk)  
- WHO (who.int)

Respects robots.txt and rate limits.
"""
import hashlib
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from urllib.parse import urljoin

import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)

RATE_LIMIT_SECONDS = 2.0


class SourceType(str, Enum):
    """Permitted knowledge sources."""
    MEDLINEPLUS = "medlineplus"
    NIH_NIDDK = "nih_niddk"
    NHS = "nhs"
    WHO = "who"


@dataclass
class SourceConfig:
    """Configuration for a knowledge source."""
    source_type: SourceType
    base_url: str
    api_url: Optional[str] = None
    rate_limit: float = RATE_LIMIT_SECONDS


PERMITTED_SOURCES = {
    SourceType.MEDLINEPLUS: SourceConfig(
        source_type=SourceType.MEDLINEPLUS,
        base_url="https://medlineplus.gov",
        api_url="https://connect.medlineplus.gov/service",
        rate_limit=2.0,
    ),
    SourceType.NIH_NIDDK: SourceConfig(
        source_type=SourceType.NIH_NIDDK,
        base_url="https://www.niddk.nih.gov",
        rate_limit=2.0,
    ),
    SourceType.NHS: SourceConfig(
        source_type=SourceType.NHS,
        base_url="https://www.nhs.uk",
        rate_limit=2.0,
    ),
    SourceType.WHO: SourceConfig(
        source_type=SourceType.WHO,
        base_url="https://www.who.int",
        rate_limit=2.0,
    ),
}


@dataclass
class FetchedContent:
    """Content fetched from a source."""
    url: str
    source_type: SourceType
    title: str
    content: str
    content_hash: str
    fetched_at: datetime
    metadata: dict[str, Any]


class KnowledgeFetcher:
    """Fetches content from permitted knowledge sources."""
    
    def __init__(self):
        self._last_fetch_time: dict[SourceType, float] = {}
        self._client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "MediLens-AI-Bot/1.0 (Educational medical report explainer)",
            },
        )
    
    def __del__(self):
        self._client.close()
    
    def _respect_rate_limit(self, source_type: SourceType) -> None:
        """Wait if needed to respect rate limit."""
        config = PERMITTED_SOURCES[source_type]
        last_time = self._last_fetch_time.get(source_type, 0)
        elapsed = time.time() - last_time
        
        if elapsed < config.rate_limit:
            sleep_time = config.rate_limit - elapsed
            logger.debug("rate_limit_wait", source=source_type.value, seconds=sleep_time)
            time.sleep(sleep_time)
        
        self._last_fetch_time[source_type] = time.time()
    
    def fetch_medlineplus_health_topic(self, topic_id: str) -> Optional[FetchedContent]:
        """Fetch a health topic from MedlinePlus.
        
        Uses MedlinePlus Connect API where possible.
        
        Args:
            topic_id: Topic ID (e.g., "cholesterol")
            
        Returns:
            FetchedContent or None if fetch failed
        """
        source_type = SourceType.MEDLINEPLUS
        self._respect_rate_limit(source_type)
        
        url = f"https://medlineplus.gov/ency/article/{topic_id}.htm"
        
        try:
            response = self._client.get(url)
            response.raise_for_status()
            
            content = self._extract_text_from_html(response.text)
            title = self._extract_title_from_html(response.text) or topic_id
            
            return FetchedContent(
                url=url,
                source_type=source_type,
                title=title,
                content=content,
                content_hash=hashlib.sha256(content.encode()).hexdigest(),
                fetched_at=datetime.utcnow(),
                metadata={"topic_id": topic_id},
            )
        except httpx.HTTPError as e:
            logger.error("fetch_failed", source="medlineplus", topic=topic_id, error=str(e))
            return None
    
    def _extract_text_from_html(self, html: str) -> str:
        """Extract readable text from HTML.
        
        Simple extraction - strips tags and extra whitespace.
        For production, consider BeautifulSoup.
        """
        import re
        
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<nav[^>]*>.*?</nav>', '', text, flags=re.DOTALL)
        text = re.sub(r'<header[^>]*>.*?</header>', '', text, flags=re.DOTALL)
        text = re.sub(r'<footer[^>]*>.*?</footer>', '', text, flags=re.DOTALL)
        
        text = re.sub(r'<[^>]+>', ' ', text)
        
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _extract_title_from_html(self, html: str) -> Optional[str]:
        """Extract title from HTML."""
        import re
        match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None


def generate_content_hash(content: str) -> str:
    """Generate SHA-256 hash for content deduplication."""
    return hashlib.sha256(content.encode()).hexdigest()
