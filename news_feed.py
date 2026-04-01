"""
Sovereign OS — News Feed

Fast ground truth news for the pipeline and for Jeff.
Pulls from multiple sources, deduplicates, feeds into NOESIS.

Sources:
- GNews API (free, 100 req/day)
- The News API (free, unlimited)
- NewsData.io (free tier)
- RSS feeds (direct, no API needed)
- Web search (Brave API)
"""

import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class NewsItem:
    """A news article."""
    title: str
    description: str
    source: str
    url: str
    published: str = ""
    category: str = ""
    tags: list = field(default_factory=list)
    hash: str = ""  # For deduplication

    def __post_init__(self):
        if not self.hash:
            self.hash = hashlib.md5(self.title.encode()).hexdigest()[:12]


class NewsFeed:
    """
    Aggregated news feed from multiple sources.
    
    Features:
    - Multiple sources (APIs, RSS, web search)
    - Deduplication
    - Category tagging
    - Direct feed into NOESIS pipeline
    """

    def __init__(self):
        self.seen_hashes: set = set()
        self.articles: list[NewsItem] = []

    def fetch_gnews(self, api_key: str, query: str = "AI agents", max_results: int = 10) -> list[NewsItem]:
        """Fetch from GNews API."""
        try:
            import httpx
            resp = httpx.get(
                "https://gnews.io/api/v4/search",
                params={
                    "q": query,
                    "lang": "en",
                    "max": max_results,
                    "apikey": api_key,
                },
                timeout=10,
            )
            data = resp.json()
            articles = []

            for item in data.get("articles", []):
                article = NewsItem(
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    source=item.get("source", {}).get("name", "GNews"),
                    url=item.get("url", ""),
                    published=item.get("publishedAt", ""),
                    tags=[query],
                )
                if article.hash not in self.seen_hashes:
                    articles.append(article)
                    self.seen_hashes.add(article.hash)

            return articles
        except Exception as e:
            print(f"GNews error: {e}")
            return []

    def fetch_thenewsapi(self, api_key: str, query: str = "", limit: int = 10) -> list[NewsItem]:
        """Fetch from The News API (free)."""
        try:
            import httpx
            params = {"api_token": api_key, "language": "en", "limit": limit}
            if query:
                params["search"] = query

            resp = httpx.get(
                "https://api.thenewsapi.com/v1/news/top",
                params=params,
                timeout=10,
            )
            data = resp.json()
            articles = []

            for item in data.get("data", []):
                article = NewsItem(
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    source=item.get("source", "TheNewsAPI"),
                    url=item.get("url", ""),
                    published=item.get("published_at", ""),
                    tags=[query] if query else [],
                )
                if article.hash not in self.seen_hashes:
                    articles.append(article)
                    self.seen_hashes.add(article.hash)

            return articles
        except Exception as e:
            print(f"TheNewsAPI error: {e}")
            return []

    def fetch_rss(self, feed_url: str, limit: int = 10) -> list[NewsItem]:
        """Fetch from RSS feed (no API key needed)."""
        try:
            import httpx
            import xml.etree.ElementTree as ET

            resp = httpx.get(feed_url, timeout=10)
            root = ET.fromstring(resp.content)

            articles = []
            items = root.findall(".//item")[:limit]

            for item in items:
                title = item.find("title")
                desc = item.find("description")
                link = item.find("link")
                pub_date = item.find("pubDate")

                article = NewsItem(
                    title=title.text if title is not None else "",
                    description=desc.text if desc is not None else "",
                    source="RSS",
                    url=link.text if link is not None else "",
                    published=pub_date.text if pub_date is not None else "",
                )
                if article.hash not in self.seen_hashes:
                    articles.append(article)
                    self.seen_hashes.add(article.hash)

            return articles
        except Exception as e:
            print(f"RSS error: {e}")
            return []

    def fetch_brave(self, query: str, count: int = 5) -> list[NewsItem]:
        """Fetch from Brave Search (uses OpenClaw's web_search)."""
        # This would use the web_search tool in production
        # For now, return placeholder
        return []

    def fetch_all(self, config: dict = None) -> list[NewsItem]:
        """Fetch from all configured sources."""
        config = config or {}
        all_articles = []

        # GNews
        if config.get("gnews_key"):
            for query in config.get("queries", ["AI agents", "crypto", "prediction markets"]):
                articles = self.fetch_gnews(config["gnews_key"], query)
                all_articles.extend(articles)

        # The News API
        if config.get("thenews_key"):
            articles = self.fetch_thenewsapi(config["thenews_key"])
            all_articles.extend(articles)

        # RSS feeds
        for feed_url in config.get("rss_feeds", []):
            articles = self.fetch_rss(feed_url)
            all_articles.extend(articles)

        # Store
        self.articles.extend(all_articles)

        return all_articles

    def get_latest(self, limit: int = 20) -> list[NewsItem]:
        """Get latest articles."""
        return sorted(
            self.articles,
            key=lambda a: a.published,
            reverse=True,
        )[:limit]

    def get_by_tag(self, tag: str) -> list[NewsItem]:
        """Get articles by tag."""
        return [a for a in self.articles if tag in a.tags]

    def to_pipeline_format(self, articles: list[NewsItem] = None) -> list[dict]:
        """
        Convert articles to pipeline-compatible format.
        
        Creates market suggestions from news articles.
        """
        articles = articles or self.articles
        pipeline_data = []

        for article in articles:
            # Generate market question from article
            question = self._article_to_question(article)
            if question:
                pipeline_data.append({
                    "question": question,
                    "description": article.description[:200],
                    "source": article.source,
                    "tags": article.tags,
                    "url": article.url,
                })

        return pipeline_data

    def _article_to_question(self, article: NewsItem) -> str:
        """Convert a news article to a prediction market question."""
        title = article.title.lower()

        # Pattern matching for question generation
        if "will" in title or "could" in title or "may" in title:
            # Already has prediction language
            return f"{article.title}?"

        if "launch" in title or "release" in title or "announce" in title:
            return f"Will {article.title}?"

        if "record" in title or "high" in title or "break" in title:
            return f"Will {article.title} continue?"

        if "crash" in title or "drop" in title or "fall" in title:
            return f"Will {article.title} recover?"

        # Default: wrap in question
        if len(article.title) > 15:
            return f"Will '{article.title}' have significant impact by Q2 2026?"

        return ""

    def get_feed_status(self) -> dict:
        """Feed status."""
        return {
            "total_articles": len(self.articles),
            "unique_hashes": len(self.seen_hashes),
            "sources": list(set(a.source for a in self.articles)),
            "latest": self.articles[-1].title if self.articles else None,
        }


# ─── RSS Feeds for Ground Truth ────────────────────────────────

DEFAULT_RSS_FEEDS = {
    "tech": [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://feeds.arstechnica.com/arstechnica/index",
    ],
    "crypto": [
        "https://cointelegraph.com/rss",
        "https://coindesk.com/arc/outboundfeeds/rss/",
    ],
    "ai": [
        "https://machinelearningmastery.com/feed/",
    ],
    "finance": [
        "https://www.ft.com/rss/home",
    ],
}

# ─── Quick Setup ───────────────────────────────────────────────

def create_news_feed(
    gnews_key: str = "",
    thenews_key: str = "",
    rss_categories: list = None,
) -> NewsFeed:
    """Create a pre-configured news feed."""
    feed = NewsFeed()

    # Add RSS feeds
    categories = rss_categories or ["tech", "crypto", "ai"]
    for cat in categories:
        for url in DEFAULT_RSS_FEEDS.get(cat, []):
            articles = feed.fetch_rss(url)
            feed.articles.extend(articles)

    return feed
