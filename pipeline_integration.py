"""
Sovereign OS — 5-Layer Pipeline → NOESIS Integration

Connects the 5-layer graph (5layergraphKB) to the NOESIS prediction market.
The pipeline becomes the intelligence engine that feeds the market.

Flow:
    INGEST → GATES → FILTERS → AGENTS → EXECUTION → NOESIS
                                                         ↓
                                                     Leaderboard
                                                     Market prices
                                                     Scores
"""

import sys
import json
import time
from pathlib import Path
from typing import Optional

# Import from noesis-prediction
from market_engine import MarketEngine
from models import Market, MarketStatus, MarketCategory, Prediction, PredictionResult

# Import from 5layergraphKB (will be copied/linked)
# In production, these would be proper imports
sys.path.insert(0, str(Path(__file__).parent.parent / "copy-bot"))


class PipelineIntegration:
    """
    Integrates the 5-layer pipeline with NOESIS.
    
    The pipeline:
    1. INGESTS data (markets, signals, external data)
    2. GATES qualify which signals are viable
    3. FILTERS score and rank signals
    4. AGENTS submit predictions based on signals
    5. EXECUTION resolves markets and updates scores
    """

    def __init__(self, engine: MarketEngine):
        self.engine = engine
        self.pipeline_log: list[dict] = []

    # ─── Layer 1: INGEST ──────────────────────────────────────

    def ingest_external_markets(self, external_data: list[dict]) -> list[dict]:
        """
        Layer 1: Ingest external market data.
        
        Sources: Polymarket, Kalshi, or custom data feeds.
        Creates NOESIS markets from external signals.
        """
        ingested = []

        for data in external_data:
            # Check if market already exists
            existing = self._find_similar_market(data.get("question", ""))
            if existing:
                self._log("ingest", f"Market exists: {existing.question[:50]}")
                continue

            # Create new market
            market = self.engine.create_market(
                question=data.get("question", ""),
                category=self._categorize(data),
                description=data.get("description", ""),
                created_by="pipeline",
                tags=data.get("tags", []),
            )

            ingested.append({
                "market_id": market.id,
                "question": market.question,
                "source": data.get("source", "external"),
            })

            self._log("ingest", f"Created: {market.question[:50]}")

        return ingested

    # ─── Layer 2: GATES ──────────────────────────────────────

    def gate_markets(self, markets: list[dict], min_volume: float = 0) -> list[dict]:
        """
        Layer 2: Gate qualification.
        
        Check if markets are viable:
        - Has enough signal (volume, predictions)
        - Is resolvable (clear outcome)
        - Is timely (not expired)
        """
        passed = []

        for m in markets:
            market = self.engine.markets.get(m.get("market_id", ""))
            if not market:
                continue

            # Gate checks
            checks = {
                "resolvable": self._is_resolvable(market),
                "timely": self._is_timely(market),
                "clear_question": len(market.question) > 10,
            }

            if all(checks.values()):
                passed.append(m)
                self._log("gates", f"PASS: {market.question[:50]}")
            else:
                failed = [k for k, v in checks.items() if not v]
                self._log("gates", f"FAIL: {market.question[:50]} — {', '.join(failed)}")

        return passed

    # ─── Layer 3: FILTERS ─────────────────────────────────────

    def filter_markets(self, markets: list[dict]) -> list[dict]:
        """
        Layer 3: Filter and score.
        
        Score markets by:
        - Relevance to collective interests
        - Resolvability
        - Engagement potential
        """
        scored = []

        for m in markets:
            market = self.engine.markets.get(m.get("market_id", ""))
            if not market:
                continue

            score = self._score_market(market)
            m["score"] = score
            scored.append(m)

            self._log("filters", f"Scored: {market.question[:50]} = {score:.2f}")

        # Sort by score descending
        scored.sort(key=lambda x: x.get("score", 0), reverse=True)

        return scored

    # ─── Layer 4: AGENTS ──────────────────────────────────────

    def agent_predictions(self, markets: list[dict], agents: list = None) -> list[dict]:
        """
        Layer 4: Agents submit predictions.
        
        Each agent evaluates markets and submits predictions
        based on their domain expertise and curiosity.
        """
        predictions = []

        for m in markets:
            market = self.engine.markets.get(m.get("market_id", ""))
            if not market:
                continue

            if agents:
                for agent in agents:
                    pred = self._agent_evaluate(agent, market)
                    if pred:
                        predictions.append(pred)
            else:
                # Auto-generate predictions based on market sentiment
                pred = self._auto_predict(market, m.get("score", 0.5))
                if pred:
                    predictions.append(pred)

            self._log("agents", f"Predictions for: {market.question[:50]}")

        return predictions

    # ─── Layer 5: EXECUTION ───────────────────────────────────

    def execute_resolution(self, market_id: str, outcome: bool) -> list[PredictionResult]:
        """
        Layer 5: Resolve market and score predictions.
        
        Updates:
        - Market status
        - Member scores
        - Leaderboard
        """
        results = self.engine.resolve_market(market_id, outcome)

        for r in results:
            self._log("execution", f"{'✅' if r.correct else '❌'} {r.member_id}: score={r.score:.2f}")

        return results

    # ─── Full Pipeline Run ────────────────────────────────────

    def run_pipeline(
        self,
        external_data: list[dict],
        agents: list = None,
        auto_resolve: bool = False,
    ) -> dict:
        """
        Run the full 5-layer pipeline.
        
        Returns complete results including:
        - Markets created
        - Markets gated
        - Markets filtered
        - Predictions submitted
        - Resolutions (if auto_resolve)
        """
        self.pipeline_log = []

        # Layer 1: Ingest
        ingested = self.ingest_external_markets(external_data)

        # Layer 2: Gate
        gated = self.gate_markets(ingested)

        # Layer 3: Filter
        filtered = self.filter_markets(gated)

        # Layer 4: Agents
        predictions = self.agent_predictions(filtered, agents)

        # Layer 5: Execution (optional auto-resolve)
        resolutions = []
        if auto_resolve:
            for m in filtered:
                market = self.engine.markets.get(m.get("market_id", ""))
                if market and market.outcome is not None:
                    results = self.execute_resolution(market.id, market.outcome)
                    resolutions.extend(results)

        return {
            "ingested": len(ingested),
            "gated": len(gated),
            "filtered": len(filtered),
            "predictions": len(predictions),
            "resolutions": len(resolutions),
            "pipeline_log": self.pipeline_log,
            "markets": [
                self.engine.get_market_summary(m.get("market_id", ""))
                for m in filtered
            ],
        }

    # ─── Helpers ──────────────────────────────────────────────

    def _find_similar_market(self, question: str) -> Optional[Market]:
        """Find existing market with similar question."""
        for market in self.engine.markets.values():
            if market.question.lower()[:30] == question.lower()[:30]:
                return market
        return None

    def _categorize(self, data: dict) -> MarketCategory:
        """Categorize market based on content."""
        tags = data.get("tags", [])
        question = data.get("question", "").lower()

        if any(t in tags for t in ["crypto", "bitcoin", "eth"]):
            return MarketCategory.MACRO
        elif any(t in tags for t in ["ai", "agent", "consciousness"]):
            return MarketCategory.REALITY_OS
        elif any(t in tags for t in ["collective", "wrong room"]):
            return MarketCategory.WRONG_ROOM
        else:
            return MarketCategory.PERSONAL

    def _is_resolvable(self, market: Market) -> bool:
        """Check if market has a clear, resolvable outcome."""
        # Must have a yes/no question
        question = market.question.lower()
        return any(w in question for w in ["will", "can", "does", "is", "are"])

    def _is_timely(self, market: Market) -> bool:
        """Check if market hasn't expired."""
        if not market.closes_at:
            return True
        return market.closes_at.timestamp() > time.time()

    def _score_market(self, market: Market) -> float:
        """Score a market by relevance and engagement potential."""
        score = 0.5  # Base score

        # Category bonus
        if market.category == MarketCategory.REALITY_OS:
            score += 0.2
        elif market.category == MarketCategory.WRONG_ROOM:
            score += 0.15

        # Engagement bonus
        if market.total_volume > 1000:
            score += 0.1

        # Recency bonus
        if market.closes_at:
            days_until_close = (market.closes_at.timestamp() - time.time()) / 86400
            if 7 < days_until_close < 60:
                score += 0.1  # Sweet spot: not too soon, not too far

        return min(1.0, score)

    def _agent_evaluate(self, agent, market: Market) -> Optional[dict]:
        """Have an agent evaluate a market."""
        # In production, would use agent.decide() and agent.execute()
        # For now, simplified version
        if agent.state.domain in market.question.lower():
            return {
                "agent": agent.state.name,
                "market_id": market.id,
                "prediction": True,
                "confidence": 0.65,
                "reasoning": f"Domain expertise in {agent.state.domain}",
            }
        return None

    def _auto_predict(self, market: Market, score: float) -> Optional[dict]:
        """Auto-generate prediction based on market sentiment."""
        if market.yes_price > 0.6:
            return {
                "agent": "pipeline-auto",
                "market_id": market.id,
                "prediction": True,
                "confidence": market.yes_price,
                "reasoning": f"Market sentiment: {market.yes_price:.0%} YES",
            }
        return None

    def _log(self, layer: str, message: str):
        """Log pipeline activity."""
        self.pipeline_log.append({
            "layer": layer,
            "message": message,
            "timestamp": time.time(),
        })


class NOESISWithPipeline:
    """
    NOESIS prediction market powered by the 5-layer pipeline.
    
    This is the INTEGRATED version:
    - Pipeline ingests, gates, filters, agents, executes
    - NOESIS provides the market infrastructure
    - ATA mesh provides agent communication
    - Encrypted gateway provides security
    """

    def __init__(self):
        self.engine = MarketEngine()
        self.pipeline = PipelineIntegration(self.engine)

    def ingest_and_predict(self, data: list[dict]) -> dict:
        """One-call pipeline: ingest → predict."""
        return self.pipeline.run_pipeline(data, auto_resolve=False)

    def get_intelligence(self) -> dict:
        """Get collective intelligence summary."""
        return {
            "open_markets": len(self.engine.get_open_markets()),
            "total_predictions": sum(
                len(preds) for preds in self.engine.predictions.values()
            ),
            "leaderboard": self.engine.get_leaderboard(),
            "pipeline_log": self.pipeline.pipeline_log[-10:],  # Last 10
        }
