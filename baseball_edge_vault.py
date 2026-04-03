"""
NOESIS Baseball Edge Vault

Daily scanner + automated edge detection.
Scans at 9 AM for games matching edge criteria.
Stacks multiple edges into digger unit parlays.
"""

import os
import json
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum


# ─── DATA MODELS ────────────────────────────────────────────────────

class EdgeType(Enum):
    """Types of edges."""
    F5_RUNS_UNDER = "f5_runs_under"
    F5_RUNS_OVER = "f5_runs_over"
    NRFI = "nrfi"
    STRIKEOUTS_OVER = "strikeouts_over"
    STRIKEOUTS_UNDER = "strikeouts_under"
    F5_ML_DOG = "f5_ml_dog"
    F5_SPREAD = "f5_spread"
    PLAYER_PROP = "player_prop"


class Confidence(Enum):
    """Edge confidence levels."""
    HIGH = 75
    MEDIUM = 65
    LOW = 55


@dataclass
class Edge:
    """A single edge bet."""
    id: str
    name: str
    edge_type: EdgeType
    criteria: Dict  # What to match in scanner
    min_confidence: int = 60
    min_odds: float = -150
    max_odds: float = +200
    description: str = ""


@dataclass
class GameMatch:
    """A game that matches edge criteria."""
    game_id: str
    away_team: str
    home_team: str
    away_pitcher: str
    home_pitcher: str
    start_time: datetime
    total: float
    ml_away: int
    ml_home: int
    starter_era: Optional[float] = None
    opponent_ops: Optional[float] = None
    temperature: Optional[float] = None
    wind: Optional[str] = None


@dataclass
class DiggerUnit:
    """A stacked parlay bet."""
    unit_id: str
    legs: List[Dict]
    total_odds: float
    recommended_units: float
    edge_score: float  # Combined confidence
    timestamp: datetime


# ─── EDGE VAULT ────────────────────────────────────────────────────

