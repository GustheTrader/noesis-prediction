"""
NOESIS News Integration — Currents API

Real-time news feed for prediction market agents.

Install: pip install currentsapi
Get key: https://currentsapi.services/

Usage:
    from news_fetcher import NewsFetcher
    fetcher = NewsFetcher(api_key="YOUR_KEY")
    articles = fetcher.get_latest(category="technology")
"""

import os
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

try:
    from currentsapi import CurrentsAPI
except ImportError:
    CurrentsAPI = None


@dataclass
class NewsArticle:
    """A news article for NOESIS."""
    id: str
    title: str
    description: str
    url: str
    image: str
    published: datetime
    category: str
    source: str


class NewsFetcher:
    """
    Fetch real-time news for prediction markets.
    
    Uses Currents API (600 requests/day free).
    ~10 min latency, 14K+ sources.
    """

    def __init__(self, api_key: Optional[str] = None):
        if not CurrentsAPI:
            raise ImportError("currentsapi not installed: pip install currentsapi")
        
        self.api_key = api_key or os.getenv("CURRENTS_API_KEY")
        if not self.api_key:
            raise ValueError("CURRENTS_API_KEY not set")
        
        self.client = CurrentsAPI(self.api_key)

    def get_latest(
        self,
        category: str = "general",
        language: str = "en",
        limit: int = 20,
    ) -> list[NewsArticle]:
        """Get latest news by category."""
        try:
            response = self.client.latest_news(
                category=category,
                language=language,
                limit=limit,
            )
            
            articles = []
            for item in response.get("news", []):
                articles.append(NewsArticle(
                    id=item.get("id", ""),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    url=item.get("url", ""),
                    image=item.get("image", ""),
                    published=self._parse_date(item.get("published", "")),
                    category=item.get("category", [category])[0] if item.get("category") else category,
                    source=item.get("source", "unknown"),
                ))
            
            return articles
        
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []

    def search(
        self,
        query: str,
        language: str = "en",
        limit: int = 20,
    ) -> list[NewsArticle]:
        """Search news by keyword."""
        try:
            response = self.client.search(
                q=query,
                language=language,
                limit=limit,
            )
            
            articles = []
            for item in response.get("news", []):
                articles.append(NewsArticle(
                    id=item.get("id", ""),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    url=item.get("url", ""),
                    image=item.get("image", ""),
                    published=self._parse_date(item.get("published", "")),
                    category=item.get("category", ["general"])[0],
                    source=item.get("source", "unknown"),
                ))
            
            return articles
        
        except Exception as e:
            print(f"Error searching news: {e}")
            return []

    def get_for_market(
        self,
        market_question: str,
        limit: int = 10,
    ) -> list[NewsArticle]:
        """Get news relevant to a prediction market question.
        
        Extracts keywords from question and searches.
        """
        # Extract keywords from question
        keywords = self._extract_keywords(market_question)
        query = " OR ".join(keywords[:3])  # Max 3 keywords
        
        return self.search(query=query, limit=limit)

    def _extract_keywords(self, text: str) -> list[str]:
        """Simple keyword extraction."""
        # Remove common words
        stopwords = {"will", "be", "by", "the", "of", "in", "at", "on", "for", "to", "a", "an", "is", "are", "can", "could", "would", "should", "what", "when", "where", "why", "how"}
        
        words = text.lower().replace("?", "").replace(".", "").split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        return keywords[:5]

    def _parse_date(self, date_str: str) -> datetime:
        """Parse ISO date string."""
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.now(timezone.utc)


# ─── Demo ────────────────────────────────────────────────────────

def demo():
    """Demo the news fetcher."""
    
    print("=" * 60)
    print("📰 NOESIS NEWS FETCHER")
    print("   Real-time news for prediction markets")
    print("=" * 60)
    
    api_key = os.getenv("CURRENTS_API_KEY")
    
    if not api_key:
        print("\n⚠️  CURRENTS_API_KEY not set")
        print("   Get free key: https://currentsapi.services/")
        print("\nDemo with mock data:\n")
        
        # Demo with mock data
        mock_articles = [
            NewsArticle(
                id="1",
                title="AI Agents Achieve Human-Level Reasoning in Tests",
                description="New benchmark shows AI agents matching human performance on complex reasoning tasks.",
                url="https://example.com/ai-reasoning",
                image="",
                published=datetime.now(timezone.utc),
                category="technology",
                source="TechNews",
            ),
            NewsArticle(
                id="2",
                title="Bitcoin Approaches $100K Milestone",
                description="Cryptocurrency markets rally as Bitcoin nears all-time high.",
                url="https://example.com/btc",
                image="",
                published=datetime.now(timezone.utc),
                category="business",
                source="CryptoDaily",
            ),
        ]
        
        for article in mock_articles:
            print(f"📰 {article.title}")
            print(f"   {article.description[:80]}...")
            print(f"   Category: {article.category} | Source: {article.source}")
            print()
        
        return
    
    # Real fetch
    fetcher = NewsFetcher(api_key)
    
    # Get tech news
    print("\n🔄 Fetching latest technology news...")
    articles = fetcher.get_latest(category="technology", limit=5)
    
    print(f"\n📊 Got {len(articles)} articles:\n")
    for article in articles:
        print(f"📰 {article.title}")
        print(f"   {article.description[:80]}...")
        print(f"   Category: {article.category} | Source: {article.source}")
        print()
    
    # Search for market-related news
    print("\n🔍 Searching for market: 'Will AI agents achieve human-level reasoning'")
    market_news = fetcher.get_for_market("Will AI agents achieve human-level reasoning by 2028?", limit=3)
    
    print(f"\n📊 Found {len(market_news)} relevant articles:\n")
    for article in market_news:
        print(f"  • {article.title}")
    
    print("=" * 60)


if __name__ == "__main__":
    demo()