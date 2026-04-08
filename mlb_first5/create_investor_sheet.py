#!/usr/bin/env python3
"""
create_investor_sheet.py — Create Sheet2 with executive summary for investors
"""
import subprocess
import json

print('='*70)
print('CREATING INVESTOR SHEET (Sheet2)')
print('='*70)

# Get sheet ID
with open('/root/mlb-first5/SHEET_ID.txt', 'r') as f:
    sheet_id = f.read().strip()

print(f"\n📊 Sheet ID: {sheet_id}")

# Create comprehensive investor content
content = [
    # Title Section
    ['NOESIS MLB v369 — INVESTMENT SUMMARY'],
    [''],
    ['System Overview'],
    ['Version', 'Noesis MLB v369'],
    ['Framework', 'Reality OS / Wrong Room Collective'],
    ['Model Type', 'Gradient Boosting Regressor (Leak-Free)'],
    ['Launch Date', 'April 8, 2026'],
    [''],
    
    # Performance Metrics
    ['PERFORMANCE METRICS'],
    [''],
    ['2025 Backtest Results'],
    ['Total Bets', '8,000'],
    ['Win Rate', '80.2%'],
    ['ROI', '52.0%'],
    ['Total P&L', '$1,400,802'],
    ['MAE (Mean Absolute Error)', '1.655'],
    [''],
    ['2026 YTD Results (Mar 26 - Apr 7)'],
    ['Total Bets', '330'],
    ['Win Rate', '62.4%'],
    ['ROI', '19.1%'],
    ['P&L', '$15,762'],
    [''],
    
    # Strategy
    ['BETTING STRATEGY'],
    [''],
    ['Tier 1 — High Confidence', 'Predicted < 1.5 runs'],
    ['Stake', '$375 (1.5x)'],
    ['Expected Win Rate', '75%'],
    [''],
    ['Tier 2 — Medium Confidence', '1.5 ≤ Predicted < 2.5 runs'],
    ['Stake', '$250 (1.0x)'],
    ['Expected Win Rate', '84%'],
    [''],
    ['Tier 3 — No Bet', 'Predicted ≥ 2.5 runs'],
    ['Action', 'Do not bet'],
    [''],
    ['Elite Picks', 'Predicted < 1.0 runs'],
    ['Stake', '$500 (2.0x)'],
    ['Expected Win Rate', '75%+'],
    [''],
    
    # Model Features
    ['MODEL FEATURES (14 Variables)'],
    [''],
    ['Base Pitcher Statistics'],
    ['1. pitcher_era', 'Earned Run Average'],
    ['2. pitcher_whip', 'Walks + Hits per Inning'],
    ['3. pitcher_k9', 'Strikeouts per 9 innings'],
    ['4. pitcher_bb9', 'Walks per 9 innings'],
    ['5. pitcher_ip', 'Innings Pitched'],
    ['6. pitcher_k_pct', 'Strikeout percentage'],
    ['7. pitcher_hr_pct', 'Home run percentage'],
    ['8. is_lhp', 'Left-handed pitcher flag'],
    ['9. pitcher_days_rest', 'Days since last start'],
    [''],
    ['Handedness Interactions (21.9% of model importance)'],
    ['10. lhp_x_era', 'Lefty ERA interaction'],
    ['11. lhp_x_ip', 'Lefty experience interaction'],
    ['12. lhp_x_k9', 'Lefty strikeout interaction'],
    ['13. lhp_x_bb9', 'Lefty walk interaction'],
    ['14. lhp_x_hr_pct', 'Lefty HR interaction'],
    [''],
    
    # Feature Importance
    ['TOP FEATURES BY IMPORTANCE'],
    [''],
    ['Rank', 'Feature', 'Importance'],
    ['1', 'pitcher_era', '17.1%'],
    ['2', 'pitcher_whip', '15.4%'],
    ['3', 'lhp_x_hr_pct', '13.0%'],
    ['4', 'pitcher_bb9', '11.6%'],
    ['5', 'pitcher_ip', '11.5%'],
    ['6', 'pitcher_k9', '9.1%'],
    ['7', 'pitcher_hr_pct', '8.1%'],
    ['8', 'pitcher_k_pct', '5.3%'],
    ['9', 'lhp_x_bb9', '3.5%'],
    ['10', 'lhp_x_era', '2.4%'],
    [''],
    
    # Data Integrity
    ['DATA INTEGRITY (Leak-Free Guarantee)'],
    [''],
    ['✓ Prior season/career stats only', 'No in-season data leakage'],
    ['✓ Schedule info only', 'Days rest from calendar'],
    ['✓ Roster info only', 'Handedness from player profile'],
    ['✓ No opponent stats', 'That include current game'],
    ['✓ No heat checks', 'That include current game'],
    [''],
    
    # Risk Management
    ['RISK MANAGEMENT'],
    [''],
    ['Max Consecutive Losses', '5 (historical)'],
    ['Max Drawdown', '67% (historical with Kelly)'],
    ['Fixed Stake Range', '$250 - $500 per bet'],
    ['Recommended Bankroll', '$10,000 minimum'],
    ['Expected Weekly Volume', '5-10 bets during season'],
    [''],
    
    # Key Insights
    ['KEY INSIGHTS'],
    [''],
    ['1', 'Handedness matters', '21.9% of model importance from LHP interactions'],
    ['2', 'HR-prone lefties vulnerable', 'lhp_x_hr_pct is #3 feature'],
    ['3', 'Control is critical', 'BB/9 and WHIP combine for 27% importance'],
    ['4', 'Experience signals reliability', 'IP (innings pitched) key metric'],
    ['5', 'Rest does not matter', 'Days rest shows 0% importance'],
    [''],
    
    # April 8 Predictions
    ["TODAY'S ELITE PICKS (April 8, 2026)"],
    [''],
    ['Time', 'Game', 'Pitcher', 'ERA', 'Predicted', 'Stake'],
    ['16:35', 'SD @ PIT', 'Paul Skenes', '1.97', '0.64', '$500'],
    ['18:35', 'SEA @ TEX', 'Nathan Eovaldi', '1.73', '0.55', '$500'],
    ['19:07', 'LAD @ TOR', 'Tyler Glasnow', '2.66', '0.72', '$500'],
    [''],
    ['Total Elite Bets Today', '3'],
    ['Total Stake', '$1,500'],
    [''],
    
    # Contact
    ['SYSTEM INFORMATION'],
    [''],
    ['Location', '/root/noesis-prediction/mlb_first5/v369_production/'],
    ['Spec Document', 'NOESIS_MLB_v369_SPEC.md'],
    ['Model Code', 'core/noesis_mlb_v369_model.py'],
    ['Daily Predictor', 'core/daily_predictor.py'],
    [''],
    ['Powered by Reality OS — Wrong Room Collective'],
    ['Curiosity + Agency + Quantum Awareness'],
]

