"""
Sovereign OS — Smart Router

Intelligent query router for structured + unstructured data.

Routes queries to the right backend:
- Structured (PostgreSQL) → exact lookups, aggregations, joins
- Unstructured (Qdrant) → semantic search, similarity, embeddings
- Hybrid → both, merge results

The router DECIDES where to send each query based on intent.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class QueryType(Enum):
    """Types of queries the router can handle."""
    STRUCTURED = "structured"      # SQL-like, exact data
    SEMANTIC = "semantic"          # Natural language, similarity
    HYBRID = "hybrid"             # Both structured + semantic
    AGGREGATION = "aggregation"   # Counts, sums, averages
    LOOKUP = "lookup"             # Exact ID/key lookup
    SEARCH = "search"             # Free-text search
    MULTIMODAL = "multimodal"     # Text + image


@dataclass
class RouteDecision:
    """A routing decision."""
    query_type: QueryType
    backend: str  # "postgres", "qdrant", "both"
    confidence: float
    reason: str
    optimized_query: str = ""


class SmartRouter:
    """
    Intelligent query router for Sovereign OS.
    
    Analyzes incoming queries and routes to the right backend:
    
    STRUCTURED (PostgreSQL):
    - "How many markets are open?"
    - "What's jeff's SVRGN balance?"
    - "Show leaderboard top 10"
    - "Get predictions for market X"
    
    SEMANTIC (Qdrant):
    - "What do I know about quantum computing?"
    - "Find similar insights to this article"
    - "What's related to covered calls?"
    - "Search my memory for anything about Tesla"
    
    HYBRID (Both):
    - "What markets are related to AI agents?"
    - "Show me predictions that match my interests"
    - "Find experts in quantum computing"
    """

    def __init__(self):
        # Patterns that indicate structured queries
        self.structured_patterns = [
            r"how many",
            r"count",
            r"total",
            r"sum",
            r"average",
            r"list all",
            r"show all",
            r"get all",
            r"balance",
            r"score",
            r"leaderboard",
            r"status",
            r"open markets",
            r"closed markets",
            r"member",
            r"prediction",
            r"transaction",
            r"top \d+",
            r"last \d+",
            r"between .* and",
            r"since",
            r"before",
            r"after",
            r"greater than",
            r"less than",
            r"equal to",
            r"where .* =",
            r"order by",
            r"group by",
        ]

        # Patterns that indicate semantic queries
        self.semantic_patterns = [
            r"what do i know",
            r"what did i learn",
            r"similar to",
            r"related to",
            r"find.*about",
            r"search.*for",
            r"what.*think",
            r"insight",
            r"memory",
            r"remember",
            r"recall",
            r"concept",
            r"idea",
            r"meaning",
            r"understand",
            r"explain",
            r"why",
            r"how does",
            r"what is the connection",
            r"pattern",
            r"theme",
        ]

        # Patterns that indicate hybrid queries
        self.hybrid_patterns = [
            r"market.*about",
            r"prediction.*related",
            r"expert.*in",
            r"who.*knows",
            r"best.*strategy",
            r"similar.*market",
            r"find.*member",
            r"agent.*expertise",
        ]

        # Patterns that indicate multimodal
        self.multimodal_patterns = [
            r"image",
            r"chart",
            r"graph",
            r"photo",
            r"screenshot",
            r"diagram",
            r"visual",
        ]

    def route(self, query: str, has_image: bool = False) -> RouteDecision:
        """
        Route a query to the appropriate backend.
        
        Returns a RouteDecision with:
        - query_type: what kind of query this is
        - backend: where to send it
        - confidence: how sure we are
        - reason: why we chose this route
        """
        query_lower = query.lower().strip()

        # Check for multimodal
        if has_image or any(re.search(p, query_lower) for p in self.multimodal_patterns):
            return RouteDecision(
                query_type=QueryType.MULTIMODAL,
                backend="qdrant",
                confidence=0.95,
                reason="Multimodal content requires vector search",
                optimized_query=query,
            )

        # Score each category
        structured_score = self._score_patterns(query_lower, self.structured_patterns)
        semantic_score = self._score_patterns(query_lower, self.semantic_patterns)
        hybrid_score = self._score_patterns(query_lower, self.hybrid_patterns)

        # Check for exact lookups (ID, name, specific key)
        if self._is_exact_lookup(query_lower):
            return RouteDecision(
                query_type=QueryType.LOOKUP,
                backend="postgres",
                confidence=0.95,
                reason="Exact lookup — use structured DB",
                optimized_query=self._optimize_structured(query),
            )

        # Check for aggregations
        if self._is_aggregation(query_lower):
            return RouteDecision(
                query_type=QueryType.AGGREGATION,
                backend="postgres",
                confidence=0.95,
                reason="Aggregation — use structured DB",
                optimized_query=self._optimize_structured(query),
            )

        # Hybrid wins if both structured and semantic match
        if hybrid_score > 0.5 and structured_score > 0.3 and semantic_score > 0.3:
            return RouteDecision(
                query_type=QueryType.HYBRID,
                backend="both",
                confidence=0.85,
                reason="Hybrid query — needs both structured and semantic",
                optimized_query=query,
            )

        # Structured wins
        if structured_score > semantic_score and structured_score > 0.3:
            return RouteDecision(
                query_type=QueryType.STRUCTURED,
                backend="postgres",
                confidence=min(0.95, structured_score),
                reason=f"Structured query (score: {structured_score:.2f})",
                optimized_query=self._optimize_structured(query),
            )

        # Semantic wins
        if semantic_score > structured_score and semantic_score > 0.3:
            return RouteDecision(
                query_type=QueryType.SEMANTIC,
                backend="qdrant",
                confidence=min(0.95, semantic_score),
                reason=f"Semantic query (score: {semantic_score:.2f})",
                optimized_query=query,
            )

        # Default to semantic (natural language questions)
        return RouteDecision(
            query_type=QueryType.SEMANTIC,
            backend="qdrant",
            confidence=0.6,
            reason="Default to semantic search for natural language",
            optimized_query=query,
        )

    def _score_patterns(self, query: str, patterns: list[str]) -> float:
        """Score how many patterns match."""
        matches = sum(1 for p in patterns if re.search(p, query))
        return min(1.0, matches / 3)  # Normalize to 0-1

    def _is_exact_lookup(self, query: str) -> bool:
        """Check if this is an exact lookup."""
        indicators = [
            r"^get .+ by id",
            r"^find .+ where",
            r"^show me .+ id",
            r"^market [a-f0-9-]+$",
            r"^member .+$",
            r"^agent .+$",
        ]
        return any(re.search(p, query) for p in indicators)

    def _is_aggregation(self, query: str) -> bool:
        """Check if this is an aggregation query."""
        indicators = [
            r"how many",
            r"count of",
            r"total",
            r"sum of",
            r"average",
            r"mean",
            r"maximum",
            r"minimum",
            r"top \d+",
            r"bottom \d+",
        ]
        return any(re.search(p, query) for p in indicators)

    def _optimize_structured(self, query: str) -> str:
        """Optimize query for structured DB."""
        query_lower = query.lower()

        # Map natural language to SQL hints
        if "open" in query_lower and "market" in query_lower:
            return "SELECT * FROM markets WHERE status = 'open'"
        if "leaderboard" in query_lower:
            return "SELECT * FROM members ORDER BY reputation_score DESC LIMIT 10"
        if "balance" in query_lower:
            return "SELECT name, svrgn_balance, svrgny_balance FROM members"
        if "prediction" in query_lower:
            return "SELECT * FROM predictions ORDER BY created_at DESC"

        return query


class QueryExecutor:
    """
    Executes routed queries against the appropriate backend.
    
    Uses SmartRouter to decide where to send each query,
    then executes and returns unified results.
    """

    def __init__(self, structured_db, vector_memory, router: SmartRouter = None):
        self.structured = structured_db
        self.vector = vector_memory
        self.router = router or SmartRouter()

    def execute(self, query: str, has_image: bool = False, limit: int = 10) -> dict:
        """
        Execute a query with automatic routing.
        
        Returns:
        - route: the routing decision
        - results: the query results
        - source: which backend(s) were used
        """
        route = self.router.route(query, has_image)

        results = {
            "query": query,
            "route": {
                "type": route.query_type.value,
                "backend": route.backend,
                "confidence": route.confidence,
                "reason": route.reason,
            },
            "results": [],
            "source": route.backend,
        }

        if route.backend == "postgres":
            results["results"] = self._execute_structured(route.optimized_query, limit)
        elif route.backend == "qdrant":
            results["results"] = self._execute_semantic(query, limit)
        elif route.backend == "both":
            structured_results = self._execute_structured(route.optimized_query, limit)
            semantic_results = self._execute_semantic(query, limit)
            results["results"] = self._merge_results(structured_results, semantic_results)

        return results

    def _execute_structured(self, query: str, limit: int) -> list[dict]:
        """Execute against PostgreSQL."""
        # In production, would use asyncpg
        # For now, return placeholder
        return [{"source": "postgres", "query": query, "rows": []}]

    def _execute_semantic(self, query: str, limit: int) -> list[dict]:
        """Execute against Qdrant."""
        return self.vector.search(query, limit)

    def _merge_results(self, structured: list, semantic: list) -> list[dict]:
        """Merge results from both backends."""
        merged = []
        for r in structured:
            merged.append({"type": "structured", "data": r})
        for r in semantic:
            merged.append({"type": "semantic", "data": r})
        return merged


# ─── Demo ───────────────────────────────────────────────────────

def demo():
    """Demo the smart router."""
    router = SmartRouter()

    queries = [
        "How many markets are open?",
        "What do I know about quantum computing?",
        "Show leaderboard top 10",
        "Find insights similar to covered calls",
        "Get member jeff's balance",
        "What markets are related to AI agents?",
        "Search memory for Tesla",
        "Count total predictions",
        "What's the best strategy for crypto?",
        "How does dopamine affect curiosity?",
    ]

    print("=" * 60)
    print("🌅 SMART ROUTER — Query Analysis")
    print("=" * 60)

    for q in queries:
        route = router.route(q)
        print(f"\n📝 \"{q}\"")
        print(f"   → {route.query_type.value.upper()}")
        print(f"   → {route.backend}")
        print(f"   → confidence: {route.confidence:.0%}")
        print(f"   → {route.reason}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo()
