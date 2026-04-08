#!/usr/bin/env python3
"""
update_game_results.py — Fetch actual F5 results and update Google Sheets
Run 2.5 hours after game start time
"""
import requests
import json
import subprocess
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

print("="*80)
print("FETCHING GAME RESULTS & UPDATING SHEETS")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M %S PT')}")
print("="*80)

# ESPN API
SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

def get_json(url, params=None):
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

# Sheet ID
SHEET_ID = "1IGgDsEXV2DyYNy5b5g2nau63ktjFFVBFRcuKMTH3FiY"

# Load today's picks
today = datetime.now().strftime('%Y%m%d')
csv_file = Path(f'/root/noesis-prediction/mlb_first5/v369_production/daily_predictions/{today}_paper_trades.csv')

if not csv_file.exists():
    print(f"❌ No picks file found: {csv_file}")
    exit()

df = pd.read_csv(csv_file)
print(f"✅ Loaded {len(df)} picks")

# Fetch all games from ESPN
games_data = get_json(SCOREBOARD_URL, params={"dates": today})
if not games_data or not games_data.get('events'):
    print("❌ No games found on ESPN")
    exit()

# Build results lookup
results = {}
for event in games_data.get('events', []):
    name = event.get('name', '')
    competitions = event.get('competitions', [])
    if not competitions:
        continue
    
    comp = competitions[0]
    status = event.get('status', {}).get('type', {})
    
    # Check if game is final or in progress with F5 data
    period = status.get('period', 0)  # Current inning
    state = status.get('state', 'unknown')
    
    # Only process if game has reached 5th inning or is final
    if state == 'post' or (state == 'in' and period >= 5):
        # Get linescores for F5
        for c in comp.get('competitors', []):
            linescores = c.get('linescores', [])
            
            # Only count runs if inning has been played
            f5_runs = 0
            for i, ls in enumerate(linescores[:5], 1):
                # For completed innings, use the value
                # For current inning in progress, only count if we're past it
                if state == 'post' or i < period or (i == period and status.get('type', {}).get('completed')):
                    f5_runs += int(ls.get('value', 0))
            
            team_abbr = c.get('team', {}).get('abbreviation', '')
            if team_abbr:
                results[team_abbr] = {
                    'f5_runs': f5_runs,
                    'status': status.get('description', 'Unknown'),
                    'is_final': state == 'post',
                    'inning': period
                }

print(f"✅ Found results for {len(results)} teams")

# Update each pick with results
updated_rows = []
pl_total = 0
wins = 0
losses = 0

for idx, row in df.iterrows():
    opponent = row['opponent']
    stake = row['stake']
    
    if opponent in results:
        f5_runs = results[opponent]['f5_runs']
        is_win = f5_runs < 2.5
        
        if is_win:
            # Win at -120 odds: profit = stake * 0.833
            pl = int(stake * 0.833)
            wins += 1
        else:
            # Loss: lose the stake
            pl = -stake
            losses += 1
        
        pl_total += pl
        
        result_str = f"{f5_runs} runs"
        pl_str = f"+${pl}" if pl > 0 else f"-${abs(pl)}"
        status_str = "✅ WIN" if is_win else "❌ LOSS"
    else:
        result_str = "Pending"
        pl_str = ""
        status_str = row['status']
    
    # Row data for sheet (columns I and J)
    # Need to map to correct row (idx + 3 because header is row 2)
    sheet_row = idx + 3
    
    updated_rows.append({
        'row': sheet_row,
        'game': row['game'],
        'opponent': opponent,
        'result': result_str,
        'pl': pl_str,
        'status': status_str
    })

# Update Google Sheets
print(f"\nUpdating {len(updated_rows)} rows in Google Sheets...")

for update in updated_rows:
    if update['result'] != 'Pending':
        # Update F5 Result (Column I)
        result_range = f"Sheet1!I{update['row']}"
        result_json = json.dumps([[update['result']]])
        
        subprocess.run(
            ["gog", "sheets", "update", SHEET_ID, result_range, 
             "--values-json", result_json, "--input", "USER_ENTERED"],
            capture_output=True
        )
        
        # Update P/L (Column J)
        pl_range = f"Sheet1!J{update['row']}"
        pl_json = json.dumps([[update['pl']]])
        
        subprocess.run(
            ["gog", "sheets", "update", SHEET_ID, pl_range,
             "--values-json", pl_json, "--input", "USER_ENTERED"],
            capture_output=True
        )
        
        print(f"  Row {update['row']}: {update['game']} | {update['result']} | {update['pl']}")

# Update summary at bottom
summary_start_row = len(df) + 5
summary_data = [
    ["ACTUAL RESULTS", "", "", "", "", "", "", "", "", ""],
    ["Wins", wins, "", "", "", "", "", "", "", ""],
    ["Losses", losses, "", "", "", "", "", "", "", ""],
    ["Win Rate", f"{wins/(wins+losses)*100:.1f}%" if (wins+losses) > 0 else "N/A", "", "", "", "", "", "", "", ""],
    ["Total P/L", f"${pl_total:+,}", "", "", "", "", "", "", "", ""],
    ["ROI", f"{pl_total/df['stake'].sum()*100:.1f}%" if df['stake'].sum() > 0 else "N/A", "", "", "", "", "", "", "", ""]
]

summary_json = json.dumps(summary_data)
summary_range = f"Sheet1!A{summary_start_row}:J{summary_start_row + 5}"

subprocess.run(
    ["gog", "sheets", "update", SHEET_ID, summary_range,
     "--values-json", summary_json, "--input", "USER_ENTERED"],
    capture_output=True
)

print(f"\n✅ Updated summary:")
print(f"   Wins: {wins}")
print(f"   Losses: {losses}")
print(f"   Win Rate: {wins/(wins+losses)*100:.1f}%" if (wins+losses) > 0 else "N/A")
print(f"   Total P/L: ${pl_total:+,}")
print(f"   ROI: {pl_total/df['stake'].sum()*100:.1f}%")

print(f"\n💾 Sheet updated: https://docs.google.com/spreadsheets/d/{SHEET_ID}")
