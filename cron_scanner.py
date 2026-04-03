#!/usr/bin/env python3
"""
NOESIS Daily Cron Job

Runs at MIDNIGHT UTC to prepare bets for tomorrow's games.
Fetches lines, scans edge vault, outputs digger units.

Schedule: 0 0 * * * (midnight UTC daily)
"""

import os
import sys
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from baseball_edge_vault import EdgeVault, DailyScanner, GameMatch, EdgeType


# ─── CONFIG ────────────────────────────────────────────────────────

CRON_LOG_FILE = "/root/.openclaw/workspace/noesis-prediction/cron_logs/scanner.log"
API_CONFIG = {
    # Add your API keys here for live data
    "odds_api": os.getenv("ODDS_API_KEY", ""),
    "the_rundown": os.getenv("THE_RUNDOWN_KEY", ""),
    "oddsjam": os.getenv("ODDSJAM_KEY", ""),
}


# ─── GAME FETCHER (Stub) ────────────────────────────────────────────

def get_tomorrow_games() -> list[GameMatch]:
    """
    Fetch tomorrow's MLB games.
    
    In production: Replace with real API calls.
    For now: Returns sample games for demo.
    """
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Check for API keys
    if not API_CONFIG["odds_api"]:
        print(f"⚠️  No ODDS_API_KEY - using sample data")
        return get_sample_games()
    
    # TODO: Real API integration
    # import requests
    # resp = requests.get(f"https://api.oddsapi.com/v1/games?date={tomorrow}&sport=mlb")
    # return parse_games(resp.json())
    
    return get_sample_games()


def get_sample_games() -> list[GameMatch]:
    """Sample games for demo/testing."""
    
    # Tomorrow's date
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    
    return [
        GameMatch(
            game_id="mlb_001",
            away_team="Dodgers",
            home_team="Giants",
            away_pitcher="Yoshinobu Yamamoto",
            home_pitcher="Logan Webb",
            start_time=tomorrow.replace(hour=21, minute=5),
            total=7.5,
            ml_away=-145,
            ml_home=+125,
            starter_era=2.50,
            opponent_ops=0.680,
        ),
        GameMatch(
            game_id="mlb_002",
            away_team="Yankees",
            home_team="Red Sox",
            away_pitcher="Carlos Rodon",
            home_pitcher="Kutter Crawford",
            start_time=tomorrow.replace(hour=18, minute=5),
            total=9.0,
            ml_away=-130,
            ml_home=+110,
            starter_era=4.20,
            opponent_ops=0.750,
        ),
        GameMatch(
            game_id="mlb_003",
            away_team="Mets",
            home_team="Phillies",
            away_pitcher="Sean Manaea",
            home_pitcher="Zack Wheeler",
            start_time=tomorrow.replace(hour=19, minute=5),
            total=8.0,
            ml_away=+140,
            ml_home=-160,
            starter_era=3.40,
            opponent_ops=0.720,
        ),
        GameMatch(
            game_id="mlb_004",
            away_team="Astros",
            home_team="Rangers",
            away_pitcher="Justin Verlander",
            home_pitcher="Jacob deGrom",
            start_time=tomorrow.replace(hour=20, minute=5),
            total=7.0,
            ml_away=-110,
            ml_home=-110,
            starter_era=3.50,
            opponent_ops=0.710,
        ),
        GameMatch(
            game_id="mlb_005",
            away_team="Braves",
            home_team="Marlins",
            away_pitcher="Chris Sale",
            home_pitcher="Jesus Luzardo",
            start_time=tomorrow.replace(hour=18, minute=10),
            total=8.5,
            ml_away=-180,
            ml_home=+160,
            starter_era=2.80,
            opponent_ops=0.690,
        ),
    ]


# ─── LINE FETCHER (Stub) ────────────────────────────────────────────

def get_live_lines(games: list[GameMatch]) -> dict:
    """
    Get live betting lines for games.
    
    In production: Fetch from OddsAPI/TheRundown.
    """
    lines = {}
    
    for game in games:
        lines[game.game_id] = {
            "total": game.total,
            "ml_away": game.ml_away,
            "ml_home": game.ml_home,
            "f5_total": round(game.total * 0.42, 1),
            "f5_away": round(game.ml_away - 20),
            "f5_home": round(game.ml_home + 20),
            "strikeout_lines": {
                "over": 5.5,
                "under": 5.5,
            },
            "ip_line": 5.5,
        }
    
    return lines


# ─── MAIN SCAN ─────────────────────────────────────────────────────

