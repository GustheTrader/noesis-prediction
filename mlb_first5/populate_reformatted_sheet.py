#!/usr/bin/env python3
"""
populate_reformatted_sheet.py — Populate Google Sheet with new structure
Rows 2-30: Today's picks
Rows 32-62: Yesterday's performance  
Row 64+: Full year results
"""
import subprocess
import json

print('='*70)
print('POPULATING REFORMATTED GOOGLE SHEET')
print('='*70)

# Get sheet ID
with open('/root/mlb-first5/SHEET_ID.txt', 'r') as f:
    sheet_id = f.read().strip()

# SECTION 1: Today's Picks (Rows 2-30)
print("\n📊 Creating Today's Picks (Rows 2-30)...")

today_picks = [
    ['Date', 'Time', 'Game', 'Side', 'Pitcher', 'Hand', 'ERA', 'Pred', 'Tier', 'Stake', 'Status'],
    ['2026-04-08', '16:35', 'SD @ PIT', 'HOME', 'Paul Skenes', 'RHP', 1.97, 0.64, 'ELITE', '$500', 'PENDING'],
    ['2026-04-08', '18:35', 'SEA @ TEX', 'HOME', 'Nathan Eovaldi', 'RHP', 1.73, 0.55, 'ELITE', '$500', 'PENDING'],
    ['2026-04-08', '19:07', 'LAD @ TOR', 'AWAY', 'Tyler Glasnow', 'RHP', 2.66, 0.72, 'ELITE', '$500', 'PENDING'],
    ['2026-04-08', '17:10', 'KC @ CLE', 'HOME', 'Tanner Bibee', 'RHP', 4.25, 0.69, 'TIER 1', '$375', 'PENDING'],
    ['2026-04-08', '18:35', 'SEA @ TEX', 'AWAY', 'Luis Castillo', 'RHP', 3.55, 1.12, 'TIER 1', '$375', 'PENDING'],
    ['2026-04-08', '19:10', 'HOU @ COL', 'HOME', 'Kyle Freeland', 'LHP', 4.99, 1.39, 'TIER 1', '$375', 'PENDING'],
    ['2026-04-08', '19:45', 'PHI @ SF', 'AWAY', 'Zack Wheeler', 'RHP', 2.71, 0.76, 'TIER 1', '$375', 'PENDING'],
    ['2026-04-08', '20:07', 'ATL @ LAA', 'HOME', 'Tyler Anderson', 'LHP', 5.43, 1.27, 'TIER 1', '$375', 'PENDING'],
    ['2026-04-08', '22:40', 'CHC @ TB', 'HOME', 'Zack Littell', 'RHP', 3.82, 1.08, 'TIER 1', '$375', 'PENDING'],
    ['2026-04-08', '23:05', 'ATH @ NYY', 'AWAY', 'Luis Severino', 'RHP', 4.55, 1.33, 'TIER 1', '$375', 'PENDING'],
    ['2026-04-08', '17:35', 'MIL @ BOS', 'AWAY', 'Freddy Peralta', 'RHP', 2.71, 1.59, 'TIER 2', '$250', 'PENDING'],
    ['2026-04-08', '17:35', 'MIL @ BOS', 'HOME', 'Tanner Houck', 'RHP', 8.12, 1.80, 'TIER 2', '$250', 'PENDING'],
    ['2026-04-08', '19:07', 'LAD @ TOR', 'HOME', 'Kevin Gausman', 'RHP', 3.59, 1.56, 'TIER 2', '$250', 'PENDING'],
    ['2026-04-08', '19:10', 'HOU @ COL', 'AWAY', 'Framber Valdez', 'LHP', 3.66, 2.41, 'TIER 2', '$250', 'PENDING'],
    ['2026-04-08', '20:05', 'STL @ WSH', 'HOME', 'MacKenzie Gore', 'LHP', 4.18, 2.28, 'TIER 2', '$250', 'PENDING'],
    ['2026-04-08', '20:10', 'ARI @ NYM', 'HOME', 'Jose Quintana', 'RHP', 4.00, 1.90, 'TIER 2', '$250', 'PENDING'],
    ['2026-04-08', '23:05', 'ATH @ NYY', 'HOME', 'Carlos Rodon', 'LHP', 3.09, 1.76, 'TIER 2', '$250', 'PENDING'],
    ['2026-04-08', '23:40', 'DET @ MIN', 'HOME', 'Pablo Lopez', 'RHP', 2.75, 2.42, 'TIER 2', '$250', 'PENDING'],
    ['', '', '', '', '', '', '', '', '', '', ''],
    ['TODAY SUMMARY', '', '', '', '', '', '', '', '', '', ''],
    ['Total Bets', '18', '', '', '', '', '', '', '', '', ''],
    ['Elite Picks', '3 @ $500 = $1,500', '', '', '', '', '', '', '', '', ''],
    ['Tier 1', '7 @ $375 = $2,625', '', '', '', '', '', '', '', '', ''],
    ['Tier 2', '8 @ $250 = $2,000', '', '', '', '', '', '', '', '', ''],
    ['Total Stake', '$6,125', '', '', '', '', '', '', '', '', ''],
    ['Expected Win Rate', '75%', '', '', '', '', '', '', '', '', ''],
    ['Potential Profit', '+$4,500', '', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', '', '', ''],
]

values_json = json.dumps(today_picks)

result = subprocess.run(
    [
        "gog", "sheets", "update", sheet_id,
        "Sheet1!A2:K30",
        "--values-json", values_json,
        "--input", "USER_ENTERED"
    ],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Today's picks saved (Rows 2-30)")
else:
    print(f"❌ Error: {result.stderr}")

# SECTION 2: Yesterday's Performance (Rows 32-62)
print("\n📊 Creating Yesterday's Performance (Rows 32-62)...")

# Load yesterday's results (April 7)
with open('v369_production/daily_predictions/2026_ytd_results.json', 'r') as f:
    ytd_data = json.load(f)

# Get April 7 results
april_7_results = [r for r in ytd_data['results'] if r['date'] == '2026-04-07' and r['stake'] > 0]

yesterday_rows = [
    ['YESTERDAY PERFORMANCE (April 7, 2026)'],
    ['Date', 'Game', 'Side', 'Team', 'Predicted', 'Actual', 'Tier', 'Stake', 'Result', 'P&L', ''],
]

# Add April 7 games (up to 25 rows)
for r in april_7_results[:25]:
    yesterday_rows.append([
        r['date'], r['game'], r['side'], r['team'],
        r['predicted'], r['actual'], r['tier'],
        f"${r['stake']}", r['result'], f"${r['pnl']:+d}", ''
    ])

# Pad to fill rows 32-62
while len(yesterday_rows) < 31:
    yesterday_rows.append(['', '', '', '', '', '', '', '', '', '', ''])

# Add summary
yesterday_wins = sum(1 for r in april_7_results if r['result'] == 'WIN')
yesterday_pnl = sum(r['pnl'] for r in april_7_results)

yesterday_rows.append(['', '', '', '', '', '', '', '', '', '', ''])
yesterday_rows.append(['APRIL 7 SUMMARY', '', '', '', '', '', '', '', '', '', ''])
yesterday_rows.append(['Total Bets', str(len(april_7_results)), '', '', '', '', '', '', '', '', ''])
yesterday_rows.append(['Wins', str(yesterday_wins), '', '', '', '', '', '', '', '', ''])
yesterday_rows.append(['Losses', str(len(april_7_results) - yesterday_wins), '', '', '', '', '', '', '', '', ''])
yesterday_rows.append(['Win Rate', f"{yesterday_wins/len(april_7_results)*100:.1f}%" if april_7_results else 'N/A', '', '', '', '', '', '', '', '', ''])
yesterday_rows.append(['Total P&L', f"${yesterday_pnl:+,}", '', '', '', '', '', '', '', '', ''])

values_json = json.dumps(yesterday_rows)

result = subprocess.run(
    [
        "gog", "sheets", "update", sheet_id,
        "Sheet1!A32:K62",
        "--values-json", values_json,
        "--input", "USER_ENTERED"
    ],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Yesterday's performance saved (Rows 32-62)")
else:
    print(f"❌ Error: {result.stderr}")

# SECTION 3: Full Year Results (Row 64+)
print("\n📊 Creating Full Year Results (Row 64+)...")

# Load full 2026 YTD
all_bets = [r for r in ytd_data['results'] if r['stake'] > 0]
total_wins = sum(1 for r in all_bets if r['result'] == 'WIN')
total_pnl = sum(r['pnl'] for r in all_bets)
total_staked = sum(r['stake'] for r in all_bets)

year_rows = [
    ['2026 YEAR-TO-DATE RESULTS (March 26 - April 7)'],
    ['Date', 'Game', 'Side', 'Team', 'Predicted', 'Actual', 'Tier', 'Stake', 'Result', 'P&L', ''],
]

# Add all bets (first 100)
for r in all_bets[:100]:
    year_rows.append([
        r['date'], r['game'], r['side'], r['team'],
        r['predicted'], r['actual'], r['tier'],
        f"${r['stake']}", r['result'], f"${r['pnl']:+d}", ''
    ])

# Summary
year_rows.append(['', '', '', '', '', '', '', '', '', '', ''])
year_rows.append(['2026 YTD SUMMARY', '', '', '', '', '', '', '', '', '', ''])
year_rows.append(['Total Games Analyzed', str(len(ytd_data['results']))])
year_rows.append(['Total Bets Placed', str(len(all_bets))])
year_rows.append(['Wins', str(total_wins)])
year_rows.append(['Losses', str(len(all_bets) - total_wins)])
year_rows.append(['Win Rate', f"{total_wins/len(all_bets)*100:.1f}%"])
year_rows.append(['Total Staked', f"${total_staked:,}"])
year_rows.append(['Total P&L', f"${total_pnl:+,}"])
year_rows.append(['ROI', f"{total_pnl/total_staked*100:+.1f}%"])
year_rows.append(['', '', '', '', '', '', '', '', '', '', ''])
year_rows.append(['AVERAGE PER BET', '', '', '', '', '', '', '', '', '', ''])
year_rows.append(['Win Rate', f"{total_wins/len(all_bets)*100:.1f}%"])
year_rows.append(['Avg P&L per Bet', f"${total_pnl/len(all_bets):+.2f}"])
year_rows.append(['Avg Stake', f"${total_staked/len(all_bets):.2f}"])

values_json = json.dumps(year_rows)

result = subprocess.run(
    [
        "gog", "sheets", "update", sheet_id,
        f"Sheet1!A64:K{64 + len(year_rows) - 1}",
        "--values-json", values_json,
        "--input", "USER_ENTERED"
    ],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print(f"✅ Full year results saved (Rows 64-{64 + len(year_rows) - 1})")
else:
    print(f"❌ Error: {result.stderr}")

print("\n" + "="*70)
print("✅ SHEET POPULATION COMPLETE!")
print("="*70)
print("\n📊 Sheet Structure:")
print("   Row 1: Headers")
print("   Rows 2-30: Today's Picks (April 8)")
print("   Row 31: Blank")
print("   Rows 32-62: Yesterday's Performance (April 7)")
print("   Row 63: Blank")
print("   Row 64+: Full 2026 YTD Results")
print(f"\n🔗 View: https://docs.google.com/spreadsheets/d/{sheet_id}")
