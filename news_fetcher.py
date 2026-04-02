"""
NOESIS News Integration — Currents API

Real-time news feed for prediction market agents.

Install: pip install currentsapi
Get key: https://currentsapi.services/

Usage:
    from news_fetcher import NewsFetcher
    fetcher = NewsFetcher(api_key="YOUR_KEY")
    articles = fetcher.get_latest(limit=20)
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
    
    Uses Currents API (1000 requests/day free).
    ~10 min latency, 120K+ sources.
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
        category: Optional[str] = None,
        language: str = "en",
        limit: int = 20,
    ) -> list[NewsArticle]:
        """Get latest news, optionally filtered by category.
        
        Note: API returns all news, filtering happens client-side.
        """
        try:
            response = self.client.latest_news()
            
            articles = []
            for item in response.get("news", []):
                # Filter by language if specified
                if language and item.get("language") != language:
                    continue
                
                # Filter by category if specified
                item_cats = item.get("category", [])
                if category and category not in item_cats:
                    continue
                
                articles.append(NewsArticle(
                    id=item.get("id", ""),
                    title=item.get("title", ""),
                    description=item.get("description", ""),
                    url=item.get("url", ""),
                    image=item.get("image", ""),
                    published=self._parse_date(item.get("published", "")),
                    category=item_cats[0] if item_cats else "general",
                    source=item.get("source", "unknown"),
                ))
                
                if len(articles) >= limit:
                    break
            
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
            response = self.client.search()
            
            # Filter results client-side for query
            articles = []
            for item in response.get("news", []):
                title = item.get("title", "").lower()
                desc = item.get("description", "").lower()
                
                if query.lower() in title or query.lower() in desc:
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
                    
                    if len(articles) >= limit:
                        break
            
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
        # Get all latest and filter client-side
        keywords = self._extract_keywords(market_question)
        
        try:
            response = self.client.latest_news()
            
            articles = []
            for item in response.get("news", []):
                title = item.get("title", "").lower()
                desc = item.get("description", "").lower()
                
                # Check if any keyword matches
                for kw in keywords:
                    if kw in title or kw in desc:
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
                        break  # Only add once
                
                if len(articles) >= limit:
                    break
            
            return articles
        
        except Exception as e:
            print(f"Error getting market news: {e}")
            return []

    def _extract_keywords(self, text: str) -> list[str]:
        """Simple keyword extraction."""
        # Remove common words
        stopwords = {"will", "be", "by", "the", "of", "in", "at", "on", "for", "to", "a", "an", "is", "are", "can", "could", "would", "should", "what", "when", "where", "why", "how", "this", "that", "with", "from"}
        
        words = text.lower().replace("?", "").replace(".", "").replace(",", "").split()
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
        return
    
    # Real fetch
    fetcher = NewsFetcher(api_key)
    
    # Get latest news
    print("\n🔄 Fetching latest news...")
    articles = fetcher.get_latest(limit=10)
    
    print(f"\n📊 Got {len(articles)} articles:\n")
    for article in articles:
        print(f"📰 {article.title[:70]}")
        print(f"   {article.description[:80] if article.description else 'No description'}...")
        print(f"   Category: {article.category} | Source: {article.source}")
        print()
    
    # Search for market-related news
    print("\n🔍 Searching for market: 'AI agents achieve human-level reasoning'")
    market_news = fetcher.get_for_market("Will AI agents achieve human-level reasoning by 2028?", limit=5)
    
    print(f"\n📊 Found {len(market_news)} relevant articles:")
    for article in market_news:
        print(f"  • {article.title[:60]}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo()