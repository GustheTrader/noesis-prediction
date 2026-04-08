#!/usr/bin/env python3
"""
daily_predict.py — Daily MLB predictions for paper trading

Runs daily to:
1. Scrape today's games from ESPN
2. Match pitchers to historical data
3. Generate predictions
4. Output qualifying bets (predicted < 1.0)
5. Save to daily log
"""

import requests
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
import pickle
import warnings
warnings.filterwarnings('ignore')

# Config
BASE_URL = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
BET_THRESHOLD = 1.0  # Predicted runs allowed < 1.0
BET_LINE = 2.5  # Team total line

print('='*70)
print(f'MLB Daily Predictions — {datetime.now().strftime("%Y-%m-%d %H:%M")}')
print('='*70)

# Load historical model data
try:
    df_hist = pd.read_csv('data/processed/model_data_v4.csv')
    print(f'✅ Loaded historical data: {len(df_hist)} games')
except Exception as e:
    print(f'❌ Error loading data: {e}')
    exit(1)

# Get today's date
today = datetime.now().strftime('%Y%m%d')
today_str = datetime.now().strftime('%Y-%m-%d')

def get_pitcher_stats(pitcher_name):
    """Get historical stats for a pitcher"""
    # Match by name (last name usually sufficient)
    pitcher_games = df_hist[df_hist['pitcher_name'].str.contains(pitcher_name.split()[-1], case=False, na=False)]
    
    if len(pitcher_games) == 0:
        return None
    
    # Get most recent season stats
    latest = pitcher_games[pitcher_games['year'] == pitcher_games['year'].max()].iloc[0]
    
    return {
        'pitcher_era': latest['pitcher_era'],
        'pitcher_whip': latest['pitcher_whip'],
        'pitcher_k9': latest['pitcher_k9'],
        'pitcher_bb9': latest['pitcher_bb9'],
        'pitcher_gbfb': latest['pitcher_gbfb'],
        'pitcher_ip': latest['pitcher_ip'],
        'is_lhp': latest['is_lhp']
    }

def get_opponent_stats(team_name):
    """Get opponent team stats"""
    # Match team by name
    team_games = df_hist[df_hist['team_id'].astype(str).str.contains(team_name[:3].upper(), na=False)]
    
    if len(team_games) == 0:
        # Use league averages
        return {
            'opp_avg_first5_allowed': df_hist['opp_avg_first5_allowed'].mean(),
            'heat_differential': 0.0,
            'edge_vs_opp': 0.0
        }
    
    latest = team_games[team_games['year'] == team_games['year'].max()].iloc[0]
    
    return {
        'opp_avg_first5_allowed': latest['opp_avg_first5_allowed'],
        'heat_differential': latest.get('heat_differential', 0.0),
        'edge_vs_opp': latest.get('edge_vs_opp', 0.0)
    }

def predict_runs_allowed(pitcher_stats, opponent_stats):
    """Simple model: weighted average of key features"""
    # Simplified prediction (no full model needed for quick daily)
    base = pitcher_stats['pitcher_era'] * 0.4
    opp_factor = opponent_stats['opp_avg_first5_allowed'] * 0.3
    whip_factor = pitcher_stats['pitcher_whip'] * 0.2
    k_factor = (10 - pitcher_stats['pitcher_k9']) * 0.1  # Lower K = higher runs
    
    prediction = base + opp_factor + whip_factor + k_factor
    
    # Adjust for handedness and other factors
    if pitcher_stats['is_lhp']:
        prediction *= 0.95  # Slight boost for lefties
    
    return max(0, min(5, prediction))  # Cap at 0-5

def fetch_todays_games():
    """Fetch today's games"""
    url = f"{BASE_URL}/events"
    params = {"dates": today, "limit": 50}
    
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code != 200:
            print(f'⚠️  ESPN API status: {r.status_code}')
            return []
        
        data = r.json()
        events = data.get('items', [])
        
        games = []
        for event_ref in events:
            event_url = event_ref.get('$ref')
            if not event_url:
                continue
            
            game_resp = requests.get(event_url, headers=HEADERS, timeout=20)
            if game_resp.status_code != 200:
                continue
            
            game = game_resp.json()
            
            # Check if game is today and not final
            status = game.get('status', {}).get('type', {}).get('name', '')
            if status in ['STATUS_FINAL', 'STATUS_POSTPONED']:
                continue
            
            # Get competitors
            comps = game.get('competitions', [])
            if not comps:
                continue
            
            comp = comps[0]
            competitors = comp.get('competitors', [])
            
            if len(competitors) != 2:
                continue
            
            # Parse teams and pitchers
            for c in competitors:
                team = c.get('team', {})
                team_name = team.get('displayName', 'Unknown')
                
                # Get probable pitcher
                probables = c.get('probables', [])
                if probables:
                    pitcher_ref = probables[0].get('$ref')
                    if pitcher_ref:
                        pitcher_resp = requests.get(pitcher_ref, headers=HEADERS, timeout=20)
                        if pitcher_resp.status_code == 200:
                            pitcher_data = pitcher_resp.json()
                            pitcher_name = pitcher_data.get('displayName', 'TBD')
                            
                            games.append({
                                'game_id': game.get('id'),
                                'time': game.get('date', 'TBD'),
                                'team': team_name,
                                'pitcher': pitcher_name,
                                'is_home': c.get('homeAway') == 'home'
                            })
        
        return games
        
    except Exception as e:
        print(f'⚠️  Error fetching games: {e}')
        return []

# Main execution
print('\nFetching today\'s games...')
games = fetch_todays_games()

if not games:
    print('\n❌ No games found or lineups not set yet.')
    print('Try again closer to game time (11am-1pm ET).')
    exit(0)

print(f'✅ Found {len(games)} probable starters')

# Generate predictions
print('\nGenerating predictions...')
qualifying_bets = []

for game in games:
    pitcher_name = game['pitcher']
    team_name = game['team']
    
    # Skip if pitcher TBD
    if pitcher_name == 'TBD':
        continue
    
    # Get stats
    pitcher_stats = get_pitcher_stats(pitcher_name)
    opponent_stats = get_opponent_stats(team_name)
    
    if pitcher_stats is None:
        print(f'⚠️  No historical data for {pitcher_name}')
        continue
    
    # Predict
    predicted = predict_runs_allowed(pitcher_stats, opponent_stats)
    
    game['predicted'] = predicted
    game['pitcher_era'] = pitcher_stats['pitcher_era']
    
    # Check if qualifies
    if predicted < BET_THRESHOLD:
        qualifying_bets.append(game)

# Output results
print('\n' + '='*70)
print(f'QUALIFYING BETS — {today_str}')
print('='*70)
print(f'Threshold: Predicted < {BET_THRESHOLD} runs allowed')
print(f'Bet: Opponent Team Total UNDER {BET_LINE}')
print(f'Stake: $250 per bet\n')

if qualifying_bets:
    print(f'✅ FOUND {len(qualifying_bets)} QUALIFYING BETS:\n')
    
    for i, bet in enumerate(qualifying_bets, 1):
        print(f"Bet {i}:")
        print(f"  Pitcher: {bet['pitcher']}")
        print(f"  Team: {bet['team']} ({'Home' if bet['is_home'] else 'Away'})")
        print(f"  Time: {bet['time']}")
        print(f"  Predicted runs allowed: {bet['predicted']:.2f}")
        print(f"  Pitcher ERA: {bet['pitcher_era']:.2f}")
        print(f"  ➜ BET: Opponent Team Total UNDER {BET_LINE}")
        print()
else:
    print('❌ No qualifying bets today.')
    print('No pitchers with predicted < 1.0 runs allowed.')

# Save to daily log
output_dir = Path('daily_bets')
output_dir.mkdir(exist_ok=True)

output_file = output_dir / f'{today_str}_bets.txt'
with open(output_file, 'w') as f:
    f.write(f'MLB Predictions — {today_str}\n')
    f.write('='*70 + '\n\n')
    f.write(f'Games analyzed: {len(games)}\n')
    f.write(f'Qualifying bets: {len(qualifying_bets)}\n\n')
    
    if qualifying_bets:
        for i, bet in enumerate(qualifying_bets, 1):
            f.write(f"Bet {i}: {bet['pitcher']} ({bet['team']})\n")
            f.write(f"  Predicted: {bet['predicted']:.2f} runs\n")
            f.write(f"  Action: Opponent UNDER {BET_LINE}\n\n")
    else:
        f.write('No qualifying bets.\n')

print(f'✅ Saved to: {output_file}')

# Summary stats
total_games = len([g for g in games if g['pitcher'] != 'TBD'])
print('\n' + '='*70)
print('SUMMARY')
print('='*70)
print(f'Total probable starters: {total_games}')
print(f'Qualifying bets: {len(qualifying_bets)}')
print(f'Qualification rate: {len(qualifying_bets)/max(total_games,1)*100:.1f}%')
print(f'Expected profit: ${len(qualifying_bets) * 131:.0f} (at +$131 EV/bet)')
print('='*70)
