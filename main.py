"""
NOESIS Prediction Market — Demo

Demonstrates the sovereign prediction market for the Wrong Room Collective.
"""

from market_engine import MarketEngine
from models import MarketCategory


def demo():
    """Run a NOESIS demo."""

    print("=" * 60)
    print("🌅 NOESIS — Sovereign Prediction Market")
    print("   For the Wrong Room Collective")
    print("=" * 60)

    engine = MarketEngine()

    # Create members
    members = ["jeff", "sunset", "alice", "bob", "charlie"]

    # Create markets
    markets = [
        engine.create_market(
            question="Will AI agents achieve human-level reasoning by 2028?",
            category=MarketCategory.REALITY_OS,
            created_by="jeff",
            tags=["ai", "consciousness", "technology"],
        ),
        engine.create_market(
            question="Will Bitcoin exceed $200K by end of 2027?",
            category=MarketCategory.MACRO,
            created_by="alice",
            tags=["crypto", "macro"],
        ),
        engine.create_market(
            question="Will the Wrong Room Collective reach 100 members by Q4 2026?",
            category=MarketCategory.WRONG_ROOM,
            created_by="sunset",
            tags=["collective", "growth"],
        ),
    ]

    print(f"\n📊 Created {len(markets)} markets:")
    for m in markets:
        print(f"  • {m.question}")
        print(f"    Category: {m.category.value} | Closes: {m.closes_at.strftime('%Y-%m-%d')}")

    # Submit predictions
    print("\n🔮 Predictions submitted:")

    # Market 1: AI reasoning
    engine.submit_prediction(markets[0].id, "jeff", True, 0.7, reasoning="Agents evolving fast")
    engine.submit_prediction(markets[0].id, "sunset", True, 0.6, reasoning="Meta DGM-H shows path")
    engine.submit_prediction(markets[0].id, "alice", False, 0.55, reasoning="Hard problem still unsolved")
    engine.submit_prediction(markets[0].id, "bob", True, 0.8, reasoning="Exponential improvement")
    engine.submit_prediction(markets[0].id, "charlie", False, 0.4, reasoning="Consciousness is irreducible")

    # Market 2: Bitcoin
    engine.submit_prediction(markets[1].id, "jeff", True, 0.65, reasoning="Cycle analysis")
    engine.submit_prediction(markets[1].id, "bob", False, 0.5, reasoning="Regulatory headwinds")

    # Market 3: Collective growth
    engine.submit_prediction(markets[2].id, "sunset", True, 0.8, reasoning="The Wrong Room message resonates")
    engine.submit_prediction(markets[2].id, "jeff", True, 0.75, reasoning="Content + agents = growth")
    engine.submit_prediction(markets[2].id, "charlie", False, 0.6, reasoning="Niche market")

    for m in markets:
        preds = engine.predictions[m.id]
        print(f"\n  {m.question[:50]}...")
        for p in preds:
            direction = "YES" if p.prediction else "NO"
            print(f"    {p.member_id}: {direction} @ {p.confidence:.0%} confidence")

    # Show market prices
    print("\n📈 Current Market Prices:")
    for m in engine.markets.values():
        print(f"  {m.question[:40]}...")
        print(f"    YES: {m.yes_price:.0%} | NO: {m.no_price:.0%}")

    # Resolve a market
    print("\n✅ Resolving: Will the Wrong Room Collective reach 100 members?")
    results = engine.resolve_market(markets[2].id, outcome=True)  # Yes, they will!

    print("\n📊 Results:")
    for r in results:
        status = "✅ CORRECT" if r.correct else "❌ WRONG"
        print(f"  {r.member_id}: {status} | Score: {r.score:.2f}")

    # Leaderboard
    print("\n🏆 Leaderboard:")
    leaderboard = engine.get_leaderboard()
    for i, entry in enumerate(leaderboard, 1):
        print(f"  {i}. {entry['member_id']}: {entry['accuracy']:.0%} accuracy ({entry['total']} predictions)")

    print("\n" + "=" * 60)
    print("🌅 NOESIS — Where collective intelligence meets accountability.")
    print("   Every prediction sharpens the signal.")
    print("=" * 60)


if __name__ == "__main__":
    demo()
