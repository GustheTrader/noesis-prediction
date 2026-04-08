#!/usr/bin/env python3
"""
heat_check_2game.py — 2-game rolling batting average (heat check)
Shorter timeframe for more reactive momentum detection.
For each game, compute each team's avg first-5 runs scored in their LAST 2 games BEFORE this game.
This is LEAK-FREE by design — only uses prior games.
"""
import json
import csv
import numpy as np
from collections import defaultdict

# Load all games
print("[*] Loading games...")
games = []
for yr in [2021, 2022, 2023, 2025]:
    try:
        with open(f'data/raw/games_{yr}.json') as f:
            games.extend(json.load(f))
    except FileNotFoundError:
        print(f"    Warning: games_{yr}.json not found, skipping")
        continue

# Sort by date for proper rolling computation
games.sort(key=lambda x: x['date'])
print(f"    {len(games)} games loaded")

# Build per-team game history: list of (date, first5_runs, event_id, side)
team_history = defaultdict(list)
for g in games:
    ht = g.get('home_team_name', g.get('home_team', 'Unknown'))
    at = g.get('away_team_name', g.get('away_team', 'Unknown'))
    
    home_runs = g.get('home_first5_runs', g.get('first_5_home'))
    away_runs = g.get('away_first5_runs', g.get('first_5_away'))
    
    if home_runs is not None:
        team_history[ht].append((g['date'], home_runs, g['event_id'], 'home'))
    if away_runs is not None:
        team_history[at].append((g['date'], away_runs, g['event_id'], 'away'))

# Sort each team's history by date
for team in team_history:
    team_history[team].sort(key=lambda x: x[0])

print(f"    Teams tracked: {len(team_history)}")

# For each game, look up the team's last 2 games BEFORE this game
heat_lookup = {}

for team, history in team_history.items():
    for i, (date, runs, event_id, side) in enumerate(history):
        # Last 2 games before this one = indices [i-2:i]
        start = max(0, i - 2)
        prior = history[start:i]
        
        if len(prior) >= 1:  # need at least 1 prior game
            avg = sum(r for _, r, _, _ in prior) / len(prior)
        else:
            avg = 2.42  # league average
        
        heat_lookup[(event_id, team)] = round(avg, 3)

print(f"    Heat lookup entries: {len(heat_lookup)}")

# Now load model data and add heat check features
print("[*] Loading model data v4...")
rows = []
with open('data/processed/model_data_v4.csv') as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    for row in reader:
        rows.append(row)
print(f"    {len(rows)} records")

# Build event_id -> game lookup
game_lookup = {}
for g in games:
    game_lookup[g['event_id']] = g

print("[*] Adding 2-game heat check features...")

# Check if columns already exist
if 'opp_heat_2' not in headers:
    new_headers = headers + ['opp_heat_2', 'pitcher_team_heat_2', 'heat_2_differential']
else:
    new_headers = headers

new_rows = []
for row in rows:
    event_id = row.get('event_id', '')
    is_home = int(row.get('is_home', '0'))
    
    game = game_lookup.get(event_id)
    if not game:
        row['opp_heat_2'] = row.get('opp_heat_2', '2.42')
        row['pitcher_team_heat_2'] = row.get('pitcher_team_heat_2', '2.42')
        row['heat_2_differential'] = row.get('heat_2_differential', '0')
        new_rows.append(row)
        continue
    
    # Get team names
    opp_side = 'away' if is_home else 'home'
    opp_team = game.get(f'{opp_side}_team_name', game.get(f'{opp_side}_team', ''))
    
    pitcher_side = 'home' if is_home else 'away'
    pitcher_team = game.get(f'{pitcher_side}_team_name', game.get(f'{pitcher_side}_team', ''))
    
    # Get 2-game heat checks
    opp_heat = heat_lookup.get((event_id, opp_team), 2.42)
    pitcher_team_heat = heat_lookup.get((event_id, pitcher_team), 2.42)
    heat_diff = round(opp_heat - pitcher_team_heat, 3)
    
    row['opp_heat_2'] = str(opp_heat)
    row['pitcher_team_heat_2'] = str(pitcher_team_heat)
    row['heat_2_differential'] = str(heat_diff)
    new_rows.append(row)

# Save v5
with open('data/processed/model_data_v5.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=new_headers)
    writer.writeheader()
    writer.writerows(new_rows)

# Stats
heat_diffs = [float(r['heat_2_differential']) for r in new_rows]
opp_heats = [float(r['opp_heat_2']) for r in new_rows]
print(f"\n[+] Saved model_data_v5.csv ({len(new_rows)} records)")
print(f"    opp_heat_2: mean={np.mean(opp_heats):.3f}, std={np.std(opp_heats):.3f}")
print(f"    heat_2_differential: mean={np.mean(heat_diffs):.3f}, std={np.std(heat_diffs):.3f}")
print(f"\n    🔥 LEAK-FREE: 2-game heat checks only use games BEFORE each prediction")
print(f"    📊 More reactive than 14-game for short-term momentum")
