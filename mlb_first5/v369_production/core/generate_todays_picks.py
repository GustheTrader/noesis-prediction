#!/usr/bin/env python3
"""
generate_todays_picks.py — Generate paper trade picks for today with confirmed pitchers
"""
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from sklearn.ensemble import GradientBoostingRegressor

print("="*80)
print("NOESIS MLB v369 — TODAY'S PICKS (Paper Trade Evaluation)")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M %S PT')}")
print("="*80)

# ESPN API setup
BASE_URL = "https://sports.core.api.espn.com/v2/sports/baseball/leagues/mlb"
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_json(url, params=None):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

# Load and train model
print("\n" + "="*80)
print("TRAINING MODEL")
print("="*80)

data_path = Path('/root/noesis-prediction/mlb_first5/data/processed/model_data_v4.csv')
if not data_path.exists():
    print(f"❌ Data not found at {data_path}")
    # Try alternate path
    alt_path = Path('/root/mlb-first5/data/processed/model_data_v4.csv')
    if alt_path.exists():
        data_path = alt_path
        print(f"✅ Found data at alternate path")
    else:
        print("❌ Data file not found")
        exit()

df = pd.read_csv(data_path)
print(f"✅ Loaded {len(df)} records")

# Create handedness interactions
df['lhp_x_era'] = df['is_lhp'] * df['pitcher_era']
df['lhp_x_ip'] = df['is_lhp'] * df['pitcher_ip']
df['lhp_x_k9'] = df['is_lhp'] * df['pitcher_k9']
df['lhp_x_bb9'] = df['is_lhp'] * df['pitcher_bb9']
df['lhp_x_hr_pct'] = df['is_lhp'] * df['pitcher_hr_pct']

features = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'is_lhp', 'pitcher_days_rest',
    'lhp_x_era', 'lhp_x_ip', 'lhp_x_k9', 'lhp_x_bb9', 'lhp_x_hr_pct'
]

# Train on 2021-2023
train_df = df[df['year'].isin([2021, 2022, 2023])]
X_train = train_df[features].fillna(0)
y_train = train_df['first_5_runs_allowed']

print(f"Training on {len(X_train)} games...")
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)
print("✅ Model trained")

# Fetch today's games
print("\n" + "="*80)
print("FETCHING CONFIRMED PITCHERS & GAME TIMES")
print("="*80)

today = datetime.now().strftime('%Y%m%d')
games_data = get_json(SCOREBOARD_URL, params={"dates": today})

if not games_data or not games_data.get('events'):
    print("❌ No games found")
    exit()

games = []
for event in games_data.get('events', []):
    name = event.get('name', 'Unknown')
    status = event.get('status', {}).get('type', {}).get('description', 'Unknown')
    status_state = event.get('status', {}).get('type', {}).get('state', 'unknown')
    
    # Get game time (convert UTC to PT)
    game_date = event.get('date', '')
    if game_date:
        utc_time = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
        pt_time = utc_time - timedelta(hours=7)
        pt_time_str = pt_time.strftime('%I:%M %p')
        pt_hour = pt_time.hour
    else:
        pt_time_str = 'TBD'
        pt_hour = 12
    
    # Categorize by time
    if pt_hour < 12:
        time_slot = 'MORNING'
    elif pt_hour < 15:
        time_slot = 'AFTERNOON'
    else:
        time_slot = 'EVENING'
    
    competitions = event.get('competitions', [])
    if not competitions:
        continue
    
    comp = competitions[0]
    game_id = comp.get('id')
    
    # Get teams and pitchers
    teams = {}
    for c in comp.get('competitors', []):
        team = c.get('team', {})
        abbr = team.get('abbreviation', 'TBD')
        side = c.get('homeAway')
        
        # Get confirmed pitcher from probables
        probables = c.get('probables', [])
        if probables:
            pitcher_name = probables[0].get('athlete', {}).get('displayName', 'TBD')
        else:
            pitcher_name = 'TBD'
        
        teams[side] = {
            'abbr': abbr,
            'name': team.get('name', 'TBD'),
            'pitcher': pitcher_name
        }
    
    games.append({
        'game_id': game_id,
        'name': name,
        'pt_time': pt_time_str,
        'pt_hour': pt_hour,
        'time_slot': time_slot,
        'status': status,
        'status_state': status_state,
        'away_team': teams.get('away', {}),
        'home_team': teams.get('home', {})
    })

