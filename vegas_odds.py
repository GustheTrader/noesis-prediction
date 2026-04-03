"""
NOESIS Vegas Odds Scraper

Daily scrape of Vegas betting lines.
Runs at specific times to grab odds before games.

Sources:
- DraftKings (primary)
- FanDuel
- BetMGM
- Caesars

Schedule: Run before 9 AM scan to get lines for edge matching.
"""

import requests
import json
import re
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path


# ─── DATA MODELS ──────────────────────────────────────────────────────

@dataclass
class VegasLine:
    """A Vegas betting line."""
    game_id: str
    book: str  # DraftKings, FanDuel, etc.
    home_team: str
    away_team: str
    ml_home: int
    ml_away: int
    total: float
    total_over: float
    total_under: float
    f5_total: float
    f5_over: float
    f5_under: float
    timestamp: datetime


@dataclass
class PropLine:
    """A player prop line."""
    player_id: str
    player_name: str
    book: str
    prop_type: str  # HR, K, BB, etc.
    line: float
    over_odds: float
    under_odds: float
    timestamp: datetime


# ─── SCRAPERS ──────────────────────────────────────────────────────────

class DraftKingsScraper:
    """Scrape DraftKings sportsbook."""
    
    BASE_URL = "https://sportsbook.draftkings.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        })
    
    def get_mlb_lines(self) -> List[VegasLine]:
        """Get MLB moneyline and totals."""
        lines = []
        
        # Try API endpoint first
        try:
            url = f"{self.BASE_URL}/sites/us-sportsbook/api/bets/events?format=json&eventTypeId=842&categoryId=48268"
            resp = self.session.get(url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                # Parse DraftKings format
                # This is simplified - real implementation needs proper parsing
                pass
        except Exception as e:
            print(f"DraftKings API error: {e}")
        
        return lines
    
    def get_player_props(self, player_id: str = None) -> List[PropLine]:
        """Get player props."""
        props = []
        
        try:
            # MLB player props endpoint
            url = f"{self.BASE_URL}/sites/us-sportsbook/api/bets/events?format=json&eventTypeId=842&categoryId=48308"
            resp = self.session.get(url, timeout=10)
            
            if resp.status_code == 200:
                # Parse props
                pass
        except Exception as e:
            print(f"DraftKings props error: {e}")
        
        return props


class VegasOddsAggregator:
    """Aggregate odds from multiple Vegas books."""
    
    def __init__(self):
        self.books = {
            "DraftKings": DraftKingsScraper(),
            # "FanDuel": FanDuelScraper(),
            # "BetMGM": BetMGMScraper(),
            # "Caesars": CaesarsScraper(),
        }
        self.lines: List[VegasLine] = []
        self.props: List[PropLine] = []
    
    def scrape_all_lines(self) -> List[VegasLine]:
        """Scrape lines from all books."""
        all_lines = []
        
        for book_name, scraper in self.books.items():
            print(f"📡 Scraping {book_name}...")
            try:
                lines = scraper.get_mlb_lines()
                for line in lines:
                    line.book = book_name
                all_lines.extend(lines)
            except Exception as e:
                print(f"   ⚠️ {book_name}: {e}")
        
        self.lines = all_lines
        return all_lines
    
    def scrape_all_props(self) -> List[PropLine]:
        """Scrape props from all books."""
        all_props = []
        
        for book_name, scraper in self.books.items():
            if hasattr(scraper, 'get_player_props'):
                try:
                    props = scraper.get_player_props()
                    for prop in props:
                        prop.book = book_name
                    all_props.extend(props)
                except Exception as e:
                    print(f"   ⚠️ {book_name} props: {e}")
        
        self.props = all_props
        return all_props
    
    def get_best_line(self, game_id: str, bet_type: str) -> VegasLine:
        """Get best line for a bet."""
        game_lines = [l for l in self.lines if l.game_id == game_id]
        
        if not game_lines:
            return None
        
        # Sort by best odds for the bet type
        if bet_type == "ml_home":
            return min(game_lines, key=lambda x: x.ml_home if x.ml_home > 0 else 999)
        elif bet_type == "ml_away":
            return min(game_lines, key=lambda x: x.ml_away if x.ml_away > 0 else 999)
        elif bet_type == "total_over":
            return min(game_lines, key=lambda x: x.total_over if x.total_over > 0 else 999)
        
        return game_lines[0]


# ─── STORAGE ──────────────────────────────────────────────────────────

ODDS_DIR = Path("/root/.openclaw/workspace/noesis-prediction/odds_logs")


def save_odds(lines: List[VegasLine], props: List[PropLine]):
    """Save odds to file."""
    ODDS_DIR.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "games": [
            {
                "game_id": l.game_id,
                "book": l.book,
                "home": l.home_team,
                "away": l.away_team,
                "ml_home": l.ml_home,
                "ml_away": l.ml_away,
                "total": l.total,
                "over": l.total_over,
                "under": l.total_under,
                "f5_total": l.f5_total,
            }
            for l in lines
        ],
        "props": [
            {
                "player": p.player_name,
                "book": p.book,
                "prop": p.prop_type,
                "line": p.line,
                "over": p.over_odds,
                "under": p.under_odds,
            }
            for p in props
        ]
    }
    
    filepath = ODDS_DIR / f"odds_{today}.json"
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"💾 Saved {len(lines)} lines, {len(props)} props to {filepath}")


# ─── SAMPLE DATA (Demo) ────────────────────────────────────────────────

def get_sample_odds() -> List[VegasLine]:
    """Get sample odds for demo."""
    today = datetime.now(timezone.utc)
    
    return [
        # Dodgers @ Giants
        VegasLine(
            game_id="mlb_001",
            book="DraftKings",
            home_team="Giants",
            away_team="Dodgers",
            ml_home=+125,
            ml_away=-145,
            total=7.5,
            total_over=-115,
            total_under=-105,
            f5_total=3.5,
            f5_over=-115,
            f5_under=-105,
            timestamp=today
        ),
        # Mets @ Phillies
        VegasLine(
            game_id="mlb_002",
            book="DraftKings",
            home_team="Phillies",
            away_team="Mets",
            ml_home=-160,
            ml_away=+140,
            total=8.0,
            total_over=-110,
            total_under=-110,
            f5_total=3.5,
            f5_over=-110,
            f5_under=-110,
            timestamp=today
        ),
        # Braves @ Marlins
        VegasLine(
            game_id="mlb_003",
            book="DraftKings",
            home_team="Marlins",
            away_team="Braves",
            ml_home=+160,
            ml_away=-180,
            total=8.5,
            total_over=-110,
            total_under=-110,
            f5_total=4.0,
            f5_over=-110,
            f5_under=-110,
            timestamp=today
        ),
        # Yankees @ Guardians
        VegasLine(
            game_id="mlb_004",
            book="DraftKings",
            home_team="Guardians",
            away_team="Yankees",
            ml_home=+100,
            ml_away=-120,
            total=8.0,
            total_over=-110,
            total_under=-110,
            f5_total=3.5,
            f5_over=-110,
            f5_under=-110,
            timestamp=today
        ),
    ]


def get_sample_props() -> List[PropLine]:
    """Get sample props for demo."""
    today = datetime.now(timezone.utc)
    
    return [
        PropLine(
            player_id="ohtani001",
            player_name="Shohei Ohtani",
            book="DraftKings",
            prop_type="home_runs",
            line=40.5,
            over_odds=-125,
            under_odds=-105,
            timestamp=today
        ),
        PropLine(
            player_id="soto001",
            player_name="Juan Soto",
            book="DraftKings",
            prop_type="walks",
            line=95.5,
            over_odds=-130,
            under_odds=+100,
            timestamp=today
        ),
        PropLine(
            player_id="judge001",
            player_name="Aaron Judge",
            book="DraftKings",
            prop_type="home_runs",
            line=40.5,
            over_odds=+100,
            under_odds=-130,
            timestamp=today
        ),
    ]


# ─── EDGE INTEGRATION ─────────────────────────────────────────────────

def match_edges_with_odds(edges: List[dict], lines: List[VegasLine], props: List[PropLine]) -> List[dict]:
    """Match edges with available odds to find +EV bets."""
    
    matched = []
    
    for edge in edges:
        # Find matching line
        game_line = None
        for line in lines:
            if edge.get("game", "").split(" @ ")[0] in line.away_team:
                game_line = line
                break
        
        if not game_line:
            continue
        
        # Match based on edge type
        if "F5 Under" in edge.get("type", ""):
            # F5 Under: check if line is high enough
            if game_line.f5_total >= 4.5:
                matched.append({
                    "edge": edge,
                    "line": game_line,
                    "value": "Good" if game_line.f5_total >= 5.0 else "Fair",
                    "odds": game_line.f5_under
                })
        
        elif "F5 Over" in edge.get("type", ""):
            if game_line.f5_total <= 5.0:
                matched.append({
                    "edge": edge,
                    "line": game_line,
                    "value": "Good" if game_line.f5_total <= 4.0 else "Fair",
                    "odds": game_line.f5_over
                })
        
        elif "Prop" in edge.get("type", "") and "Ohtani" in edge.get("type", ""):
            # Match Ohtani HR prop
            ohtani_prop = [p for p in props if "Ohtani" in p.player_name and p.prop_type == "home_runs"]
            if ohtani_prop:
                matched.append({
                    "edge": edge,
                    "prop": ohtani_prop[0],
                    "value": "Available",
                    "odds": ohtani_prop[0].over_odds
                })
        
        elif "Prop" in edge.get("type", "") and "Soto" in edge.get("type", ""):
            soto_prop = [p for p in props if "Soto" in p.player_name and p.prop_type == "walks"]
            if soto_prop:
                matched.append({
                    "edge": edge,
                    "prop": soto_prop[0],
                    "value": "Available",
                    "odds": soto_prop[0].over_odds
                })
    
    return matched


# ─── MAIN ─────────────────────────────────────────────────────────────

def run_daily_odds_scrape():
    """Run daily odds scrape."""
    
    print("=" * 70)
    print("🎰 NOESIS VEGAS ODDS SCRAPER")
    print(f"   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)
    
    # Try to scrape, fall back to sample
    print("\n📡 Attempting Vegas scrape...")
    
    try:
        aggregator = VegasOddsAggregator()
        lines = aggregator.scrape_all_lines()
        props = aggregator.scrape_all_props()
    except Exception as e:
        print(f"   ⚠️ Scrape failed: {e}")
        print("   Using sample data...")
        lines = get_sample_odds()
        props = get_sample_props()
    
    print(f"\n📊 Got {len(lines)} game lines")
    print(f"📊 Got {len(props)} player props")
    
    # Show sample
    print("\n📋 Sample Lines:")
    for line in lines[:3]:
        print(f"   {line.away_team} @ {line.home_team}")
        print(f"   ML: {line.ml_away}/{line.ml_home} | Total: {line.total} | F5: {line.f5_total}")
    
    print("\n📋 Sample Props:")
    for prop in props:
        print(f"   {prop.player_name}: {prop.prop_type} {prop.line} (O: {prop.over_odds} / U: {prop.under_odds})")
    
    # Save
    save_odds(lines, props)
    
    return lines, props


if __name__ == "__main__":
    run_daily_odds_scrape()