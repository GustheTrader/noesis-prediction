#!/usr/bin/env python3
"""
heat_check.py — 14-game rolling batting average (heat check)
For each game, compute each team's avg first-5 runs scored in their LAST 14 games BEFORE this game.
This is LEAK-FREE by design — only uses prior games.
"""
import json, csv
from collections import defaultdict, deque

# Load all games
print("[*] Loading games...")
games = []
for yr in [2021, 2022, 2023, 2025]:
    with open(f'data/raw/games_{yr}.json') as f:
        games.extend(json.load(f))

# Sort by date for proper rolling computation
games.sort(key=lambda x: x['date'])
print(f"    {len(games)} games loaded")

# Build per-team game history: list of (date, first5_runs)
team_history = defaultdict(list)
for g in games:
    ht = g['home_team_name']
    at = g['away_team_name']
    team_history[ht].append((g['date'], g['home_first5_runs'], g['event_id'], 'home'))
    team_history[at].append((g['date'], g['away_first5_runs'], g['event_id'], 'away'))

# Sort each team's history by date
for team in team_history:
    team_history[team].sort(key=lambda x: x[0])

# For each game, look up the team's last 14 games BEFORE this game
# Build a lookup: (event_id, side) -> heat_check_value
heat_lookup = {}

for team, history in team_history.items():
    for i, (date, runs, event_id, side) in enumerate(history):
        # Last 14 games before this one = indices [i-14:i]
        start = max(0, i - 14)
        prior = history[start:i]
        if len(prior) >= 3:  # need at least 3 prior games
            avg = sum(r for _, r, _, _ in prior) / len(prior)
        elif len(prior) > 0:
            avg = sum(r for _, r, _, _ in prior) / len(prior)
        else:
            avg = 2.42  # league average
        
        heat_lookup[(event_id, team)] = round(avg, 3)

print(f"    Heat lookup entries: {len(heat_lookup)}")

# Now load model data and add heat check features
print("[*] Loading model data...")
rows = []
with open('data/processed/model_data_v3.csv') as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    for row in reader:
        rows.append(row)
print(f"    {len(rows)} records")

# Need to find the game for each row to get opponent team name
# Build event_id -> game lookup
game_lookup = {}
for g in games:
    game_lookup[g['event_id']] = g

print("[*] Adding heat check features...")
new_headers = headers + ['opp_heat_14', 'pitcher_team_heat_14', 'heat_differential']
new_rows = []
for row in rows:
    event_id = row.get('event_id', '')
    is_home = int(row.get('is_home', '0'))
    
    game = game_lookup.get(event_id)
    if not game:
        row['opp_heat_14'] = '2.42'
        row['pitcher_team_heat_14'] = '2.42'
        row['heat_differential'] = '0'
        new_rows.append(row)
        continue
    
    # Opponent team (the team batting against this pitcher)
    opp_side = 'away' if is_home else 'home'
    opp_team = game.get(f'{opp_side}_team_name', '')
    
    # Pitcher's own team (for comparison)
    pitcher_side = 'home' if is_home else 'away'
    pitcher_team = game.get(f'{pitcher_side}_team_name', '')
    
    # Get heat checks (only prior games — leak-free)
    opp_heat = heat_lookup.get((event_id, opp_team), 2.42)
    pitcher_team_heat = heat_lookup.get((event_id, pitcher_team), 2.42)
    heat_diff = round(opp_heat - pitcher_team_heat, 3)
    
    row['opp_heat_14'] = str(opp_heat)
    row['pitcher_team_heat_14'] = str(pitcher_team_heat)
    row['heat_differential'] = str(heat_diff)
    new_rows.append(row)

# Save v4
with open('data/processed/model_data_v4.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=new_headers)
    writer.writeheader()
    writer.writerows(new_rows)

# Stats
import numpy as np
heat_diffs = [float(r['heat_differential']) for r in new_rows]
opp_heats = [float(r['opp_heat_14']) for r in new_rows]
print(f"\n[+] Saved model_data_v4.csv ({len(new_rows)} records)")
print(f"    opp_heat_14: mean={np.mean(opp_heats):.3f}, std={np.std(opp_heats):.3f}")
print(f"    heat_diff: mean={np.mean(heat_diffs):.3f}, std={np.std(heat_diffs):.3f}")
print(f"\n    🔥 LEAK-FREE: heat checks only use games BEFORE each prediction")