print(f"\nFound {len(games)} games today:\n")
for g in games:
    away = g['away_team']
    home = g['home_team']
    status_icon = "✅" if g['status_state'] == 'post' else "⏳" if g['status_state'] == 'in' else "🔴"
    print(f"{status_icon} {g['pt_time']} | {g['time_slot']:<10} | {away['abbr']} @ {home['abbr']}")
    print(f"           Pitchers: {away['pitcher']} @ {home['pitcher']}")

# Get pitcher stats from historical data
print("\n" + "="*80)
print("MATCHING PITCHERS TO HISTORICAL STATS")
print("="*80)

# Build pitcher database from historical data
pitcher_stats = {}
for _, row in df.iterrows():
    name = row['pitcher_name']
    if name not in pitcher_stats:
        pitcher_stats[name] = {
            'games': [],
            'avg_era': row['pitcher_era'],
            'avg_whip': row['pitcher_whip'],
            'avg_k9': row['pitcher_k9'],
            'avg_bb9': row['pitcher_bb9'],
            'avg_ip': row['pitcher_ip'],
            'avg_k_pct': row['pitcher_k_pct'],
            'avg_hr_pct': row['pitcher_hr_pct'],
            'is_lhp': row['is_lhp']
        }
    pitcher_stats[name]['games'].append(row['first_5_runs_allowed'])

print(f"✅ Built pitcher database with {len(pitcher_stats)} pitchers")

# Generate predictions for each game
print("\n" + "="*80)
print("GENERATING PREDICTIONS")
print("="*80)

picks = []
unknown_pitchers = []

for g in games:
    # Skip completed games
    if g['status_state'] == 'post':
        continue
    
    away = g['away_team']
    home = g['home_team']
    
    # Check both pitchers
    for side, team in [('away', away), ('home', home)]:
        pitcher_name = team['pitcher']
        opponent = home if side == 'away' else away
        
        if pitcher_name in pitcher_stats:
            stats = pitcher_stats[pitcher_name]
            
            # Create feature vector
            features_dict = {
                'pitcher_era': stats['avg_era'],
                'pitcher_whip': stats['avg_whip'],
                'pitcher_k9': stats['avg_k9'],
                'pitcher_bb9': stats['avg_bb9'],
                'pitcher_ip': stats['avg_ip'],
                'pitcher_k_pct': stats['avg_k_pct'],
                'pitcher_hr_pct': stats['avg_hr_pct'],
                'is_lhp': stats['is_lhp'],
                'pitcher_days_rest': 4  # Assume standard rest
            }
            
            # Add interactions
            features_dict['lhp_x_era'] = features_dict['is_lhp'] * features_dict['pitcher_era']
            features_dict['lhp_x_ip'] = features_dict['is_lhp'] * features_dict['pitcher_ip']
            features_dict['lhp_x_k9'] = features_dict['is_lhp'] * features_dict['pitcher_k9']
            features_dict['lhp_x_bb9'] = features_dict['is_lhp'] * features_dict['pitcher_bb9']
            features_dict['lhp_x_hr_pct'] = features_dict['is_lhp'] * features_dict['pitcher_hr_pct']
            
            # Make prediction
            X_pred = pd.DataFrame([features_dict])[features]
            pred_runs = model.predict(X_pred)[0]
            
            # Adjust for home/away
            if side == 'away':
                pred_runs *= 1.05  # Slight penalty for road
            else:
                pred_runs *= 0.95  # Bonus for home
            
            # Determine tier
            if pred_runs < 1.0:
                tier = 'ELITE'
                stake = 500
            elif pred_runs < 1.5:
                tier = 'TIER 1'
                stake = 375
            elif pred_runs < 2.5:
                tier = 'TIER 2'
                stake = 250
            else:
                tier = 'NO BET'
                stake = 0
            
            if tier != 'NO BET':
                picks.append({
                    'time': g['pt_time'],
                    'time_slot': g['time_slot'],
                    'game': f"{away['abbr']} @ {home['abbr']}",
                    'bet_on': team['abbr'],
                    'side': side,
                    'pitcher': pitcher_name,
                    'opponent': opponent['abbr'],
                    'pred_runs': round(pred_runs, 2),
                    'tier': tier,
                    'stake': stake,
                    'bet': f"{opponent['abbr']} Team Total UNDER 2.5 (First 5)",
                    'odds': -120,
                    'status': g['status'],
                    'state': g['status_state']
                })
        else:
            unknown_pitchers.append({
                'game': f"{away['abbr']} @ {home['abbr']}",
                'team': team['abbr'],
                'pitcher': pitcher_name
            })

if unknown_pitchers:
    print(f"\n⚠️  {len(unknown_pitchers)} pitchers not in database:")
    for u in unknown_pitchers[:5]:
        print(f"   {u['game']}: {u['pitcher']} ({u['team']})")

# Output picks by time slot
print("\n" + "="*80)
print("PAPER TRADE PICKS BY TIME SLOT")
print("="*80)

time_slots = ['MORNING', 'AFTERNOON', 'EVENING']
total_stake = 0
total_bets = 0

for slot in time_slots:
    slot_picks = [p for p in picks if p['time_slot'] == slot]
    if not slot_picks:
        continue
    
    print(f"\n{'='*80}")
    print(f"{slot} GAMES")
    print(f"{'='*80}")
    
    for pick in slot_picks:
        state_icon = "✅" if pick['state'] == 'post' else "⏳" if pick['state'] == 'in' else "🔴"
        print(f"\n{state_icon} {pick['time']} | {pick['game']}")
        print(f"   Pitcher: {pick['pitcher']} ({pick['side']})")
        print(f"   Predicted: {pick['pred_runs']} runs allowed")
        print(f"   Tier: {pick['tier']} | Stake: ${pick['stake']}")
        print(f"   Bet: {pick['bet']}")
        total_stake += pick['stake']
        total_bets += 1

print("\n" + "="*80)
print("PAPER TRADE SUMMARY")
print("="*80)
print(f"Total Bets: {total_bets}")
print(f"Total Stake: ${total_stake:,}")
print(f"Expected Value: ${total_stake * 0.191:.0f} (at 19.1% ROI)")
print(f"Expected Win Rate: ~62%")

# Breakdown by tier
elite = sum(1 for p in picks if p['tier'] == 'ELITE')
tier1 = sum(1 for p in picks if p['tier'] == 'TIER 1')
tier2 = sum(1 for p in picks if p['tier'] == 'TIER 2')

print(f"\nBreakdown:")
print(f"  ELITE (x{elite}): ${elite * 500}")
print(f"  TIER 1 (x{tier1}): ${tier1 * 375}")
print(f"  TIER 2 (x{tier2}): ${tier2 * 250}")

# Save picks
output_dir = Path('/root/noesis-prediction/mlb_first5/v369_production/daily_predictions')
output_dir.mkdir(parents=True, exist_ok=True)
output_file = output_dir / f"{today}_paper_trades.json"

with open(output_file, 'w') as f:
    json.dump({
        'date': today,
        'generated_at': datetime.now().isoformat(),
        'timezone': 'PT',
        'picks': picks,
        'summary': {
            'total_bets': total_bets,
            'total_stake': total_stake,
            'expected_ev': total_stake * 0.191,
            'elite': elite,
            'tier1': tier1,
            'tier2': tier2
        },
        'disclaimer': 'PAPER TRADE ONLY - NOT REAL MONEY'
    }, f, indent=2)

print(f"\n💾 Saved to: {output_file}")

# Also create CSV for easy viewing
csv_file = output_dir / f"{today}_paper_trades.csv"
if picks:
    df_picks = pd.DataFrame(picks)
    df_picks.to_csv(csv_file, index=False)
    print(f"💾 CSV saved to: {csv_file}")
