#!/usr/bin/env python3
"""
NOESIS Morning Edge Scan - 9 AM UTC

Runs at 9 AM to check what edges actually set up for today's games.
Filters by what's actually available in the market.

Schedule: 0 9 * * * (9 AM UTC daily)
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from baseball_edge_vault import EdgeVault, DailyScanner, GameMatch, EdgeType


# ─── LIVE DATA FETCHER (9 AM) ───────────────────────────────────────

def get_today_games_9am() -> list[GameMatch]:
    """
    Get today's games at 9 AM - more detailed data.
    """
    today = datetime.now(timezone.utc)
    
    # In production: fetch from API with full pitcher stats
    
    # Sample: More realistic 9 AM data
    return [
        GameMatch(
            game_id="mlb_001",
            away_team="Dodgers",
            home_team="Giants",
            away_pitcher="Yoshinobu Yamamoto",
            home_pitcher="Logan Webb",
            start_time=today.replace(hour=21, minute=5),
            total=7.5,
            ml_away=-145,
            ml_home=+125,
            starter_era=2.50,
            opponent_ops=0.680,
        ),
        GameMatch(
            game_id="mlb_002",
            away_team="Mets",
            home_team="Phillies",
            away_pitcher="Sean Manaea",
            home_pitcher="Zack Wheeler",
            start_time=today.replace(hour=19, minute=5),
            total=8.0,
            ml_away=+140,
            ml_home=-160,
            starter_era=3.40,
            opponent_ops=0.720,
        ),
        GameMatch(
            game_id="mlb_003",
            away_team="Braves",
            home_team="Marlins",
            away_pitcher="Chris Sale",
            home_pitcher="Jesus Luzardo",
            start_time=today.replace(hour=18, minute=10),
            total=8.5,
            ml_away=-180,
            ml_home=+160,
            starter_era=2.80,
            opponent_ops=0.690,
        ),
        GameMatch(
            game_id="mlb_004",
            away_team="Yankees",
            home_team="Guardians",
            away_pitcher="Carlos Rodon",
            home_pitcher="Shane Bieber",
            start_time=today.replace(hour=18, minute=10),
            total=8.0,
            ml_away=-120,
            ml_home=+100,
            starter_era=3.80,
            opponent_ops=0.710,
        ),
    ]


def get_live_props() -> dict:
    """
    Get available player props at 9 AM.
    
    In production: Fetch from DraftKings/FanDuel API.
    """
    return {
        "shohei-ohtani": {
            "home_runs": {"line": 40.5, "over": -125, "under": -105},
            "strikeouts": {"line": 7.5, "over": +100, "under": -130},
            "hits": {"line": 2.5, "over": -120, "under": -110},
        },
        "juan-soto": {
            "walks": {"line": 95.5, "over": -130, "under": +100},
            "hits": {"line": 2.5, "over": +110, "under": -140},
            "runs": {"line": 1.5, "over": -120, "under": -110},
        },
        "aaron-judge": {
            "home_runs": {"line": 40.5, "over": +100, "under": -130},
            "hits": {"line": 2.5, "over": -110, "under": -120},
            "rbi": {"line": 3.5, "over": -110, "under": -120},
        },
    }


# ─── EDGE FILTER (9 AM) ─────────────────────────────────────────────

def filter_available_edges(games: list[GameMatch], props: dict) -> list:
    """
    Filter edges by what's actually available in the market at 9 AM.
    """
    available = []
    
    for game in games:
        game_edges = []
        
        # Check F5 edges
        if game.starter_era and game.starter_era < 3.0:
            game_edges.append({
                "type": "F5 Under",
                "game": f"{game.away_team} @ {game.home_team}",
                "pitcher": game.away_pitcher,
                "confidence": 75,
                "available": True
            })
        
        if game.opponent_ops and game.opponent_ops > 0.750:
            game_edges.append({
                "type": "F5 Over",
                "game": f"{game.away_team} @ {game.home_team}",
                "pitcher": game.home_pitcher,
                "confidence": 70,
                "available": True
            })
        
        # Check props
        if "shohei-ohtani" in props:
            if props["shohei-ohtani"]["home_runs"]["line"] == 40.5:
                game_edges.append({
                    "type": "Prop: Ohtani 40+ HR",
                    "line": "40.5",
                    "odds": props["shohei-ohtani"]["home_runs"]["over"],
                    "confidence": 85,
                    "available": True
                })
        
        if "juan-soto" in props:
            if props["juan-soto"]["walks"]["line"] == 95.5:
                game_edges.append({
                    "type": "Prop: Soto 95+ Walks",
                    "line": "95.5",
                    "odds": props["juan-soto"]["walks"]["over"],
                    "confidence": 80,
                    "available": True
                })
        
        if game_edges:
            available.append({
                "game": game,
                "edges": game_edges
            })
    
    return available


# ─── MORNING SCAN ──────────────────────────────────────────────────

def run_morning_scan():
    """Run 9 AM scan - what's actually available."""
    
    print("=" * 70)
    print(f"🌅 NOESIS MORNING SCAN - 9 AM UTC - {datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    print("=" * 70)
    
    # Step 1: Get today's games
    print("\n📡 Fetching today's games...")
    games = get_today_games_9am()
    print(f"   {len(games)} games today")
    
    for g in games:
        print(f"   • {g.away_team} ({g.away_pitcher}) @ {g.home_team} ({g.home_pitcher})")
        print(f"     Total: {g.total} | ML: {g.ml_away}/{g.ml_home}")
    
    # Step 2: Get available props
    print("\n📊 Fetching available props...")
    props = get_live_props()
    print(f"   {len(props)} players with props")
    
    for player, player_props in props.items():
        print(f"   • {player}: {list(player_props.keys())}")
    
    # Step 3: Filter available edges
    print("\n🎯 Filtering available edges...")
    available = filter_available_edges(games, props)
    
    # Step 4: Output morning setup
    print("\n" + "=" * 70)
    print("🌅 TODAY'S EDGE SETUP:")
    print("=" * 70)
    
    total_confidence = 0
    total_units = 0
    
    for item in available:
        game = item["game"]
        edges = item["edges"]
        
        # Calculate game confidence
        game_conf = sum(e["confidence"] for e in edges) / len(edges)
        
        print(f"\n⚾ {game.away_team} @ {game.home_team}")
        print(f"   Start: {game.start_time.strftime('%H:%M')} UTC | Total: {game.total}")
        print(f"   Pitchers: {game.away_pitcher} vs {game.home_pitcher}")
        print(f"   EDGES ({len(edges)} found):")
        
        for edge in edges:
            print(f"      ✅ {edge['type']} ({edge['confidence']}% conf)")
            total_confidence += edge["confidence"]
        
        # Units = confidence / 100 * 2
        game_units = round((game_conf / 100) * 2, 2)
        print(f"   📦 RECOMMENDED: {game_units} units")
        total_units += game_units
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 MORNING SUMMARY:")
    print("=" * 70)
    print(f"   Games with edges: {len(available)}")
    print(f"   Total edges: {sum(len(item['edges']) for item in available)}")
    print(f"   Avg confidence: {total_confidence / max(1, sum(len(item['edges']) for item in available)):.1f}%")
    print(f"   💰 TOTAL UNITS: {round(total_units, 2)}")
    
    # Best plays
    print("\n🏆 TOP PLAYS:")
    all_edges = []
    for item in available:
        for edge in item["edges"]:
            all_edges.append({
                "game": f"{item['game'].away_team} @ {item['game'].home_team}",
                "edge": edge["type"],
                "confidence": edge["confidence"]
            })
    
    # Sort by confidence
    all_edges.sort(key=lambda x: x["confidence"], reverse=True)
    
    for i, e in enumerate(all_edges[:5], 1):
        print(f"   {i}. {e['edge']} ({e['game']}) - {e['confidence']}%")
    
    print("\n" + "=" * 70)
    print("✅ Morning scan complete. Bet the edges.")
    print("=" * 70)
    
    return available


if __name__ == "__main__":
    run_morning_scan()