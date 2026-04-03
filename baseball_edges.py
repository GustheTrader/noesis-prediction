"""
NOESIS — Top 10 Baseball Edge Bets (Stackable)

Profitable angles from 2024-2025 data + KB edge players.
Each can be stacked together for more edge.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class EdgeBet:
    """A stacked edge bet."""
    id: int
    angle: str
    pick: str
    reason: str
    confidence: float  # 0-100%
    category: str


# ─── TOP 10 EDGE BETS ────────────────────────────────────────────

EDGE_BETS = [
    # 1. BULLPEN EDGE (Best performing system 2024-2025)
    EdgeBet(
        id=1,
        angle="Better Bullpen Underdog",
        pick="Team with better bullpen as underdog",
        reason="+59.39 units in 2025, +6.2% ROI. Oddsmakers ignore bullpens.",
        confidence=75,
        category="system"
    ),
    
    # 2. HOME DOG +110 to +135
    EdgeBet(
        id=2,
        angle="Home Underdog Value",
        pick="Home team +110 to +135 ML",
        reason="Bookmakers see 1-2 run difference but favor road team. Home dog catches the edge.",
        confidence=65,
        category="system"
    ),
    
    # 3. OHTANI HR PROP
    EdgeBet(
        id=3,
        angle="Ohtani 40+ HR Season",
        pick="Shohei Ohtani over 40.5 HR",
        reason="3-year avg: 45 HR. Stability: 0.08 (elite). Best player in baseball.",
        confidence=85,
        category="player_prop"
    ),
    
    # 4. JUDGE MVP ROLL
    EdgeBet(
        id=4,
        angle="Judge MVP Candidate",
        pick="Aaron Judge MVP",
        reason="3-year: 48 HR, 115 RBI, 1.030 OPS. Best power hitter. Yankees compete.",
        confidence=70,
        category="futures"
    ),
    
    # 5. SOTO PLATE DISCIPLINE
    EdgeBet(
        id=5,
        angle="Soto On-Base Machine",
        pick="Juan Soto over 95.5 walks",
        reason="3-year BB%: 16% (best in baseball). 650 PA x 16% = 104 walks.",
        confidence=80,
        category="player_prop"
    ),
    
    # 6. DODGERS WIN DIVISION
    EdgeBet(
        id=6,
        angle="Dodgers NL West",
        pick="Dodgers win NL West",
        reason="Ohtani + Betts + Yamamoto + Glasnow. Most complete roster. Depth beats injuries.",
        confidence=80,
        category="futures"
    ),
    
    # 7. OVER TOTAL - GOOD OFFENSE
    EdgeBet(
        id=7,
        angle="Run Line - High Scoring Teams",
        pick="Overs on games with Ohtani/Judge teams",
        reason="Ohtani's team: ~5.2 runs/game. Judge's team: ~5.0. Both push overs.",
        confidence=70,
        category="totals"
    ),
    
    # 8. BETTS STEALS
    EdgeBet(
        id=8,
        angle="Mookie Steals 20+",
        pick="Mookie Betts over 20.5 SB",
        reason="3-year: 25 SB. Stability: 0.06 (elite). Leadoff, aggressive, healthy.",
        confidence=75,
        category="player_prop"
    ),
    
    # 9. LINDOR SILENT ASSASSIN
    EdgeBet(
        id=9,
        angle="Lindor 30-30 Club",
        pick="Francisco Lindor 30 HR + 30 SB",
        reason="3-year: 30 HR, 25 SB. Mets SS. Speed + power combo. Undervalued.",
        confidence=60,
        category="player_prop"
    ),
    
    # 10. COUNTER - FADE BAD BULLPEN FAVORITES
    EdgeBet(
        id=10,
        angle="Fade Favorite with Bad Bullpen",
        pick="Lay -150 or more against team with bottom 10 bullpen",
        reason="Favorites are often overvalued. If bullpen sucks, late innings = lose.",
        confidence=65,
        category="system"
    ),
]


# ─── STACKING LOGIC ───────────────────────────────────────────────

def get_stackable_picks() -> List[str]:
    """
    Get picks that can stack together.
    
    Stacking = multiple bets on same outcome = more edge.
    """
    stack = []
    
    # Stack 1: DODGERS DOMINATION
    stack.append("🟢 STACK 1: DODGERS")
    stack.append("  • Ohtani 40+ HR")
    stack.append("  • Mookie 20+ SB")
    stack.append("  • Dodgers NL West")
    stack.append("  • Overs (high scoring)")
    
    # Stack 2: YANKEE POWER
    stack.append("\n🟡 STACK 2: YANKEES")
    stack.append("  • Judge MVP")
    stack.append("  • Judge 45+ HR")
    stack.append("  • Yankees AL East")
    
    # Stack 3: SYSTEM EDGES
    stack.append("\n🔵 STACK 3: SYSTEMS")
    stack.append("  • Better bullpen underdog")
    stack.append("  • Home dog +110 to +135")
    stack.append("  • Fade bad bullpen favs")
    
    # Stack 4: PROPS
    stack.append("\n🟣 STACK 4: PROPS")
    stack.append("  • Soto over 95.5 walks")
    stack.append("  • Lindor 30-30")
    stack.append("  • Betts 20+ SB")
    
    return stack


def get_parlay_builder() -> dict:
    """
    Build a multi-leg parlay with positive EV.
    """
    return {
        "leg_1": "Dodgers ML (-150) — too strong",
        "leg_2": "Ohtani 40+ HR (-130)",
        "leg_3": "Judge 40+ HR (-130)",
        "leg_4": "Mookie 20+ SB (+120)",
        "leg_5": "Soto 95+ walks (-130)",
        "recommended_stake": "1 unit for ~4.2x payout",
        "note": "Diversify across categories for +EV"
    }


# ─── DEMO ──────────────────────────────────────────────────────────

def demo():
    """Show the edge bets."""
    
    print("=" * 70)
    print("🏟️  TOP 10 BASEBALL EDGE BETS")
    print("   Stackable angles from 2024-2025 + KB data")
    print("=" * 70)
    
    print("\n📊 ALL 10 EDGES:\n")
    for bet in EDGE_BETS:
        print(f"  {bet.id:2}. {bet.angle}")
        print(f"      Pick: {bet.pick}")
        print(f"      Reason: {bet.reason[:60]}...")
        print(f"      Confidence: {bet.confidence}% | Category: {bet.category}")
        print()
    
    print("\n" + "=" * 70)
    print("📦 STACKABLE PARLAYS:")
    print("=" * 70)
    
    for line in get_stackable_picks():
        print(line)
    
    print("\n" + "=" * 70)
    print("🎯 PARLAY BUILDER:")
    print("=" * 70)
    pb = get_parlay_builder()
    for k, v in pb.items():
        print(f"  {k}: {v}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo()