#!/usr/bin/env python3
"""
noesis_mlb_v369_live.py — Live daily predictions for Noesis MLB v369
April 8, 2026
"""
import requests
import json
import pandas as pd
import subprocess
from datetime import datetime
from pathlib import Path

print('='*70)
print('NOESIS MLB v369 — LIVE DAILY PREDICTOR')
print(f'Date: {datetime.now().strftime("%Y-%m-%d")}')
print('='*70)

BASE_URL = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_json(url, params=None):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        return resp.json()
    except:
        return None

# Step 1: Fetch today's games
print("\n📅 Fetching today's games...")
today = "20260408"  # April 8, 2026
url = f"{BASE_URL}/events"
data = get_json(url, params={"dates": today})

if not data:
    print("❌ Failed to fetch games")
    exit(1)

games = []
for item in data.get('items', []):
    game_ref = item.get('$ref')
    if not game_ref:
        continue
    
    game = get_json(game_ref)
    if not game:
        continue
    
    comp = game.get('competitions', [{}])[0]
    
    # Get teams
    teams = {}
    for c in comp.get('competitors', []):
        team_ref = c.get('team', {}).get('$ref')
        team = get_json(team_ref) if team_ref else {}
        side = c.get('homeAway')
        teams[side] = {
            'name': team.get('name', 'TBD'),
            'abbr': team.get('abbreviation', 'TBD'),
            'id': c.get('id')
        }
    
    # Get probable starters if available
    home_pitcher = "TBD"
    away_pitcher = "TBD"
    
    for c in comp.get('competitors', []):
        roster_ref = c.get('roster', {}).get('$ref')
        if roster_ref:
            roster = get_json(roster_ref)
            if roster:
                for entry in roster.get('entries', []):
                    if entry.get('position', {}).get('abbreviation') == 'SP':
                        athlete_ref = entry.get('athlete', {}).get('$ref')
                        athlete = get_json(athlete_ref) if athlete_ref else {}
                        pitcher_name = athlete.get('displayName', 'TBD')
                        
                        if c.get('homeAway') == 'home':
                            home_pitcher = pitcher_name
                        else:
                            away_pitcher = pitcher_name
    
    games.append({
        'game_id': game.get('id'),
        'time': game.get('date', ''),
        'home_team': teams.get('home', {}).get('name', 'TBD'),
        'away_team': teams.get('away', {}).get('name', 'TBD'),
        'home_abbr': teams.get('home', {}).get('abbr', 'TBD'),
        'away_abbr': teams.get('away', {}).get('abbr', 'TBD'),
        'home_pitcher': home_pitcher,
        'away_pitcher': away_pitcher,
        'status': comp.get('status', {}).get('type', {}).get('name', 'SCHEDULED')
    })

print(f"✅ Found {len(games)} games today")

# Step 2: Get pitcher stats from our database
print("\n🎯 Loading pitcher database...")
pitcher_db = pd.read_csv('data/processed/model_data_v4.csv')

# Get most recent stats for each pitcher
latest_stats = {}
for pitcher_name in pitcher_db['pitcher_name'].unique():
    pitcher_games = pitcher_db[pitcher_db['pitcher_name'] == pitcher_name]
    if len(pitcher_games) > 0:
        # Get most recent season's average stats
        latest_year = pitcher_games['year'].max()
        latest = pitcher_games[pitcher_games['year'] == latest_year].iloc[0]
        latest_stats[pitcher_name] = {
            'era': latest['pitcher_era'],
            'whip': latest['pitcher_whip'],
            'k9': latest['pitcher_k9'],
            'bb9': latest['pitcher_bb9'],
            'ip': latest['pitcher_ip'],
            'k_pct': latest['pitcher_k_pct'],
            'hr_pct': latest['pitcher_hr_pct'],
            'is_lhp': latest['is_lhp']
        }

print(f"✅ Loaded {len(latest_stats)} pitchers from database")

# Step 3: Make predictions
print("\n🔮 Generating predictions...")

# Load the trained model
import pickle
from sklearn.ensemble import GradientBoostingRegressor

# Train fresh model on all historical data
df_train = pitcher_db[pitcher_db['year'].isin([2021, 2022, 2023, 2025])]

features = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'is_lhp'
]

X_train = df_train[features].fillna(0)
y_train = df_train['first_5_runs_allowed']

model = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

print("✅ Model trained on historical data")

# Predict for today's games
predictions = []

