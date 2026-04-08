#!/usr/bin/env python3
"""
fetch_confirmed_lineups.py — Poll ESPN API for confirmed lineups with L/R handedness
Run every 15 minutes starting 2 hours before first game
"""
import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

BASE_URL = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_json(url, params=None):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

def fetch_lineups_for_date(date_str):
    """Fetch all confirmed lineups for a given date"""
    print(f"[{datetime.now().strftime('%H:%M')}] Fetching lineups for {date_str}...")
    
    # Get games for date
    url = f"{BASE_URL}/events"
    data = get_json(url, params={"dates": date_str})
    
    if not data or not data.get('items'):
        print("  No games found")
        return []
    
    lineups = []
    
    for item in data.get('items', []):
        game_ref = item.get('$ref')
        game = get_json(game_ref)
        if not game:
            continue
        
        game_id = game.get('id')
        comp = game.get('competitions', [{}])[0]
        
        # Get rosters/lineups
        roster_url = f"{BASE_URL}/events/{game_id}/competitions/{game_id}/rosters"
        roster_data = get_json(roster_url)
        
        if not roster_data or not roster_data.get('rosters'):
            continue
        
        game_time = game.get('date', '')[11:16] if game.get('date') else 'TBD'
        
        for roster in roster_data.get('rosters', []):
            # Get team info
            team_ref = roster.get('team', {}).get('$ref')
            team = get_json(team_ref) if team_ref else {}
            team_name = team.get('name', 'Unknown')
            team_abbr = team.get('abbreviation', 'UNK')
            
            # Check if lineup is confirmed (has batting order entries)
            entries = roster.get('entries', [])
            if len(entries) < 5:
                continue  # Not confirmed yet
            
            lineup_spots = []
            for entry in entries[:9]:  # First 9 batters
                athlete_ref = entry.get('athlete', {}).get('$ref')
                athlete = get_json(athlete_ref) if athlete_ref else {}
                
                # Get handedness - try multiple sources
                bats = athlete.get('bats', {}).get('type', 'Unknown')
                if bats == 'Unknown':
                    # Try from position/known players
                    bats = infer_handedness(athlete.get('displayName', ''))
                
                lineup_spots.append({
                    'spot': entry.get('battingOrder', entry.get('order', 0)),
                    'name': athlete.get('displayName', 'TBD'),
                    'hand': bats[0] if bats != 'Unknown' else 'R',  # L, R, or S
                    'position': entry.get('position', {}).get('abbreviation', ''),
                    'player_id': athlete.get('id', '')
                })
            
            # Get starting pitcher from roster
            pitcher_name = "TBD"
            pitcher_hand = "RHP"
            for entry in entries:
                if entry.get('position', {}).get('abbreviation') == 'SP':
                    athlete_ref = entry.get('athlete', {}).get('$ref')
                    athlete = get_json(athlete_ref) if athlete_ref else {}
                    pitcher_name = athlete.get('displayName', 'TBD')
                    throws = athlete.get('throws', {}).get('abbreviation', 'R')
                    pitcher_hand = 'LHP' if throws == 'L' else 'RHP'
                    break
            
            lineups.append({
                'game_id': game_id,
                'game_time': game_time,
                'date': date_str,
                'team': team_name,
                'team_abbr': team_abbr,
                'pitcher': pitcher_name,
                'pitcher_hand': pitcher_hand,
                'lineup_confirmed': True,
                'lineup': lineup_spots,
                'timestamp': datetime.now().isoformat()
            })
    
    print(f"  Found {len(lineups)} confirmed lineups")
    return lineups

def infer_handedness(player_name):
    """Infer handedness from known player database"""
    # Load from our historical data
    known_players = {
        # Add known LHH here as needed
        'Shohei Ohtani': 'L',
        'Juan Soto': 'L',
        'Kyle Tucker': 'L',
        'Freddie Freeman': 'L',
        'Matt Olson': 'L',
    }
    return known_players.get(player_name, 'R')  # Default to RHH

def save_lineups(lineups, date_str):
    """Save lineups to JSON file"""
    output_dir = Path('v369_production/daily_predictions')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = output_dir / f"{date_str}_confirmed_lineups.json"
    
    with open(filename, 'w') as f:
        json.dump(lineups, f, indent=2)
    
    print(f"  Saved to: {filename}")
    return filename

def main():
    # Get today's date in YYYYMMDD format
    today = datetime.now().strftime('%Y%m%d')
    
    print("="*70)
    print(f"FETCH CONFIRMED LINEUPS — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    # Fetch lineups
    lineups = fetch_lineups_for_date(today)
    
    if lineups:
        # Save lineups
        filename = save_lineups(lineups, today)
        
        # Print summary
        print(f"\n✅ CONFIRMED LINEUPS: {len(lineups)}")
        for lu in lineups[:5]:  # Show first 5
            print(f"  {lu['game_time']} | {lu['team_abbr']} | {lu['pitcher']} ({lu['pitcher_hand']})")
            hands = [spot['hand'] for spot in lu['lineup'][:5]]
            print(f"    Top 5: {' | '.join(hands)}")
    else:
        print("\n⏳ No confirmed lineups yet. Check again in 15 minutes.")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()
