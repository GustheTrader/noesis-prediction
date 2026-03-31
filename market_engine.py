"""
NOESIS Prediction Market — Market Engine

Core market operations: create, predict, resolve, score.
"""

from datetime import datetime, timedelta
from typing import Optional
from models import (
    Market, MarketStatus, MarketCategory,
    Prediction, PredictionResult, Member
)


class MarketEngine:
    """
    Manages prediction markets for the Wrong Room Collective.
    """

    def __init__(self):
        self.markets: dict[str, Market] = {}
        self.predictions: dict[str, list[Prediction]] = {}  # market_id -> predictions
        self.results: list[PredictionResult] = []

    def create_market(
        self,
        question: str,
        category: MarketCategory = MarketCategory.REALITY_OS,
        description: str = "",
        created_by: str = "",
        closes_in_days: int = 30,
        tags: list = None,
    ) -> Market:
        """Create a new prediction market."""
        market = Market(
            question=question,
            description=description,
            category=category,
            created_by=created_by,
            closes_at=datetime.utcnow() + timedelta(days=closes_in_days),
            tags=tags or [],
        )
        self.markets[market.id] = market
        self.predictions[market.id] = []
        return market

    def submit_prediction(
        self,
        market_id: str,
        member_id: str,
        prediction: bool,
        confidence: float = 0.5,
        stake: float = 1.0,
        reasoning: str = "",
    ) -> Optional[Prediction]:
        """Submit a prediction on a market."""
        market = self.markets.get(market_id)
        if not market or market.status != MarketStatus.OPEN:
            return None

        pred = Prediction(
            market_id=market_id,
            member_id=member_id,
            prediction=prediction,
            confidence=confidence,
            stake=stake,
            reasoning=reasoning,
        )
        self.predictions[market_id].append(pred)

        # Update market prices based on predictions
        self._update_prices(market_id)

        return pred

    def resolve_market(self, market_id: str, outcome: bool) -> list[PredictionResult]:
        """Resolve a market and score all predictions."""
        market = self.markets.get(market_id)
        if not market:
            return []

        market.status = MarketStatus.RESOLVED
        market.outcome = outcome
        market.resolved_at = datetime.utcnow()

        results = []
        for pred in self.predictions.get(market_id, []):
            result = self._score_prediction(pred, outcome)
            results.append(result)
            self.results.append(result)

        return results

    def _score_prediction(self, pred: Prediction, outcome: bool) -> PredictionResult:
        """
        Score a prediction using calibration-based scoring.
        
        Score = (confidence if correct, 1-confidence if wrong) 
                - overconfidence penalty
        """
        correct = pred.prediction == outcome

        if correct:
            # Reward for being right, proportional to confidence
            score = pred.confidence
        else:
            # Penalize for being wrong, proportional to confidence
            score = -(pred.confidence)

        # Overconfidence penalty: very high confidence + wrong = bigger penalty
        if not correct and pred.confidence > 0.8:
            score -= (pred.confidence - 0.8) * 2

        return PredictionResult(
            prediction_id=pred.id,
            market_id=pred.market_id,
            member_id=pred.member_id,
            predicted=pred.prediction,
            actual=outcome,
            confidence=pred.confidence,
            score=round(score, 4),
            correct=correct,
        )

    def _update_prices(self, market_id: str):
        """Update market prices based on predictions."""
        preds = self.predictions.get(market_id, [])
        if not preds:
            return

        market = self.markets[market_id]
        yes_weighted = sum(p.confidence * p.stake for p in preds if p.prediction)
        no_weighted = sum(p.confidence * p.stake for p in preds if not p.prediction)
        total = yes_weighted + no_weighted

        if total > 0:
            market.yes_price = round(yes_weighted / total, 4)
            market.no_price = round(no_weighted / total, 4)

    def get_member_accuracy(self, member_id: str) -> dict:
        """Get a member's accuracy stats."""
        member_results = [r for r in self.results if r.member_id == member_id]
        if not member_results:
            return {"total": 0, "correct": 0, "accuracy": 0, "avg_confidence": 0}

        correct = sum(1 for r in member_results if r.correct)
        total = len(member_results)
        avg_confidence = sum(r.confidence for r in member_results) / total

        return {
            "total": total,
            "correct": correct,
            "accuracy": round(correct / total, 4) if total > 0 else 0,
            "avg_confidence": round(avg_confidence, 4),
        }

    def get_leaderboard(self, limit: int = 10) -> list[dict]:
        """Get the collective leaderboard."""
        member_scores: dict[str, dict] = {}

        for result in self.results:
            mid = result.member_id
            if mid not in member_scores:
                member_scores[mid] = {"member_id": mid, "total": 0, "correct": 0, "score_sum": 0}
            member_scores[mid]["total"] += 1
            if result.correct:
                member_scores[mid]["correct"] += 1
            member_scores[mid]["score_sum"] += result.score

        # Calculate accuracy and sort
        for mid in member_scores:
            s = member_scores[mid]
            s["accuracy"] = round(s["correct"] / s["total"], 4) if s["total"] > 0 else 0
            s["avg_score"] = round(s["score_sum"] / s["total"], 4) if s["total"] > 0 else 0

        sorted_members = sorted(
            member_scores.values(),
            key=lambda x: x["accuracy"],
            reverse=True,
        )

        return sorted_members[:limit]

    def get_open_markets(self) -> list[Market]:
        """Get all open markets."""
        return [m for m in self.markets.values() if m.status == MarketStatus.OPEN]

    def get_market_summary(self, market_id: str) -> dict:
        """Get summary of a market."""
        market = self.markets.get(market_id)
        if not market:
            return {}

        preds = self.predictions.get(market_id, [])
        return {
            "id": market.id,
            "question": market.question,
            "status": market.status.value,
            "category": market.category.value,
            "yes_price": market.yes_price,
            "no_price": market.no_price,
            "total_predictions": len(preds),
            "closes_at": market.closes_at.isoformat() if market.closes_at else None,
        }