for game in games:
    for side in ['home', 'away']:
        pitcher_name = game[f'{side}_pitcher']
        
        if pitcher_name == 'TBD':
            continue
        
        # Get pitcher stats
        stats = latest_stats.get(pitcher_name)
        if not stats:
            # Use league average
            stats = {
                'era': 4.00, 'whip': 1.30, 'k9': 8.0,
                'bb9': 3.0, 'ip': 100, 'k_pct': 0.20,
                'hr_pct': 0.03, 'is_lhp': 0
            }
        
        # Create feature vector
        X = [[
            stats['era'], stats['whip'], stats['k9'],
            stats['bb9'], stats['ip'], stats['k_pct'],
            stats['hr_pct'], stats['is_lhp']
        ]]
        
        pred_runs = model.predict(X)[0]
        
        # Determine tier and action
        if pred_runs < 1.5:
            tier = "TIER 1"
            action = "BET 1.5x ($375)"
            confidence = "HIGH"
        elif pred_runs < 2.5:
            tier = "TIER 2"
            action = "BET 1.0x ($250)"
            confidence = "MEDIUM"
        else:
            tier = "TIER 3"
            action = "NO BET"
            confidence = "LOW"
        
        predictions.append({
            'date': '2026-04-08',
            'time': game['time'][11:16] if len(game['time']) > 16 else 'TBD',
            'game': f"{game['away_abbr']} @ {game['home_abbr']}",
            'pitcher': pitcher_name,
            'side': side.upper(),
            'is_lhp': 'LHP' if stats['is_lhp'] else 'RHP',
            'era': round(stats['era'], 2),
            'predicted_runs': round(pred_runs, 2),
            'tier': tier,
            'confidence': confidence,
            'action': action
        })

print(f"✅ Generated {len(predictions)} predictions")

# Step 4: Display results
print("\n" + "="*70)
print("TODAY'S PREDICTIONS — April 8, 2026")
print("="*70)

# Sort by tier
tier_order = {'TIER 1': 0, 'TIER 2': 1, 'TIER 3': 2}
predictions.sort(key=lambda x: tier_order.get(x['tier'], 3))

for pred in predictions:
    print(f"\n{pred['time']} | {pred['game']}")
    print(f"  Pitcher: {pred['pitcher']} ({pred['is_lhp']}, ERA: {pred['era']})")
    print(f"  Predicted: {pred['predicted_runs']} runs | {pred['tier']} | {pred['confidence']}")
    print(f"  ACTION: {pred['action']}")

# Step 5: Save to Google Sheets
print("\n📊 Saving to Google Sheets...")

# Prepare data for sheet
headers = ['Date', 'Time', 'Game', 'Pitcher', 'Side', 'Hand', 'ERA', 'Predicted', 'Tier', 'Confidence', 'Action']
values = [headers]

for pred in predictions:
    row = [
        pred['date'], pred['time'], pred['game'],
        pred['pitcher'], pred['side'], pred['is_lhp'],
        pred['era'], pred['predicted_runs'],
        pred['tier'], pred['confidence'], pred['action']
    ]
    values.append(row)

# Get sheet ID
with open('/root/mlb-first5/SHEET_ID.txt', 'r') as f:
    sheet_id = f.read().strip()

# Add to new sheet/tab
values_json = json.dumps(values)

result = subprocess.run(
    [
        "gog", "sheets", "update", sheet_id,
        "Todays_Picks!A1:K100",  # New tab for today's picks
        "--values-json", values_json,
        "--input", "USER_ENTERED"
    ],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Predictions saved to Google Sheets!")
    print(f"   View: https://docs.google.com/spreadsheets/d/{sheet_id}")
else:
    print(f"❌ Error saving to sheet: {result.stderr}")

# Also save locally
with open('todays_predictions_v369.json', 'w') as f:
    json.dump(predictions, f, indent=2)

print(f"\n💾 Local save: todays_predictions_v369.json")

# Summary
bets_tier1 = sum(1 for p in predictions if p['tier'] == 'TIER 1')
bets_tier2 = sum(1 for p in predictions if p['tier'] == 'TIER 2')
total_bets = bets_tier1 + bets_tier2

print("\n" + "="*70)
print("DAILY SUMMARY")
print("="*70)
print(f"Total Games: {len(games)}")
print(f"Total Pitchers Analyzed: {len(predictions)}")
print(f"Tier 1 Bets (High Conviction): {bets_tier1}")
print(f"Tier 2 Bets (Medium Conviction): {bets_tier2}")
print(f"Total Recommended Bets: {total_bets}")
print(f"Expected Stake: ${bets_tier1 * 375 + bets_tier2 * 250}")

print("\n" + "="*70)
print("✨ Noesis MLB v369 — Predictions Complete!")
print("="*70)
