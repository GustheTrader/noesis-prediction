"""
NOESIS Baseball Knowledge Base

3-year rolling averages for edge picks.
Predictive metrics: WAR, OPS, wRC+, K%, BB%

For building edge in betting.
"""

import json
import csv
import os
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone


@dataclass
class PlayerStats:
    """3-year average stats for a player."""
    name: str
    team: str
    position: str
    # 3-year averages
    games: float
    pa: float  # Plate appearances
    hr: float  # Home runs
    rbi: float
    runs: float
    sb: float  # Stolen bases
    avg: float  # Batting average
    obp: float  # On-base %
    slg: float  # Slugging %
    ops: float  # On-base + Slugging
    wrc_plus: float  # Weighted runs created plus
    war: float  # Wins above replacement
    k_pct: float  # Strikeout %
    bb_pct: float  # Walk %
    # Stability indicators (lower = more consistent)
    ops_stability: float  # Std dev of OPS


# Sample 3-year data (2024-2026) - Top edge players
# In production: fetch from pybaseball or FanGraphs API
SAMPLE_PLAYERS = {
    # Elite hitters with consistent 3-year production
    "shohei-ohtani": PlayerStats(
        name="Shohei Ohtani",
        team="Dodgers",
        position="DH",
        games=150.0, pa=650.0, hr=45.0, rbi=110.0, runs=100.0, sb=30.0,
        avg=.310, obp=.410, slg=.650, ops=1.060, wrc_plus=175.0, war=7.5,
        k_pct=18.0, bb_pct=12.0, ops_stability=0.08
    ),
    "aaron-judge": PlayerStats(
        name="Aaron Judge",
        team="Yankees",
        position="CF",
        games=145.0, pa=620.0, hr=48.0, rbi=115.0, runs=105.0, sb=12.0,
        avg=.290, obp=.410, slg=.620, ops=1.030, wrc_plus=168.0, war=6.8,
        k_pct=22.0, bb_pct=14.0, ops_stability=0.12
    ),
    "mike-trout": PlayerStats(
        name="Mike Trout",
        team="Angels",
        position="CF",
        games=120.0, pa=520.0, hr=35.0, rbi=85.0, runs=80.0, sb=20.0,
        avg=.280, obp=.390, slg=.550, ops=.940, wrc_plus=145.0, war=5.2,
        k_pct=20.0, bb_pct=13.0, ops_stability=0.15
    ),
    "mookie-betts": PlayerStats(
        name="Mookie Betts",
        team="Dodgers",
        position="RF",
        games=150.0, pa=650.0, hr=35.0, rbi=95.0, runs=110.0, sb=25.0,
        avg=.295, obp=.385, slg=.560, ops=.945, wrc_plus=140.0, war=6.0,
        k_pct=14.0, bb_pct=10.0, ops_stability=0.06
    ),
    "franc Lindor": PlayerStats(
        name="Francisco Lindor",
        team="Mets",
        position="SS",
        games=155.0, pa=650.0, hr=30.0, rbi=95.0, runs=100.0, sb=25.0,
        avg=.275, obp=.345, slg=.500, ops=.845, wrc_plus=125.0, war=5.5,
        k_pct=16.0, bb_pct=9.0, ops_stability=0.07
    ),
    "juan-soto": PlayerStats(
        name="Juan Soto",
        team="Mets",
        position="RF",
        games=150.0, pa=650.0, hr=35.0, rbi=100.0, runs=95.0, sb=15.0,
        avg=.285, obp=.420, slg=.550, ops=.970, wrc_plus=160.0, war=5.8,
        k_pct=18.0, bb_pct=16.0, ops_stability=0.10
    ),
    "vladimir-guerrero": PlayerStats(
        name="Vladimir Guerrero Jr.",
        team="Blue Jays",
        position="1B",
        games=150.0, pa=650.0, hr=38.0, rbi=105.0, runs=90.0, sb=10.0,
        avg=.290, obp=.360, slg=.530, ops=.890, wrc_plus=130.0, war=4.5,
        k_pct=15.0, bb_pct=8.0, ops_stability=0.09
    ),
    "yoshinobu-yamamoto": PlayerStats(
        name="Yoshinobu Yamamoto",
        team="Dodgers",
        position="P",
        games=30.0, pa=0.0, hr=0.0, rbi=0.0, runs=0.0, sb=0.0,
        avg=.000, obp=.000, slg=.000, ops=.000, wrc_plus=0.0, war=4.0,
        k_pct=28.0, bb_pct=5.0, ops_stability=0.00
    ),
}

# Stability thresholds for edge detection
STABILITY_THRESHOLDS = {
    "elite": 0.08,      # Extremely consistent
    "solid": 0.12,      # Reliable
    "volatile": 0.20,   # Inconsistent
}


