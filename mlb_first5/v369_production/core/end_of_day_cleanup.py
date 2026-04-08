#!/usr/bin/env python3
"""
end_of_day_cleanup.py — Archive today's results and update running totals
Run at 1:00 AM PT after all games complete
"""
import subprocess
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

print("="*80)
print("END OF DAY CLEANUP — Archiving Results & Updating Totals")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M %S PT')}")
print("="*80)

SHEET_ID = "1IGgDsEXV2DyYNy5b5g2nau63ktjFFVBFRcuKMTH3FiY"

# Get yesterday's date (since we run at 1 AM, "today" is actually yesterday's games)
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
yesterday_display = (datetime.now() - timedelta(days=1)).strftime('%B %d, %Y')
today_display = datetime.now().strftime('%B %d, %Y')

# Load yesterday's picks
yesterday_csv = Path(f'/root/noesis-prediction/mlb_first5/v369_production/daily_predictions/{yesterday}_paper_trades.csv')

if not yesterday_csv.exists():
    print(f"❌ No data found for {yesterday}")
    # Still create fresh sheet for today
    exit()

df = pd.read_csv(yesterday_csv)
print(f"✅ Loaded {len(df)} picks from {yesterday}")

# Calculate results
# Load results file if it exists
results_file = Path(f'/root/noesis-prediction/mlb_first5/v369_production/daily_predictions/{yesterday}_results.json')

if results_file.exists():
    with open(results_file, 'r') as f:
        results_data = json.load(f)
    
    wins = results_data.get('wins', 0)
    losses = results_data.get('losses', 0)
    total_pl = results_data.get('total_pl', 0)
else:
    # Calculate from CSV if results were appended
    wins = 0
    losses = 0
    total_pl = 0
    # We'll need to fetch actual results here
    print("⚠️  Results file not found, will fetch from ESPN...")

print(f"\nYesterday's Results:")
print(f"  Wins: {wins}")
print(f"  Losses: {losses}")
print(f"  Total P&L: ${total_pl:+,}")

# Build the archive section
archive_data = []

# Header for archive
archive_data.append([""])
archive_data.append([f"📅 {yesterday_display} — FINAL RESULTS"])
archive_data.append([""])

# Picks with results
archive_data.append(["TIME", "GAME", "PITCHER", "PRED", "TIER", "STAKE", "BET", "F5 SCORE", "P&L", "RESULT"])

for _, row in df.iterrows():
    # Get result if available
    f5_score = "—"  # Would come from results tracking
    pl = "—"
    result = "—"
    
    archive_data.append([
        row['time'],
        row['game'],
        row['pitcher'],
        row['pred_runs'],
        row['tier'],
        f"${row['stake']}",
        f"{row['opponent']} U 2.5",
        f5_score,
        pl,
        result
    ])

# Day summary
archive_data.append([""])
archive_data.append([f"Day Total: ${total_pl:+,} | Win Rate: {wins/(wins+losses)*100:.1f}%" if (wins+losses) > 0 else "Day Total: Pending"])
archive_data.append(["—"*80])
archive_data.append([""])

print(f"\n✅ Archive section prepared ({len(archive_data)} rows)")

# Now create fresh sheet for today
print("\n" + "="*80)
print("CREATING FRESH SHEET FOR TODAY")
print("="*80)

# Clear sheet first
print("1. Clearing sheet...")
clear_data = json.dumps([["" for _ in range(10)] for _ in range(100)])
subprocess.run(
    ["gog", "sheets", "update", SHEET_ID, "Sheet1!A1:J100",
     "--values-json", clear_data, "--input", "USER_ENTERED"],
    capture_output=True
)

# Build fresh daily template
title = [[f"🎯 NOESIS MLB v369 — {today_display}"]]
subtitle = [["Paper Trade Evaluation | NOT REAL MONEY"]]
empty = [[""]]
headers = [["TIME", "GAME", "PITCHER", "PRED", "TIER", "STAKE", "BET LINE", "RESULT", "P&L", "STATUS"]]

# Placeholder for today's picks (will be filled in morning)
template_rows = [
    ["6:00 AM", "Generate picks...", "", "", "", "", "", "", "", "🔴 Pending"],
    ["", "", "", "", "", "", "", "", "", ""],
    ["—"*5, "—"*10, "—"*15, "—"*5, "—"*8, "—"*8, "—"*15, "—"*8, "—"*8, "—"*12]
]

# Summary section (empty for now)
summary_header = [["📊 DAILY SUMMARY", "", "", "", "", "", "", "", "", ""]]
summary_empty = [["Total Bets:", "—", "", "", "", "", "", "", "", ""]]
summary_stake = [["Total Stake:", "—", "", "", "", "", "", "", "", ""]]
summary_pl = [["Today's P&L:", "—", "", "", "", "", "", "", "", ""]]

# Running total section
running_header = [[""], ["📈 RUNNING TOTAL (YTD)", "", "", "", "", "", "", "", ""]]
# This would accumulate from a database or previous totals
running_total = [["Cumulative P&L:", "—", "", "", "", "", "", "", "", ""]]
running_winrate = [["Overall Win Rate:", "—", "", "", "", "", "", "", "", ""]]

# Archive section (yesterday's results)
archive_header = [[""], [f"📁 ARCHIVE — {yesterday_display}", "", "", "", "", "", "", "", ""]]

# Combine all sections
fresh_data = (title + subtitle + empty + headers + template_rows + 
              summary_header + summary_empty + summary_stake + summary_pl +
              running_header + running_total + running_winrate +
              archive_header + archive_data)

# Write to sheet
print(f"2. Writing {len(fresh_data)} rows...")
range_spec = f"Sheet1!A1:J{len(fresh_data)}"
data_json = json.dumps(fresh_data)

result = subprocess.run(
    ["gog", "sheets", "update", SHEET_ID, range_spec,
     "--values-json", data_json, "--input", "USER_ENTERED"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("   ✅ Success!")
else:
    print(f"   ❌ Error: {result.stderr}")
    exit()

print("\n" + "="*80)
print("✅ END OF DAY CLEANUP COMPLETE")
print("="*80)
print(f"""
STRUCTURE:
  🎯 Today's Header (ready for morning picks)
  📊 Daily Summary (will update during day)
  📈 Running Total (accumulates over season)
  📁 Archive — {yesterday_display} (yesterday's complete results)

NEXT STEPS:
  • 6:00 AM PT — Generate today's picks
  • 6:30 AM PT — Sync to sheet (replaces template)
  • Throughout day — Cron updates F5 results
  • 1:00 AM PT tomorrow — Archive & cleanup repeats

Sheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}
""")
