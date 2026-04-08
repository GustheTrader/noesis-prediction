#!/usr/bin/env python3
"""
setup_predictions_sheet.py — Create dedicated sheet for daily predictions
"""
import subprocess
import json

print('='*70)
print('SETTING UP NOESIS MLB v369 PREDICTIONS SHEET')
print('='*70)

# Get sheet ID
with open('/root/mlb-first5/SHEET_ID.txt', 'r') as f:
    sheet_id = f.read().strip()

print(f"\n📊 Sheet ID: {sheet_id}")

# Create header row for predictions sheet
headers = [
    'Date', 'Time', 'Game', 'Side', 'Pitcher', 'Hand', 
    'ERA', 'Predicted', 'Tier', 'Action', 'Stake', 'Status', 'Result', 'P&L'
]

# Create sample structure
sample_data = [
    headers,
    ['2026-04-08', '16:35', 'SD @ PIT', 'HOME', 'Paul Skenes', 'RHP', '1.97', '0.64', 'TIER 1', 'BET', '$375', 'PENDING', '', ''],
    ['2026-04-08', '18:35', 'SEA @ TEX', 'HOME', 'Nathan Eovaldi', 'RHP', '1.73', '0.55', 'TIER 1', 'BET', '$375', 'PENDING', '', ''],
]

values_json = json.dumps(sample_data)

print("\n📋 Creating 'Daily_Predictions' tab...")

# First, try to add a new sheet via API
# For now, we'll use a different range that's empty
result = subprocess.run(
    [
        "gog", "sheets", "update", sheet_id,
        "Sheet2!A1:N20",  # Use Sheet2 (should be empty)
        "--values-json", values_json,
        "--input", "USER_ENTERED"
    ],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Created Sheet2 with predictions template!")
    print(f"   View: https://docs.google.com/spreadsheets/d/{sheet_id}")
    print("\n📌 Switch to 'Sheet2' tab to see predictions")
else:
    print(f"⚠️  Sheet2 might not exist. Using Sheet1 row 100+")
    
    # Try using rows 100+ on Sheet1
    result2 = subprocess.run(
        [
            "gog", "sheets", "update", sheet_id,
            "Sheet1!A100:N120",
            "--values-json", values_json,
            "--input", "USER_ENTERED"
        ],
        capture_output=True,
        text=True
    )
    
    if result2.returncode == 0:
        print("✅ Saved to Sheet1 starting at row 100")
        print(f"   View: https://docs.google.com/spreadsheets/d/{sheet_id}")
    else:
        print(f"❌ Error: {result2.stderr}")

print("\n" + "="*70)
print("✨ Predictions sheet setup complete!")
print("="*70)
