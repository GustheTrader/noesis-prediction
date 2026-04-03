"""
NOESIS — F5 (First 5 Innings) Edge Bets

Single game pitcher and runs edges.
Focus on first 5 innings only - avoid bullpen chaos.
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timezone


@dataclass
class F5EdgeBet:
    """First 5 innings edge bet."""
    id: int
    game: str
    pitcher: str
    line: str  # -150, +120, etc.
    pick: str
    edge_type: str  # pitcher, runs, nrfi, strikeouts
    reasoning: str
    confidence: float


# Sample F5 edges for tonight/soon - need live data for actual picks
# These are examples based on pitcher metrics + matchup

F5_EDGES = [
    # 1. F5 RUNS UNDER - ELITE STARTER VS WEAK LINEUP
    F5EdgeBet(
        id=1,
        game="Dodgers vs Giants",
        pitcher="Yoshinobu Yamamoto",
        line="-130",
        pick="F5 Under 4.5 runs",
        edge_type="runs",
        reasoning="Yamamoto (elite stuff) vs weak SF lineup. F5 O/U typically lower. Target 4.5 or 5.",
        confidence=75,
    ),
    
    # 2. NRFI - NO RUN FIRST INNING
    F5EdgeBet(
        id=2,
        game="Any elite pitcher start",
        pitcher="Elite starter",
        line="+100",
        pick="NRFI - No Run 1st Inning",
        edge_type="nrfi",
        reasoning="Elite pitcher facing 1st time through order = low run probability in inning 1.",
        confidence=65,
    ),
    
    # 3. F5 MONEYLINE - ACE VS BAD TEAM
    F5EdgeBet(
        id=3,
        game="Aaron Judge's team vs weak opponent",
        pitcher="Any good starter",
        line="-160",
        pick="F5 Favorite -1.5",
        edge_type="runs",
        reasoning="Ace vs weak lineup = likely 3+ run lead by inning 5. Cover -1.5 F5.",
        confidence=70,
    ),
    
    # 4. STRIKEOUTS OVER - K GUY VS WEAK TEAM
    F5EdgeBet(
        id=4,
        game="High K pitcher vs weak offensive team",
        pitcher="Max K potential",
        line="-130",
        pick="F5 Over 4.5 K",
        edge_type="strikeouts",
        reasoning="High K pitcher (25+ K/9) vs bottom 10 offense = 5+ K in 5 innings.",
        confidence=75,
    ),
    
    # 5. F5 DOG + MONEY - VALUE UNDERDOG
    F5EdgeBet(
        id=5,
        game="Good pitcher dog vs great team",
        pitcher="Good pitcher +140",
        line="+140",
        pick="F5 Dog ML",
        edge_type="moneyline",
        reasoning="Good pitcher keeps it close. +140 value. Fade public on chalk.",
        confidence=60,
    ),
    
    # 6. F5 RUNS OVER - HIGH OFFENSE VS BAD STARTER
    F5EdgeBet(
        id=6,
        game="Ohtani/Judge team vs bad pitcher",
        pitcher="Bad starter 5+ ERA",
        line="-120",
        pick="F5 Over 5.5 runs",
        edge_type="runs",
        reasoning="Elite offense vs bad starter = 4+ runs in first 5. Target 5.5 or 6.",
        confidence=75,
    ),
    
    # 7. FIRST INNING SPECIFIC - HR OR NOTHING
    F5EdgeBet(
        id=7,
        game="Power team vs power pitcher",
        pitcher="Power vs Power",
        line="+150",
        pick="1st Inning Over 0.5 runs",
        edge_type="nrfi",
        reasoning="Either HR early or nothing. Risk/reward. Take at +150.",
        confidence=55,
    ),
    
    # 8. F5 WALKER - FADE BIG FAVE WITH BAD BULLPEN
    F5EdgeBet(
        id=8,
        game="Big favorite but weak starter",
        pitcher="Weak starter",
        line="+180",
        pick="F5 +1.5 on dog",
        edge_type="runs",
        reasoning="Big favorite but weak starter. Dog gets +1.5. Fade the steam.",
        confidence=65,
    ),
    
    # 9. STRIKEOUTS UNDER - CONTACT BATTER VS K PITCHER
    F5EdgeBet(
        id=9,
        game="Contact team vs high K pitcher",
        pitcher="High K guy",
        line="+110",
        pick="F5 Under 5.5 K",
        edge_type="strikeouts",
        reasoning="Contact team (low K%) vs K pitcher = fewer K than expected. Sell the over.",
        confidence=60,
    ),
    
    # 10. F5 INNING SPECIFIC - 3RD INNING
    F5EdgeBet(
        id=10,
        game="Any game",
        pitcher="2nd time through order",
        line="+120",
        pick="3rd Inning Over 0.5 runs",
        edge_type="nrfi",
        reasoning="2nd time through order = more mistakes. 3rd inning spikes in scoring.",
        confidence=55,
    ),
]


# ─── LIVE F5 SCANNER ───────────────────────────────────────────────

def get_f5_scanner_checklist() -> List[str]:
    """
    Checklist for scanning today's F5 edges.
    Use this before betting - check each item.
    """
    return [
        "📋 F5 SCANNER CHECKLIST",
        "─" * 40,
        "",
        "1. STARTER ANALYSIS",
        "   □ Check ERA, K/9, BB/9, WHIP last 3 starts",
        "   □ Is pitcher 1st or 2nd time through order?",
        "   □ Health/rest days (4 days rest = better?)",
        "",
        "2. OPPONENT MATCHUP",
        "   □ Team OPS vs RHP (if RHP starter)",
        "   □ K% vs this handedness",
        "   □ Recent form (last 10 games)",
        "",
        "3. RUNS SCORING CHECK",
        "   □ Weather: wind out = more HR",
        "   □ Ballpark: hitter's vs pitcher's park",
        "   □ Umpire: extreme zone?",
        "",
        "4. F5 SPECIFIC EDGES",
        "   □ NRFI if elite pitcher + weak leadoff",
        "   □ F5 Under if ace + weak lineup + low total",
        "   □ F5 Over if bad starter + elite offense",
        "   □ Dog +1.5 if bad starter but good bullpen favorite",
        "",
        "5. LINE SHOPPING",
        "   □ Check 3+ books for best line",
        "   □ F5 lines move less than full game",
        "   □ Look for steam moves (fading can be +EV)",
        "",
        "6. KEY NUMBERS (F5)",
        "   □ F5 -1.5 typically needs 3+ runs",
        "   □ F5 totals typically 40-60% of full game total",
        "   □ +1.5 F5 dog often has value",
    ]


def calculate_f5_line(full_game_total: float) -> dict:
    """
    Estimate F5 total from full game total.
    Rule of thumb: F5 = 40-45% of full game.
    """
    low_estimate = full_game_total * 0.40
    high_estimate = full_game_total * 0.45
    
    return {
        "full_game": full_game_total,
        "f5_estimate_low": round(low_estimate, 1),
        "f5_estimate_high": round(high_estimate, 1),
        "recommended_f5": round((low_estimate + high_estimate) / 2, 1),
    }


# ─── DEMO ────────────────────────────────────────────────────────────

def demo():
    """Show F5 edges."""
    
    print("=" * 70)
    print("⚾ F5 (FIRST 5 INNINGS) EDGE BETS")
    print("   Single game - Pitcher props - First 5 runs")
    print("=" * 70)
    
    print("\n📊 TOP 10 F5 EDGES:\n")
    for bet in F5_EDGES:
        print(f"  {bet.id:2}. {bet.edge_type.upper():12} | {bet.game}")
        print(f"      Pick: {bet.pick}")
        print(f"      Line: {bet.line} | Conf: {bet.confidence}%")
        print(f"      Why:  {bet.reasoning[:50]}...")
        print()
    
    print("=" * 70)
    print("📋 SCANNER CHECKLIST:")
    print("=" * 70)
    for line in get_f5_scanner_checklist():
        print(f"  {line}")
    
    print("\n" + "=" * 70)
    print("🎯 F5 TOTALS ESTIMATOR:")
    print("=" * 70)
    examples = [7, 8, 9, 10, 11]
    for total in examples:
        calc = calculate_f5_line(total)
        print(f"  Full game {total} runs → F5 should be ~{calc['recommended_f5']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo()