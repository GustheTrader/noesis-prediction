#!/usr/bin/env python3
"""
lineup_analyst.py — Confirmed lineup analysis with L/R handedness matchups
Second-layer analysis after rosters are confirmed
"""
import requests
import json
from datetime import datetime
import re

print('='*70)
print('LINEUP ANALYST — L/R Handedness Matchup Analyzer')
print('='*70)

# Data sources for confirmed lineups
DATA_SOURCES = {
    'espn': {
        'name': 'ESPN API',
        'url_pattern': 'https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb/events/{game_id}/competitions/{game_id}/rosters',
        'reliability': 'High',
        'timing': '90-120 min before game'
    },
    'mlb_dot_com': {
        'name': 'MLB.com Lineups',
        'url_pattern': 'https://www.mlb.com/gameday/{game_id}',
        'reliability': 'Very High',
        'timing': '90 min before game (official)'
    },
    'baseball_press': {
        'name': 'Baseball Press',
        'url_pattern': 'https://www.baseballpress.com/lineups',
        'reliability': 'High',
        'timing': '60-90 min before game'
    },
    'rotowire': {
        'name': 'RotoWire',
        'url_pattern': 'https://www.rotowire.com/baseball/daily-lineups.htm',
        'reliability': 'High',
        'timing': '60-90 min before game'
    },
    'twitter': {
        'name': 'Official Team Twitter',
        'pattern': '@{team} starting lineup',
        'reliability': 'Very High',
        'timing': '90-120 min before game'
    }
}

print("\n📊 CONFIRMED LINEUP DATA SOURCES")
print("="*70)
for source_id, source in DATA_SOURCES.items():
    print(f"\n{source['name']}:")
    print(f"  Reliability: {source['reliability']}")
    print(f"  Timing: {source['timing']}")
    print(f"  URL: {source.get('url_pattern', source.get('pattern', 'N/A'))}")

# ESPN API Test for confirmed lineups
print("\n" + "="*70)
print("TESTING ESPN API FOR CONFIRMED LINEUPS")
print("="*70)

BASE_URL = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_json(url, params=None):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

# Test with a recent game to see lineup format
print("\nFetching sample lineup from recent game...")

# Try April 7 game
recent_game_id = "401814693"  # Sample game ID
roster_url = f"{BASE_URL}/events/{recent_game_id}/competitions/{recent_game_id}/rosters"

roster_data = get_json(roster_url)

if roster_data:
    print("✅ ESPN roster endpoint accessible")
    print(f"   Keys: {list(roster_data.keys())[:5]}")
    
    # Check structure
    if 'rosters' in roster_data:
        print(f"   Rosters found: {len(roster_data['rosters'])}")
        
        for roster in roster_data['rosters'][:1]:  # Check first roster
            team_ref = roster.get('team', {}).get('$ref')
            if team_ref:
                team = get_json(team_ref)
                print(f"   Team: {team.get('name', 'Unknown')}")
            
            # Check for batting order
            entries = roster.get('entries', [])
            print(f"   Entries: {len(entries)}")
            
            if entries:
                print("\n   Sample Lineup Entry:")
                entry = entries[0]
                print(f"     Keys: {list(entry.keys())}")
                
                # Get athlete info
                athlete_ref = entry.get('athlete', {}).get('$ref')
                if athlete_ref:
                    athlete = get_json(athlete_ref)
                    if athlete:
                        print(f"     Name: {athlete.get('displayName')}")
                        print(f"     Bats: {athlete.get('bats', {}).get('type', 'Unknown')}")
                        print(f"     Position: {entry.get('position', {}).get('abbreviation')}")
                        print(f"     Batting Order: {entry.get('battingOrder', 'N/A')}")
else:
    print("❌ Could not fetch roster data")

# Create Lineup Analysis Framework
print("\n" + "="*70)
print("LINEUP ANALYSIS FRAMEWORK")
print("="*70)

framework = """
┌─────────────────────────────────────────────────────────────┐
│           CONFIRMED LINEUP ANALYSIS PIPELINE                │
└─────────────────────────────────────────────────────────────┘

PHASE 1: DATA COLLECTION (T-90 minutes)
  ☐ Scrape ESPN rosters endpoint
  ☐ Cross-check MLB.com official lineups
  ☐ Verify no late scratches via Twitter
  ☐ Confirm starting pitchers locked

PHASE 2: L/R HANDEDNESS EXTRACTION
  For each confirmed lineup:
    • Extract batter handedness (L/R/S)
    • Extract pitcher handedness (LHP/RHP)
    • Calculate platoon matchups 1-9
    
PHASE 3: MATCHUP ANALYSIS
  Calculate:
    • % of batters with platoon advantage vs starter
    • Weighted OPS vs pitcher handedness
    • Lineup balance (L/R mix)
    • Top 3 hitters handedness
    
PHASE 4: SCORING PROJECTION ADJUSTMENT
  If > 60% of lineup has platoon advantage:
    → Increase predicted runs by 0.3-0.5
  If < 30% of lineup has platoon advantage:
    → Decrease predicted runs by 0.2-0.4
  If balanced lineup:
    → No adjustment

PHASE 5: BETTING DECISION UPDATE
  Original prediction + Lineup adjustment = Final prediction
  
  Example:
    Original: Paul Skenes vs CHC → 0.64 runs
    CHC Lineup: 7 RHH vs Skenes (RHP) → -0.4 adjustment
    Final Prediction: 1.04 runs
    Decision: Tier 2 instead of Elite

┌─────────────────────────────────────────────────────────────┐
│  DATA AVAILABILITY CHECKLIST                                │
├─────────────────────────────────────────────────────────────┤
│  Source                │ Handedness │ Timing    │ Status   │
├────────────────────────┼────────────┼───────────┼──────────┤
│  ESPN API              │ ✅ Yes     │ T-90m     │ Active   │
│  MLB.com               │ ✅ Yes     │ T-90m     │ Official │
│  Baseball-Reference    │ ✅ Yes     │ T-60m     │ Delayed  │
│  Baseball Press        │ ✅ Yes     │ T-60m     │ Active   │
│  RotoWire              │ ✅ Yes     │ T-60m     │ Active   │
│  Team Twitter          │ ✅ Yes     │ T-90m     │ Official │
└─────────────────────────────────────────────────────────────┘
"""

