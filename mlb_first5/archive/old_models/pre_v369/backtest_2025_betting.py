#!/usr/bin/env python3
"""
backtest_2025_betting.py — Run betting simulation on 2025 season with 21-game heat check
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
import json

print('='*70)
print('2025 SEASON BACKTEST — With 21-Game Heat Check')
print('='*70)

# Load v6 data (includes 21-game heat)
df = pd.read_csv('data/processed/model_data_v6.csv')
print(f"\n📊 Loaded {len(df)} records")

# Features with 21-game heat
feature_cols = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'opp_avg_runs_allowed', 'opp_avg_first5_allowed',
    'is_lhp', 'opp_batting_first5', 'platoon_score',
    'opp_heat_21', 'heat_21_differential'  # Using 21-game heat
]

# Train/test split
train_df = df[df['year'].isin([2021, 2022, 2023])]
test_df = df[df['year'] == 2025]

X_train = train_df[feature_cols].fillna(0)
y_train = train_df['first_5_runs_allowed']
X_test = test_df[feature_cols].fillna(0)
y_test = test_df['first_5_runs_allowed']

print(f"\n🤖 Training model with 21-game heat...")
print(f"  Train: {len(X_train)} samples (2021-2023)")
print(f"  Test:  {len(X_test)} samples (2025)")

model = GradientBoostingRegressor(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    random_state=42
)
model.fit(X_train, y_train)

# Predictions on 2025
preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)

print(f"\n📈 Model Performance:")
print(f"  MAE: {mae:.3f}")
print(f"  14-game heat MAE: 0.368 (for comparison)")

# Add predictions to test data
test_df = test_df.copy()
test_df['predicted_runs'] = preds

# Betting simulation: UNDER 2.5 when predicted < 1.0
print(f"\n💰 Betting Simulation (UNDER 2.5 when predicted < 1.0)")
print(f"  Stake: $250 per bet")
print(f"  Odds: -110 (win $227, lose $250)")
print(f"\n{'='*70}")

# High confidence bets
high_conf = test_df[test_df['predicted_runs'] < 1.0]
print(f"\nHigh Confidence Bets (predicted < 1.0): {len(high_conf)}")

if len(high_conf) > 0:
    wins = (high_conf['first_5_runs_allowed'] < 2.5).sum()
    losses = len(high_conf) - wins
    win_rate = wins / len(high_conf) * 100
    
    pnl = wins * 227 - losses * 250
    roi = pnl / (len(high_conf) * 250) * 100
    
    print(f"  Wins: {wins}")
    print(f"  Losses: {losses}")
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Total P&L: ${pnl:+,}")
    print(f"  ROI: {roi:+.1f}%")
    print(f"  Avg per bet: ${pnl/len(high_conf):+.2f}")

# All bets (predicted < 2.0 for comparison)
all_bets = test_df[test_df['predicted_runs'] < 2.0]
print(f"\nAll Low Predictions (< 2.0): {len(all_bets)}")

if len(all_bets) > 0:
    wins_all = (all_bets['first_5_runs_allowed'] < 2.5).sum()
    losses_all = len(all_bets) - wins_all
    win_rate_all = wins_all / len(all_bets) * 100
    
    pnl_all = wins_all * 227 - losses_all * 250
    roi_all = pnl_all / (len(all_bets) * 250) * 100
    
    print(f"  Wins: {wins_all}")
    print(f"  Losses: {losses_all}")
    print(f"  Win Rate: {win_rate_all:.1f}%")
    print(f"  Total P&L: ${pnl_all:+,}")
    print(f"  ROI: {roi_all:+.1f}%")

# Compare with 14-game heat model
feature_cols_14 = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'opp_avg_runs_allowed', 'opp_avg_first5_allowed',
    'is_lhp', 'opp_batting_first5', 'platoon_score',
    'opp_heat_14', 'heat_differential'
]

X_train_14 = train_df[feature_cols_14].fillna(0)
X_test_14 = test_df[feature_cols_14].fillna(0)

model_14 = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
model_14.fit(X_train_14, y_train)
preds_14 = model_14.predict(X_test_14)

test_df['predicted_runs_14'] = preds_14
high_conf_14 = test_df[test_df['predicted_runs_14'] < 1.0]

print(f"\n{'='*70}")
print("COMPARISON: 14-game vs 21-game Heat Check")
print(f"{'='*70}")

print(f"\n14-Game Heat Model:")
print(f"  High conf bets (< 1.0): {len(high_conf_14)}")
if len(high_conf_14) > 0:
    wins_14 = (high_conf_14['first_5_runs_allowed'] < 2.5).sum()
    losses_14 = len(high_conf_14) - wins_14
    pnl_14 = wins_14 * 227 - losses_14 * 250
    print(f"  Win Rate: {wins_14/len(high_conf_14)*100:.1f}%")
    print(f"  P&L: ${pnl_14:+,}")

print(f"\n21-Game Heat Model:")
print(f"  High conf bets (< 1.0): {len(high_conf)}")
if len(high_conf) > 0:
    print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  P&L: ${pnl:+,}")

# Save results
results = {
    'model': '21_game_heat',
    'mae': mae,
    'total_bets': len(high_conf),
    'wins': int(wins) if len(high_conf) > 0 else 0,
    'losses': int(losses) if len(high_conf) > 0 else 0,
    'win_rate': win_rate if len(high_conf) > 0 else 0,
    'pnl': int(pnl) if len(high_conf) > 0 else 0,
    'comparison_14game': {
        'mae': 0.368,
        'total_bets': len(high_conf_14),
        'wins': int(wins_14) if len(high_conf_14) > 0 else 0,
        'losses': int(losses_14) if len(high_conf_14) > 0 else 0,
    }
}

with open('backtest_2025_21game_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved to: backtest_2025_21game_results.json")
print("\n" + "="*70)
print("✨ 2025 Backtest Complete!")