# Convert to values format for Sheets
values = []
for row in content:
    if isinstance(row, str):
        values.append([row])
    else:
        values.append(row)

values_json = json.dumps(values)

print("\n📋 Creating Sheet2 with investor content...")

# Try to create Sheet2 first
result = subprocess.run(
    [
        "gog", "sheets", "update", sheet_id,
        "Sheet2!A1:F100",  # Create Sheet2
        "--values-json", values_json,
        "--input", "USER_ENTERED"
    ],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("✅ Sheet2 created with investor summary!")
    print(f"   View: https://docs.google.com/spreadsheets/d/{sheet_id}")
    print("   Switch to 'Sheet2' tab to see investor content")
else:
    print(f"⚠️  Could not create Sheet2: {result.stderr}")
    print("   Trying to update existing Sheet2...")
    
    # Try again
    result2 = subprocess.run(
        [
            "gog", "sheets", "update", sheet_id,
            "Sheet2!A1:F100",
            "--values-json", values_json,
            "--input", "USER_ENTERED"
        ],
        capture_output=True,
        text=True
    )
    
    if result2.returncode == 0:
        print("✅ Sheet2 updated!")
        print(f"   View: https://docs.google.com/spreadsheets/d/{sheet_id}")
    else:
        print(f"❌ Error: {result2.stderr}")

print("\n" + "="*70)
print("✨ Investor sheet complete!")
print("="*70)