print(framework)

# Implementation Plan
print("\n" + "="*70)
print("IMPLEMENTATION PLAN FOR v370")
print("="*70)

plan = """
NEW FEATURE: lineup_strength_vs_hand

Files to Create:
  1. v369_production/core/fetch_confirmed_lineups.py
     - Poll ESPN rosters endpoint every 15 min starting T-120
     - Detect when lineups are confirmed (no more TBD)
     - Extract batter handedness for each spot 1-9
     - Store in daily_predictions/{date}_confirmed_lineups.json

  2. v369_production/core/analyze_platoon_matchups.py
     - Input: Confirmed lineups + Pitcher handedness
     - Calculate platoon advantage % for each team
     - Lookup historical OPS vs LHP/RHP
     - Output: Lineup strength score (0.0 - 2.0)

  3. v369_production/core/adjust_predictions.py
     - Input: Base prediction + Lineup strength score
     - Apply adjustment: base_pred × lineup_factor
     - Re-classify tiers based on adjusted prediction
     - Output: Final betting recommendation

Workflow:
  10:00 AM PT → Run base predictions (no lineup data)
  11:00 AM PT → Check for confirmed lineups
  11:30 AM PT → Run lineup-adjusted predictions
  11:45 AM PT → Final betting decisions
  12:00 PM PT → First pitch

Data Schema:
  confirmed_lineup = {
    "game_id": "401814693",
    "team": "Chicago Cubs",
    "pitcher": "Justin Steele",
    "pitcher_hand": "LHP",
    "batting_order": [
      {"spot": 1, "name": "Nico Hoerner", "hand": "R", "pos": "2B"},
      {"spot": 2, "name": "Ian Happ", "hand": "S", "pos": "LF"},
      ...
    ],
    "platoon_advantage_pct": 0.67,  # % with advantage vs LHP
    "avg_ops_vs_lhp": 0.789,
    "lineup_strength_score": 1.15   # 1.0 = neutral, >1 = stronger
  }

Expected Improvement:
  • Current: 62.4% win rate
  • With Lineup Analysis: 65-67% win rate
  • Edge: +2-3% from platoon optimization
  
Timeline: 3-5 days to implement
"""

print(plan)

# Create sample data fetcher
print("\n" + "="*70)
print("SAMPLE: Fetch Today's Confirmed Lineups")
print("="*70)

# Check today's games for confirmed lineups
today = "20260408"
url = f"{BASE_URL}/events"
params = {"dates": today}

data = get_json(url, params)

if data and data.get('items'):
    print(f"\nToday's games: {len(data['items'])}")
    print("\nChecking for confirmed lineups...")
    
    confirmed_count = 0
    pending_count = 0
    
    for item in data['items'][:5]:  # Check first 5 games
        game_ref = item.get('$ref')
        game = get_json(game_ref)
        if not game:
            continue
        
        game_id = game.get('id')
        comp = game.get('competitions', [{}])[0]
        
        # Check roster status
        roster_url = f"{BASE_URL}/events/{game_id}/competitions/{game_id}/rosters"
        roster = get_json(roster_url)
        
        if roster and roster.get('rosters'):
            # Check if we have actual players or TBD
            has_players = False
            for r in roster.get('rosters', []):
                if r.get('entries') and len(r.get('entries', [])) > 5:
                    has_players = True
                    break
            
            if has_players:
                confirmed_count += 1
                status = "✅ CONFIRMED"
            else:
                pending_count += 1
                status = "⏳ PENDING"
        else:
            pending_count += 1
            status = "⏳ PENDING"
        
        # Get team names
        teams = []
        for c in comp.get('competitors', []):
            team_ref = c.get('team', {}).get('$ref')
            if team_ref:
                team = get_json(team_ref)
                teams.append(team.get('abbreviation', 'TBD'))
        
        game_time = game.get('date', '')[11:16] if game.get('date') else 'TBD'
        print(f"  {game_time} | {' @ '.join(teams)} | {status}")
    
    print(f"\nSummary: {confirmed_count} confirmed, {pending_count} pending")
    print(f"\n💡 Recommendation: Check again at 11:00 AM PT for confirmed lineups")

print("\n" + "="*70)
print("✨ LINEUP ANALYST FRAMEWORK COMPLETE")
print("="*70)
print("\n📋 Next Steps:")
print("   1. Implement fetch_confirmed_lineups.py")
print("   2. Build platoon matchup calculator")
print("   3. Test on historical 2025 data")
print("   4. Deploy as v370 feature")
print("\n🔍 Data Source: ESPN API (rosters endpoint)")
print("⏰ Timing: Check at T-90 minutes (11:00 AM PT for most games)")