def run_daily_scan():
    """Run the daily scan at midnight."""
    
    print("=" * 70)
    print(f"🕛 NOESIS DAILY SCAN - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 70)
    
    # Step 1: Fetch games for tomorrow
    print("\n📡 Fetching tomorrow's games...")
    games = get_tomorrow_games()
    print(f"   Found {len(games)} games")
    
    for g in games:
        print(f"   • {g.away_team} @ {g.home_team} | {g.start_time.strftime('%H:%M')} UTC")
    
    # Step 2: Fetch live lines
    print("\n📊 Fetching betting lines...")
    lines = get_live_lines(games)
    print(f"   Got lines for {len(lines)} games")
    
    # Step 3: Initialize vault + scanner
    print("\n📦 Loading edge vault...")
    vault = EdgeVault()
    scanner = DailyScanner(vault)
    print(f"   {len(vault.edges)} edges loaded")
    
    # Step 4: Run scan
    print("\n🔍 Scanning for edges...")
    digger_units = scanner.scan(games)
    
    # Step 5: Output results
    print("\n" + "=" * 70)
    print("🎯 DIGGER UNITS FOR TOMORROW:")
    print("=" * 70)
    
    if not digger_units:
        print("   No edges found today. Check back tomorrow.")
    else:
        total_units = 0
        for unit in digger_units:
            print(f"\n📦 {unit.unit_id}")
            print(f"   Edge Score: {unit.edge_score}%")
            print(f"   Odds: {unit.total_odds}x")
            print(f"   BET: {unit.recommended_units} units")
            print(f"   Legs:")
            for leg in unit.legs:
                print(f"      • {leg['edge_name']}")
            total_units += unit.recommended_units
        
        print(f"\n💰 TOTAL UNITS TO BET: {round(total_units, 2)}")
    
    # Step 6: Save results
    save_results(games, lines, digger_units)
    
    print("\n✅ Scan complete. See you at 9 AM for live edges.")
    print("=" * 70)
    
    return digger_units


def save_results(games: list[GameMatch], lines: dict, units: list):
    """Save scan results to file."""
    
    results_dir = Path("/root/.openclaw/workspace/noesis-prediction/cron_results")
    results_dir.mkdir(exist_ok=True)
    
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    
    results = {
        "scan_date": datetime.now(timezone.utc).isoformat(),
        "games_date": tomorrow,
        "games": [
            {
                "id": g.game_id,
                "away": g.away_team,
                "home": g.home_team,
                "away_pitcher": g.away_pitcher,
                "home_pitcher": g.home_pitcher,
                "start_time": g.start_time.isoformat(),
                "total": g.total,
            }
            for g in games
        ],
        "lines": lines,
        "digger_units": [
            {
                "unit_id": u.unit_id,
                "legs": u.legs,
                "odds": u.total_odds,
                "units": u.recommended_units,
                "edge_score": u.edge_score,
            }
            for u in units
        ],
    }
    
    result_file = results_dir / f"scan_{tomorrow}.json"
    with open(result_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {result_file}")


# ─── CRON SETUP ────────────────────────────────────────────────────

def generate_cron_entry() -> str:
    """Generate crontab entry."""
    
    script_path = "/root/.openclaw/workspace/noesis-prediction/cron_scanner.py"
    log_path = "/root/.openclaw/workspace/noesis-prediction/cron_logs/scanner.log"
    
    # Ensure log directory exists
    os.makedirs("/root/.openclaw/workspace/noesis-prediction/cron_logs", exist_ok=True)
    
    return f"""
# NOESIS Daily Scanner - Runs at MIDNIGHT UTC
# To add to crontab: crontab -e
# Then add this line:

0 0 * * * /usr/bin/python3 {script_path} >> {log_path} 2>&1

# Or use python directly:
# 0 0 * * * cd /root/.openclaw/workspace/noesis-prediction && python3 cron_scanner.py >> cron_logs/scanner.log 2>&1
"""


def setup_cron():
    """Set up the cron job."""
    
    cron_entry = generate_cron_entry()
    
    print("📝 CRON SETUP:")
    print(cron_entry)
    
    # Write to crontab
    cron_file = "/root/.openclaw/workspace/noesis-prediction/crontab"
    with open(cron_file, "w") as f:
        f.write(cron_entry)
    
    print(f"\n✅ Cron file saved to: {cron_file}")
    print("To activate: crontab /root/.openclaw/workspace/noesis-prediction/crontab")


# ─── MAIN ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="NOESIS Daily Scanner")
    parser.add_argument("--setup-cron", action="store_true", help="Set up cron job")
    parser.add_argument("--run-now", action="store_true", help="Run scan immediately")
    
    args = parser.parse_args()
    
    if args.setup_cron:
        setup_cron()
    elif args.run_now:
        run_daily_scan()
    else:
        # Default: run now
        run_daily_scan()