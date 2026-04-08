#!/usr/bin/env python3
"""
sync_todays_picks_to_sheets.py — Sync today's paper trade picks to Google Sheets
"""
import json
import subprocess
import pandas as pd
from datetime import datetime
from pathlib import Path

print("="*80)
print("SYNCING TODAY'S PICKS TO GOOGLE SHEETS")
print("="*80)

# Load picks
today = datetime.now().strftime('%Y%m%d')
csv_file = Path(f'/root/noesis-prediction/mlb_first5/v369_production/daily_predictions/{today}_paper_trades.csv')

if not csv_file.exists():
    print(f"❌ CSV file not found: {csv_file}")
    exit()

df = pd.read_csv(csv_file)
print(f"✅ Loaded {len(df)} picks from CSV")

# Sheet ID
sheet_id = "1IGgDsEXV2DyYNy5b5g2nau63ktjFFVBFRcuKMTH3FiY"

# Prepare data for sheets
# Row 2-30: Today's picks
# Format: Time | Game | Pitcher | Pred | Tier | Stake | Bet | Status | Result

header = [["TIME", "GAME", "PITCHER", "PRED RUNS", "TIER", "STAKE", "BET", "STATUS", "F5 RESULT", "P/L"]]

rows = []
for _, row in df.iterrows():
    rows.append([
        row['time'],
        row['game'],
        f"{row['pitcher']} ({row['side']})",
        row['pred_runs'],
        row['tier'],
        f"${row['stake']}",
        row['bet'],
        row['status'],
        "",  # F5 Result (to be filled)
        ""   # P/L (to be calculated)
    ])

# Add summary row
rows.append(["", "", "", "", "", "", "", "", "", ""])
rows.append(["SUMMARY", "", "", "", "", "", "", "", "", ""])
rows.append(["Total Bets", len(df), "", "", "", "", "", "", "", ""])
rows.append(["Total Stake", f"${df['stake'].sum():,}", "", "", "", "", "", "", "", ""])
rows.append(["Expected EV", f"${df['stake'].sum() * 0.191:.0f}", "", "", "", "", "", "", "", ""])

# Combine header + rows
all_data = header + rows

# Convert to JSON for gog
values_json = json.dumps(all_data)

print(f"\nSyncing {len(all_data)} rows to Google Sheets...")
print(f"Sheet ID: {sheet_id}")

# Update Sheet1!A2:J{2+len(all_data)}
end_row = 2 + len(all_data)
range_spec = f"Sheet1!A2:J{end_row}"

result = subprocess.run(
    [
        "gog", "sheets", "update", sheet_id,
        range_spec,
        "--values-json", values_json,
        "--input", "USER_ENTERED"
    ],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print(f"\n✅ Successfully synced to Google Sheets!")
    print(f"   Range: {range_spec}")
    print(f"   Sheet: 'Noesis MLB'")
    print(f"\n   URL: https://docs.google.com/spreadsheets/d/{sheet_id}")
else:
    print(f"\n❌ Error syncing to Sheets:")
    print(f"   {result.stderr}")
    exit()

# Also add a header row explaining this is paper trade data
header_note = [["⚠️ PAPER TRADE EVALUATION — April 8, 2026 — NOT REAL MONEY"]]
note_json = json.dumps(header_note)

result2 = subprocess.run(
    [
        "gog", "sheets", "update", sheet_id,
        "Sheet1!A1:J1",
        "--values-json", note_json,
        "--input", "USER_ENTERED"
    ],
    capture_output=True,
    text=True
)

if result2.returncode == 0:
    print("✅ Added header note")

print("\n" + "="*80)
print("SYNC COMPLETE")
print("="*80)
print(f"\nView your picks at:")
print(f"https://docs.google.com/spreadsheets/d/{sheet_id}")