class EdgeVault:
    """
    The Edge Vault — stores all edge criteria.
    Daily scanner checks games against these edges.
    """

    def __init__(self):
        self.edges: List[Edge] = []
        self.matches: List[GameMatch] = []
        self.digger_units: List[DiggerUnit] = []
        self.last_scan: Optional[datetime] = None
        self._init_default_edges()

    def _init_default_edges(self):
        """Initialize default edge criteria."""

        # F5 RUNS UNDER - Elite pitcher vs weak lineup
        self.edges.append(Edge(
            id="edge_001",
            name="F5 Under - Ace vs Weak",
            edge_type=EdgeType.F5_RUNS_UNDER,
            criteria={
                "starter_era_max": 3.0,
                "opponent_ops_max": 0.700,
                "total_max": 8.0,
                "f5_line_max": 5.0,
            },
            min_confidence=75,
            min_odds=-150,
            max_odds=-110,
            description="Elite pitcher (ERA <3) vs weak offense (OPS <.700) = F5 under"
        ))

        # F5 RUNS OVER - Elite offense vs bad pitcher
        self.edges.append(Edge(
            id="edge_002",
            name="F5 Over - Elite vs Bad Starter",
            edge_type=EdgeType.F5_RUNS_OVER,
            criteria={
                "opponent_ops_min": 0.800,
                "starter_era_min": 5.0,
                "total_min": 9.0,
                "f5_line_min": 5.5,
            },
            min_confidence=75,
            min_odds=-130,
            max_odds=-100,
            description="Elite offense vs bad starter (ERA >5) = F5 over"
        ))

        # NRFI - Elite pitcher
        self.edges.append(Edge(
            id="edge_003",
            name="NRFI - No Run 1st Inning",
            edge_type=EdgeType.NRFI,
            criteria={
                "starter_era_max": 2.5,
                "opponent_ops_max": 0.720,
                "nrfi_odds_max": +120,
            },
            min_confidence=65,
            min_odds=-120,
            max_odds=+120,
            description="Elite pitcher (ERA <2.5) + weak leadoff = NRFI"
        ))

        # STRIKEOUTS OVER - K pitcher vs weak team
        self.edges.append(Edge(
            id="edge_004",
            name="K Over - High K vs Weak",
            edge_type=EdgeType.STRIKEOUTS_OVER,
            criteria={
                "k_per_nine_min": 10.0,
                "opponent_k_pct_min": 25.0,
                "k_line_max": 4.5,
            },
            min_confidence=75,
            min_odds=-150,
            max_odds=-110,
            description="High K pitcher (10+/9) vs high K% team = K over"
        ))

        # F5 DOG ML - Good pitcher dog
        self.edges.append(Edge(
            id="edge_005",
            name="F5 Dog ML - Value Dog",
            edge_type=EdgeType.F5_ML_DOG,
            criteria={
                "starter_era_max": 3.5,
                "ml_odds_min": +120,
                "ml_odds_max": +180,
            },
            min_confidence=60,
            min_odds=+120,
            max_odds=+200,
            description="Good pitcher (ERA <3.5) as dog +120 to +180 = value"
        ))

        # F5 SPREAD +1.5 - Fade steam
        self.edges.append(Edge(
            id="edge_006",
            name="F5 +1.5 - Fade Favorite",
            edge_type=EdgeType.F5_SPREAD,
            criteria={
                "ml_fav_min": -180,
                "starter_underdog_era_max": 4.0,
                "spread_odds_min": +160,
            },
            min_confidence=65,
            min_odds=+140,
            max_odds=+200,
            description="Big favorite (-180+) but weak starter = dog +1.5 value"
        ))

        # STRIKEOUTS UNDER - Contact team
        self.edges.append(Edge(
            id="edge_007",
            name="K Under - Contact vs K",
            edge_type=EdgeType.STRIKEOUTS_UNDER,
            criteria={
                "k_per_nine_min": 10.0,
                "opponent_k_pct_max": 18.0,
                "k_line_min": 5.5,
            },
            min_confidence=60,
            min_odds=-110,
            max_odds=+120,
            description="Contact team (K% <18%) vs K pitcher = K under value"
        ))

        # F5 -1.5 Favorite - Ace covers
        self.edges.append(Edge(
            id="edge_008",
            name="F5 -1.5 - Ace Covers",
            edge_type=EdgeType.F5_SPREAD,
            criteria={
                "starter_era_max": 2.5,
                "opponent_ops_max": 0.700,
                "ml_fav_max": -150,
            },
            min_confidence=70,
            min_odds=-160,
            max_odds=-120,
            description="Elite ace vs weak team = -1.5 F5 covers"
        ))

        # PLAYER PROP - Ohtani HR
        self.edges.append(Edge(
            id="edge_009",
            name="Ohtani 40+ HR",
            edge_type=EdgeType.PLAYER_PROP,
            criteria={
                "player": "shohei-ohtani",
                "prop": "home_runs",
                "line": 40.5,
                "3yr_avg_min": 40,
            },
            min_confidence=85,
            min_odds=-150,
            max_odds=-110,
            description="Ohtani 3-year avg: 45 HR. Take the over."
        ))

        # PLAYER PROP - Soto walks
        self.edges.append(Edge(
            id="edge_010",
            name="Soto 95+ Walks",
            edge_type=EdgeType.PLAYER_PROP,
            criteria={
                "player": "juan-soto",
                "prop": "walks",
                "line": 95.5,
                "bb_pct_min": 14.0,
            },
            min_confidence=80,
            min_odds=-150,
            max_odds=-110,
            description="Soto 16% BB rate = 100+ walks. Take over."
        ))

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get edge by ID."""
        for e in self.edges:
            if e.id == edge_id:
                return e
        return None

    def get_edges_by_type(self, edge_type: EdgeType) -> List[Edge]:
        """Get all edges of a type."""
        return [e for e in self.edges if e.edge_type == edge_type]

    def to_dict(self) -> dict:
        """Export vault to dict."""
        return {
            "edges": [
                {
                    "id": e.id,
                    "name": e.name,
                    "edge_type": e.edge_type.value,
                    "criteria": e.criteria,
                    "min_confidence": e.min_confidence,
                    "min_odds": e.min_odds,
                    "max_odds": e.max_odds,
                    "description": e.description,
                }
                for e in self.edges
            ],
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "matches_count": len(self.matches),
            "digger_units_count": len(self.digger_units),
        }


# ─── DAILY SCANNER ─────────────────────────────────────────────────

class DailyScanner:
    """
    Scans daily at 9 AM for matching games.
    Combines multiple edges into digger units.
    """

    def __init__(self, vault: EdgeVault):
        self.vault = vault

    def scan(self, games: List[GameMatch]) -> List[DiggerUnit]:
        """
        Scan games against edge vault.
        Returns digger units (stacked bets).
        """
        self.vault.matches = []
        matched_edges = []

        for game in games:
            for edge in self.vault.edges:
                if self._matches_edge(game, edge):
                    matched_edges.append({
                        "game": game,
                        "edge": edge,
                        "confidence": self._calculate_confidence(game, edge),
                    })
                    self.vault.matches.append(game)

        # Build digger units from matched edges
        digger_units = self._build_digger_units(matched_edges)
        self.vault.digger_units = digger_units
        self.vault.last_scan = datetime.now(timezone.utc)

        return digger_units

    def _matches_edge(self, game: GameMatch, edge: Edge) -> bool:
        """Check if game matches edge criteria."""
        criteria = edge.criteria

        # F5 RUNS UNDER
        if edge.edge_type == EdgeType.F5_RUNS_UNDER:
            if game.starter_era and criteria.get("starter_era_max"):
                if game.starter_era > criteria["starter_era_max"]:
                    return False
            if game.opponent_ops and criteria.get("opponent_ops_max"):
                if game.opponent_ops > criteria["opponent_ops_max"]:
                    return False
            return True

        # F5 RUNS OVER
        if edge.edge_type == EdgeType.F5_RUNS_OVER:
            if game.starter_era and criteria.get("starter_era_min"):
                if game.starter_era < criteria["starter_era_min"]:
                    return False
            return True

        # NRFI
        if edge.edge_type == EdgeType.NRFI:
            if game.starter_era and criteria.get("starter_era_max"):
                return game.starter_era <= criteria["starter_era_max"]
            return False

        # Default: pass basic check
        return True

    def _calculate_confidence(self, game: GameMatch, edge: Edge) -> float:
        """Calculate confidence score for match."""
        base = edge.min_confidence

        # Adjust based on how well criteria match
        if game.starter_era:
            if edge.edge_type == EdgeType.F5_RUNS_UNDER:
                if game.starter_era < 2.5:
                    base += 10  # Extra edge for elite pitcher

        return min(base, 95)  # Cap at 95%

    def _build_digger_units(self, matches: List[dict]) -> List[DiggerUnit]:
        """Build stacked parlay units from matches."""
        if not matches:
            return []

        units = []

        # Group by game
        game_edges = {}
        for m in matches:
            gid = m["game"].game_id
            if gid not in game_edges:
                game_edges[gid] = []
            game_edges[gid].append(m)

        # Build single-game digger units
        for gid, edges in game_edges.items():
            if len(edges) >= 2:
                # Multiple edges on same game = stack it
                game = edges[0]["game"]
                legs = []
                total_odds = 1.0
                edge_score = 0

                for e in edges:
                    leg = {
                        "edge_id": e["edge"].id,
                        "edge_name": e["edge"].name,
                        "game": f"{game.away_team} @ {game.home_team}",
                        "confidence": e["confidence"],
                    }
                    legs.append(leg)
                    total_odds *= (e["confidence"] / 100)
                    edge_score += e["confidence"]

                edge_score /= len(legs)

                units.append(DiggerUnit(
                    unit_id=f"digger_{gid}_{datetime.now().strftime('%Y%m%d')}",
                    legs=legs,
                    total_odds=round(total_odds * 100, 1),
                    recommended_units=round(edge_score / 100 * 2.0, 2),  # 0.5-2 units
                    edge_score=round(edge_score, 1),
                    timestamp=datetime.now(timezone.utc),
                ))

        return units


# ─── SCHEDULER (Cron-like) ─────────────────────────────────────────

def next_scan_time() -> datetime:
    """Next 9 AM scan time."""
    now = datetime.now(timezone.utc)
    next_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)
    
    if now.hour >= 9:
        next_9am += timedelta(days=1)
    
    return next_9am


# ─── DEMO ────────────────────────────────────────────────────────────

def demo():
    """Demo the edge vault."""
    
    print("=" * 70)
    print("📦 NOESIS EDGE VAULT")
    print("   Daily scanner + digger units")
    print("=" * 70)
    
    # Initialize vault
    vault = EdgeVault()
    
    print(f"\n📊 EDGES IN VAULT: {len(vault.edges)}")
    for edge in vault.edges:
        print(f"  {edge.id}: {edge.name}")
        print(f"      Type: {edge.edge_type.value}")
        print(f"      Conf: {edge.min_confidence}%+")
        print(f"      Desc: {edge.description[:50]}...")
        print()
    
    # Export vault
    vault_dict = vault.to_dict()
    print(f"\n📦 Vault export:")
    print(f"  Edges: {len(vault_dict['edges'])}")
    print(f"  Ready for scanner")
    
    # Demo scanner
    scanner = DailyScanner(vault)
    
    # Sample games (would come from live API in production)
    sample_games = [
        GameMatch(
            game_id="game_001",
            away_team="Dodgers",
            home_team="Giants",
            away_pitcher="Yoshinobu Yamamoto",
            home_pitcher="Logan Webb",
            start_time=datetime.now(timezone.utc) + timedelta(hours=4),
            total=7.5,
            ml_away=-140,
            ml_home=+120,
            starter_era=2.50,  # Elite
            opponent_ops=0.680,  # Weak
        ),
        GameMatch(
            game_id="game_002",
            away_team="Yankees",
            home_team="Red Sox",
            away_pitcher="Carlos Rodon",
            home_pitcher="Kutter Crawford",
            start_time=datetime.now(timezone.utc) + timedelta(hours=5),
            total=9.0,
            ml_away=-130,
            ml_home=+110,
            starter_era=4.20,
            opponent_ops=0.750,
        ),
    ]
    
    # Run scan
    print("\n🔄 RUNNING DAILY SCANNER...")
    digger_units = scanner.scan(sample_games)
    
    print(f"\n📊 SCAN RESULTS:")
    print(f"  Games scanned: {len(sample_games)}")
    print(f"  Matches found: {len(vault.matches)}")
    print(f"  Digger units: {len(digger_units)}")
    
    # Next scan
    next_scan = next_scan_time()
    print(f"\n⏰ NEXT SCAN: {next_scan.strftime('%Y-%m-%d %H:%M UTC')}")
    
    print("\n" + "=" * 70)
    print("🛠️  TO RUN DAILY SCAN:")
    print("=" * 70)
    print("""
# In production, run at 9 AM UTC:

from baseball_edge_vault import EdgeVault, DailyScanner

vault = EdgeVault()
scanner = DailyScanner(vault)

# Get today's games from API (e.g., TheRundown, OddsAPI)
games = get_todays_games()

# Scan and build digger units
units = scanner.scan(games)

# Each unit has:
# - unit_id
# - legs (multiple edges)
# - total_odds
# - recommended_units (0.5-2.0 based on confidence)
# - edge_score (combined confidence)

for unit in units:
    print(f"Bet {unit.recommended_units} units on {unit.unit_id}")
""")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo()