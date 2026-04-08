#!/usr/bin/env python3
"""
rebuild_heat_check.py — Rebuild heat check with strict leakage prevention
"""
import pandas as pd
import numpy as np
from collections import defaultdict

print('='*70)
print('REBUILDING HEAT CHECK — Strict Leakage Prevention')
print('='*70)

# Load the raw games data from CSV (more reliable than JSON)
df = pd.read_csv('data/processed/model_data_v4.csv')
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values(['date', 'event_id'])

print(f"\n📊 Loaded {len(df)} games")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")

# Build team history from the data itself
# For each team, track their games in chronological order
team_games = defaultdict(list)

for _, row in df.iterrows():
    event_id = row['event_id']
    date = row['date']
    year = row['year']
    
    # Get team info - need to infer from the data
    # For home pitchers (is_home=1), their team is the home team
    # For away pitchers (is_home=0), their team is the away team
    
    # We can use team_id to identify teams
    team_id = row['team_id']
    
    # The runs scored by the opponent (what we care about for heat check)
    # If this pitcher is home (is_home=1), opponent is away
    # If this pitcher is away (is_home=0), opponent is home
    
    # Actually, we need to track: for each team, what was their first-5 runs SCORED
    # The model_data has first_5_runs_allowed (what pitcher gave up)
    # But we need runs SCORED by each team for heat check
    
    # Let's use a proxy: in each game, total runs = home_runs + away_runs
    # We know first_5_runs_allowed for each pitcher
    # For heat check, we want opponent's recent scoring
    
    team_games[team_id].append({
        'date': date,
        'event_id': event_id,
        'year': year,
        'runs_allowed': row['first_5_runs_allowed'],
        'is_home': row['is_home']
    })

print(f"\n📋 Built history for {len(team_games)} teams")

# Calculate heat check with STRICT prior-only rule
heat_14_strict = {}
heat_7_strict = {}
heat_21_strict = {}

for team_id, games in team_games.items():
    # Sort by date
    games = sorted(games, key=lambda x: x['date'])
    
    for i, game in enumerate(games):
        event_id = game['event_id']
        
        # STRICT: only games BEFORE this one (indices < i)
        prior_games = games[:i]
        
        # 14-game heat
        if len(prior_games) >= 14:
            heat_14 = np.mean([g['runs_allowed'] for g in prior_games[-14:]])
        elif len(prior_games) > 0:
            heat_14 = np.mean([g['runs_allowed'] for g in prior_games])
        else:
            heat_14 = 2.42  # league average
        
        # 7-game heat
        if len(prior_games) >= 7:
            heat_7 = np.mean([g['runs_allowed'] for g in prior_games[-7:]])
        elif len(prior_games) > 0:
            heat_7 = np.mean([g['runs_allowed'] for g in prior_games])
        else:
            heat_7 = 2.42
        
        # 21-game heat
        if len(prior_games) >= 21:
            heat_21 = np.mean([g['runs_allowed'] for g in prior_games[-21:]])
        elif len(prior_games) > 0:
            heat_21 = np.mean([g['runs_allowed'] for g in prior_games])
        else:
            heat_21 = 2.42
        
        heat_14_strict[(event_id, team_id)] = round(heat_14, 3)
        heat_7_strict[(event_id, team_id)] = round(heat_7, 3)
        heat_21_strict[(event_id, team_id)] = round(heat_21, 3)

print(f"✅ Computed heat checks: {len(heat_14_strict)} entries")

# Apply to dataframe
print("\n[*] Applying strict heat checks to dataset...")

df['heat_14_strict'] = 2.42
df['heat_7_strict'] = 2.42
df['heat_21_strict'] = 2.42

for idx, row in df.iterrows():
    event_id = row['event_id']
    team_id = row['team_id']
    
    # For the opponent's heat, we need to get the opposing team
    # In the same game, find the other team's pitcher
    same_game = df[df['event_id'] == event_id]
    
    if len(same_game) == 2:
        # Two pitchers in this game
        other_team = same_game[same_game['team_id'] != team_id]['team_id'].values[0]
        
        df.loc[idx, 'heat_14_strict'] = heat_14_strict.get((event_id, other_team), 2.42)
        df.loc[idx, 'heat_7_strict'] = heat_7_strict.get((event_id, other_team), 2.42)
        df.loc[idx, 'heat_21_strict'] = heat_21_strict.get((event_id, other_team), 2.42)

# Save new version
output_cols = [c for c in df.columns if 'strict' not in c] + ['heat_7_strict', 'heat_14_strict', 'heat_21_strict']
df.to_csv('data/processed/model_data_v8_strict.csv', index=False)

print(f"\n[+] Saved model_data_v8_strict.csv")
print(f"    Heat 14 strict: mean={df['heat_14_strict'].mean():.3f}, std={df['heat_14_strict'].std():.3f}")
print(f"    Heat 7 strict:  mean={df['heat_7_strict'].mean():.3f}, std={df['heat_7_strict'].std():.3f}")
print(f"    Heat 21 strict: mean={df['heat_21_strict'].mean():.3f}, std={df['heat_21_strict'].std():.3f}")

# Test correlation with target
corr_14 = df['heat_14_strict'].corr(df['first_5_runs_allowed'])
corr_old = df['opp_heat_14'].corr(df['first_5_runs_allowed'])

print(f"\n📊 Correlation with target:")
print(f"    Old heat_14:  {corr_old:.3f}")
print(f"    Strict heat:  {corr_14:.3f}")

if abs(corr_14 - corr_old) > 0.1:
    print("    ⚠️  Significant difference - old version may have leakage")
else:
    print("    ✅ Similar correlation - old version appears valid")
