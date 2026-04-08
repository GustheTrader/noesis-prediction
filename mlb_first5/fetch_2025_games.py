#!/usr/bin/env python3
"""
fetch_2025_games.py — Fetch 2025 season games with F5 scores from ESPN play-by-play
"""
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

BASE_URL = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_json(url, params=None):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        return resp.json()
    except:
        return None

def get_f5_from_pbp(game_id):
    """Get F5 scores from play-by-play"""
    plays_url = f"{BASE_URL}/events/{game_id}/competitions/{game_id}/plays"
    
    data = get_json(plays_url, params={"page": 1})
    if not data:
        return None, None
    
    total_pages = data.get('pageCount', 1)
    
    # Start from middle pages where F5 usually is
    start_page = max(1, int(total_pages * 0.4))
    
    f5_away = None
    f5_home = None
    
    for page in range(start_page, total_pages + 1):
        data = get_json(plays_url, params={"page": page})
        if not data:
            continue
        
        for play in data.get('items', []):
            period = play.get('period', {})
            inning = period.get('number', 0)
            
            if inning == 5:
                away = play.get('awayScore')
                home = play.get('homeScore')
                if away is not None:
                    f5_away = away
                if home is not None:
                    f5_home = home
            
            if inning > 5:
                return f5_away, f5_home
    
    return f5_away, f5_home

def fetch_game_details(game_url):
    """Fetch game details"""
    game = get_json(game_url)
    if not game:
        return None
    
    comp = game.get('competitions', [{}])[0]
    
    # Check status
    status_url = comp.get('status', {}).get('$ref')
    if not status_url:
        return None
    
    status = get_json(status_url)
    if not status or status.get('type', {}).get('name') != 'STATUS_FINAL':
        return None
    
    # Get teams
    teams = {}
    for c in comp.get('competitors', []):
        team_ref = c.get('team', {}).get('$ref')
        team = get_json(team_ref) if team_ref else {}
        side = c.get('homeAway')
        teams[side] = {
            'name': team.get('name', 'Unknown'),
            'abbr': team.get('abbreviation', 'UNK'),
            'id': c.get('id')
        }
    
    # Get F5 scores from PBP
    f5_away, f5_home = get_f5_from_pbp(game['id'])
    
    return {
        'event_id': game['id'],
        'date': game.get('date', '')[:10],
        'home_team_name': teams.get('home', {}).get('name'),
        'away_team_name': teams.get('away', {}).get('name'),
        'home_team_id': teams.get('home', {}).get('id'),
        'away_team_id': teams.get('away', {}).get('id'),
        'home_first5_runs': f5_home,
        'away_first5_runs': f5_away,
        'season': 2025
    }

def fetch_season(year, start_month=3, end_month=10):
    """Fetch entire season"""
    print(f"\n📅 Fetching {year} season...")
    
    games = []
    
    for month in range(start_month, end_month + 1):
        for day in range(1, 32):
            try:
                date = datetime(year, month, day)
            except:
                continue
            
            date_str = date.strftime('%Y%m%d')
            url = f"{BASE_URL}/events"
            data = get_json(url, params={"dates": date_str})
            
            if not data:
                continue
            
            items = data.get('items', [])
            if not items:
                continue
            
            print(f"  {date.strftime('%Y-%m-%d')}: {len(items)} games", end='\r')
            
            for item in items:
                game_ref = item.get('$ref')
                if game_ref:
                    game = fetch_game_details(game_ref)
                    if game and game['home_first5_runs'] is not None:
                        games.append(game)
    
    print(f"\n✅ Fetched {len(games)} games with F5 data")
    return games

def main():
    print("="*60)
    print("Fetching 2025 MLB Season with Play-by-Play F5 Scores")
    print("="*60)
    
    games = fetch_season(2025)
    
    # Save
    output_file = '/root/noesis-prediction/mlb_first5/data/raw/games_2025.json'
    with open(output_file, 'w') as f:
        json.dump(games, f, indent=2)
    
    print(f"\n💾 Saved to: {output_file}")
    
    # Show sample
    print(f"\nSample games:")
    for g in games[:3]:
        print(f"  {g['date']}: {g['away_team_name']} @ {g['home_team_name']}")
        print(f"    F5: {g['away_first5_runs']}-{g['home_first5_runs']}")

if __name__ == "__main__":
    main()