class BaseballKB:
    """
    Knowledge base for baseball betting edges.
    
    Uses 3-year rolling averages for predictive power.
    Filters for stability = consistent edge.
    """

    def __init__(self):
        self.players = SAMPLE_PLAYERS.copy()
        self.teams = {}

    def get_player(self, player_id: str) -> Optional[PlayerStats]:
        """Get player by ID."""
        return self.players.get(player_id)

    def search_by_metric(self, metric: str, min_value: float) -> list[PlayerStats]:
        """Find players by metric threshold."""
        results = []
        for p in self.players.values():
            if metric == "ops" and p.ops >= min_value:
                results.append(p)
            elif metric == "war" and p.war >= min_value:
                results.append(p)
            elif metric == "wrc_plus" and p.wrc_plus >= min_value:
                results.append(p)
            elif metric == "bb_pct" and p.bb_pct >= min_value:
                results.append(p)
        return sorted(results, key=lambda x: getattr(x, metric, 0), reverse=True)

    def get_edge_players(self) -> list[PlayerStats]:
        """
        Get players with edge: high OPS + high stability.
        
        Edge = high skill + consistent results
        """
        edges = []
        for p in self.players.values():
            if p.ops >= 0.900 and p.ops_stability <= STABILITY_THRESHOLDS["solid"]:
                edges.append(p)
        return sorted(edges, key=lambda x: x.ops, reverse=True)

    def get_steals_edge(self, min_sb: int = 15) -> list[PlayerStats]:
        """Get players with steals edge."""
        return sorted(
            [p for p in self.players.values() if p.sb >= min_sb],
            key=lambda x: x.sb, reverse=True
        )

    def get_power_edge(self, min_hr: int = 30) -> list[PlayerStats]:
        """Get players with power edge."""
        return sorted(
            [p for p in self.players.values() if p.hr >= min_hr],
            key=lambda x: x.hr, reverse=True
        )

    def get_plate_discipline(self, min_bb: float = 12.0) -> list[PlayerStats]:
        """Get players with best plate discipline (high BB%)."""
        return sorted(
            [p for p in self.players.values() if p.bb_pct >= min_bb],
            key=lambda x: x.bb_pct, reverse=True
        )

    def to_knowledge_graph(self) -> dict:
        """Export to knowledge graph format."""
        nodes = []
        edges = []
        
        for pid, p in self.players.items():
            # Node
            nodes.append({
                "id": pid,
                "type": "player",
                "name": p.name,
                "team": p.team,
                "position": p.position,
                "metrics": {
                    "ops_3yr": p.ops,
                    "war_3yr": p.war,
                    "wrc_plus_3yr": p.wrc_plus,
                    "sb_3yr": p.sb,
                    "hr_3yr": p.hr,
                    "stability": p.ops_stability,
                },
                "category": "baseball_edge" if p.ops >= 0.900 and p.ops_stability <= 0.12 else "baseball",
            })
            
            # Edge to team
            edges.append({
                "from": pid,
                "to": p.team.lower().replace(" ", "-"),
                "type": "plays_for",
            })
        
        return {"nodes": nodes, "edges": edges}

    def validate_prediction(self, claim: str) -> dict:
        """
        Validate a prediction against the knowledge base.
        
        Example: "Juan Soto will hit 40+ HR"
        """
        claim_lower = claim.lower()
        
        # Check player mentions
        for pid, p in self.players.items():
            if p.name.lower() in claim_lower:
                # Extract metric from claim
                if "hr" in claim_lower or "home run" in claim_lower:
                    # Extract number
                    import re
                    nums = re.findall(r'\d+', claim_lower)
                    if nums:
                        predicted = int(nums[0])
                        return {
                            "is_valid": True,
                            "player": p.name,
                            "metric": "hr",
                            "3yr_avg": p.hr,
                            "prediction": predicted,
                            "confidence": 1.0 - abs(p.hr - predicted) / p.hr,
                            "reason": f"3-year avg: {p.hr:.1f} HR",
                        }
        
        return {"is_valid": False, "reason": "No matching player found"}


# ─── Demo ────────────────────────────────────────────────────────

def demo():
    """Demo the baseball knowledge base."""
    
    print("=" * 60)
    print("🏟️  NOESIS BASEBALL KNOWLEDGE BASE")
    print("   3-Year Averages for Edge Picks")
    print("=" * 60)
    
    kb = BaseballKB()
    
    # Show all players
    print("\n📊 ALL PLAYERS:")
    for p in kb.players.values():
        print(f"  {p.name:20} | {p.team:10} | OPS: {p.ops:.3f} | WAR: {p.war:.1f}")
    
    # Edge players
    print("\n🎯 EDGE PLAYERS (High OPS + Stable):")
    edges = kb.get_edge_players()
    for p in edges:
        print(f"  {p.name:20} | OPS: {p.ops:.3f} | Stability: {p.ops_stability:.2f}")
    
    # Power edge
    print("\n💪 POWER EDGE (30+ HR):")
    power = kb.get_power_edge(30)
    for p in power:
        print(f"  {p.name:20} | HR: {p.hr:.0f}")
    
    # Steals edge
    print("\n⚡ STEALS EDGE (15+ SB):")
    steals = kb.get_steals_edge(15)
    for p in steals:
        print(f"  {p.name:20} | SB: {p.sb:.0f}")
    
    # Plate discipline
    print("\n🎓 PLATE DISCIPLINE (12%+ BB):")
    disc = kb.get_plate_discipline(12.0)
    for p in disc:
        print(f"  {p.name:20} | BB%: {p.bb_pct:.1f}%")
    
    # Validate prediction
    print("\n🔍 VALIDATE PREDICTION:")
    result = kb.validate_prediction("Juan Soto will hit 40 HR")
    print(f"  Claim: 'Juan Soto will hit 40 HR'")
    print(f"  Result: {result}")
    
    # Export to graph
    print("\n📦 KNOWLEDGE GRAPH:")
    graph = kb.to_knowledge_graph()
    print(f"  Nodes: {len(graph['nodes'])}")
    print(f"  Edges: {len(graph['edges'])}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    demo()