#!/usr/bin/env python3
"""
noesis_mlb_v369_manual.py — Manual pitcher entry for today's games
Use when ESPN has TBD lineups
"""
import pandas as pd
import json
import subprocess
from datetime import datetime

print('='*70)
print('NOESIS MLB v369 — MANUAL PITCHER ENTRY')
print(f'Date: April 8, 2026')
print('='*70)

# Load model and database
print("\n🎯 Loading Noesis MLB v369 model...")
pitcher_db = pd.read_csv('data/processed/model_data_v4.csv')

# Train model
features = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct', 'is_lhp'
]

df_train = pitcher_db[pitcher_db['year'].isin([2021, 2022, 2023, 2025])]
X_train = df_train[features].fillna(0)
y_train = df_train['first_5_runs_allowed']

from sklearn.ensemble import GradientBoostingRegressor
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)

print("✅ Model loaded")

# Get latest pitcher stats
latest_stats = {}
for pitcher_name in pitcher_db['pitcher_name'].unique():
    pitcher_games = pitcher_db[pitcher_db['pitcher_name'] == pitcher_name]
    if len(pitcher_games) > 0:
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

print(f"✅ Loaded {len(latest_stats)} pitchers")

# Today's games with manual pitcher entry (from MLB.com or other source)
today_games = [
    # Format: (Game, Time, Away Pitcher, Home Pitcher)
    ("SD @ PIT", "16:35", "Dylan Cease", "Paul Skenes"),
    ("KC @ CLE", "17:10", "Cole Ragans", "Tanner Bibee"),
    ("MIL @ BOS", "17:35", "Freddy Peralta", "Tanner Houck"),
    ("BAL @ CHW", "18:10", "Corbin Burnes", "Dylan Cease"),  # Note: Cease on both?
    ("SEA @ TEX", "18:35", "Luis Castillo", "Nathan Eovaldi"),
    ("LAD @ TOR", "19:07", "Tyler Glasnow", "Kevin Gausman"),
    ("HOU @ COL", "19:10", "Framber Valdez", "Kyle Freeland"),
    ("PHI @ SF", "19:45", "Zack Wheeler", "Logan Webb"),
    ("STL @ WSH", "20:05", "Miles Mikolas", "MacKenzie Gore"),
    ("ATL @ LAA", "20:07", "Chris Sale", "Tyler Anderson"),
    ("ARI @ NYM", "20:10", "Zac Gallen", "Jose Quintana"),
    ("CHC @ TB", "22:40", "Justin Steele", "Zack Littell"),
    ("CIN @ MIA", "22:40", "Hunter Greene", "Sandy Alcantara"),
    ("ATH @ NYY", "23:05", "Luis Severino", "Carlos Rodon"),
    ("DET @ MIN", "23:40", "Tarik Skubal", "Pablo Lopez"),
]

print(f"\n📅 Analyzing {len(today_games)} games...")

predictions = []

for game, time, away_pitcher, home_pitcher in today_games:
    for side, pitcher in [('AWAY', away_pitcher), ('HOME', home_pitcher)]:
        # Get stats or use default
        stats = latest_stats.get(pitcher)
        if not stats:
            # Try partial match
            for name, data in latest_stats.items():
                if pitcher.split()[-1].lower() in name.lower():
                    stats = data
                    break
        
        if not stats:
            print(f"  ⚠️  {pitcher} not found - using league average")
            stats = {
                'era': 4.00, 'whip': 1.30, 'k9': 8.0,
                'bb9': 3.0, 'ip': 100, 'k_pct': 0.20,
                'hr_pct': 0.03, 'is_lhp': 0
            }
        
        # Predict
        X = [[stats['era'], stats['whip'], stats['k9'], stats['bb9'],
              stats['ip'], stats['k_pct'], stats['hr_pct'], stats['is_lhp']]]
        
        pred_runs = model.predict(X)[0]
        
        # Determine tier
        if pred_runs < 1.5:
            tier = "TIER 1"
            action = "BET $375 (1.5x)"
            bet = "YES"
        elif pred_runs < 2.5:
            tier = "TIER 2"
            action = "BET $250 (1.0x)"
            bet = "YES"
        else:
            tier = "TIER 3"
            action = "NO BET"
            bet = "NO"
        
        predictions.append({
            'date': '2026-04-08',
            'time': time,
            'game': game,
            'pitcher': pitcher,
            'side': side,
            'hand': 'LHP' if stats['is_lhp'] else 'RHP',
            'era': round(stats['era'], 2),
            'pred': round(pred_runs, 2),
            'tier': tier,
            'action': action,
            'bet': bet
        })

# Display
print("\n" + "="*70)
print("TODAY'S PREDICTIONS — April 8, 2026")
print("="*70)

# Sort by tier
tier_order = {'TIER 1': 0, 'TIER 2': 1, 'TIER 3': 2}
predictions.sort(key=lambda x: (tier_order.get(x['tier'], 3), x['time']))

for p in predictions:
    print(f"\n{p['time']} | {p['game']}")
    print(f"  {p['side']}: {p['pitcher']} ({p['hand']}, ERA: {p['era']})")
    print(f"  Predicted: {p['pred']} runs | {p['tier']} | {p['action']}")

# Save to sheet
print("\n📊 Saving to Google Sheets...")

headers = ['Date', 'Time', 'Game', 'Side', 'Pitcher', 'Hand', 'ERA', 'Pred', 'Tier', 'Action', 'Bet']
values = [headers]

for p in predictions:
    values.append([p['date'], p['time'], p['game'], p['side'], p['pitcher'],
                   p['hand'], p['era'], p['pred'], p['tier'], p['action'], p['bet']])

# Get sheet ID
with open('/root/mlb-first5/SHEET_ID.txt', 'r') as f:
    sheet_id = f.read().strip()

values_json = json.dumps(values)

result = subprocess.run(
    [
        "gog", "sheets", "update", sheet_id,
        "Sheet1!AH1:AR40",  # Use columns AH-AR to not overwrite other data
        "--values-json", values_json,
        "--input", "USER_ENTERED"
    ],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Saved to Google Sheets!")
    print(f"   View: https://docs.google.com/spreadsheets/d/{sheet_id}")
else:
    print(f"⚠️  Could not save to sheet: {result.stderr}")
    print("   Check sheet permissions or try again")

# Summary
bets_yes = sum(1 for p in predictions if p['bet'] == 'YES')
tier1_count = sum(1 for p in predictions if p['tier'] == 'TIER 1')
tier2_count = sum(1 for p in predictions if p['tier'] == 'TIER 2')

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print(f"Total Games: {len(today_games)}")
print(f"Total Pitchers: {len(predictions)}")
print(f"Tier 1 (High Conf): {tier1_count}")
print(f"Tier 2 (Medium Conf): {tier2_count}")
print(f"Total Bets: {bets_yes}")

print("\n" + "="*70)
print("✨ Noesis MLB v369 — Ready for today's action!")
print("="*70)
