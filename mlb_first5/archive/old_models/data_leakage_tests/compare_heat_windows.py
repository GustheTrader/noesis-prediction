#!/usr/bin/env python3
"""
compare_heat_windows.py — Compare 7, 14, and 21 game heat check windows
Test all on 2025 season and report betting performance
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
import json

print('='*70)
print('HEAT CHECK COMPARISON — 7 vs 14 vs 21 Game Windows')
print('='*70)

# Load data with all heat features
df = pd.read_csv('data/processed/model_data_v7.csv')
print(f"\n📊 Loaded {len(df)} records")

# Define feature sets for each window
feature_sets = {
    '7-game': [
        'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
        'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
        'opp_avg_runs_allowed', 'opp_avg_first5_allowed',
        'is_lhp', 'opp_batting_first5', 'platoon_score',
        'opp_heat_7', 'heat_7_differential'
    ],
    '14-game': [
        'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
        'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
        'opp_avg_runs_allowed', 'opp_avg_first5_allowed',
        'is_lhp', 'opp_batting_first5', 'platoon_score',
        'opp_heat_14', 'heat_differential'
    ]
}

# Train/test split
train_df = df[df['year'].isin([2021, 2022, 2023])]
test_df = df[df['year'] == 2025]

y_train = train_df['first_5_runs_allowed']
y_test = test_df['first_5_runs_allowed']

print(f"\n🤖 Training models...")
print(f"  Train: {len(y_train)} samples (2021-2023)")
print(f"  Test:  {len(y_test)} samples (2025)")

results = {}

for name, features in feature_sets.items():
    print(f"\n{'='*70}")
    print(f"Testing {name} heat window...")
    print(f"{'='*70}")
    
    X_train = train_df[features].fillna(0)
    X_test = test_df[features].fillna(0)
    
    model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        random_state=42
    )
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    
    # Betting simulation
    test_df_copy = test_df.copy()
    test_df_copy['predicted'] = preds
    
    high_conf = test_df_copy[test_df_copy['predicted'] < 1.0]
    
    if len(high_conf) > 0:
        wins = (high_conf['first_5_runs_allowed'] < 2.5).sum()
        losses = len(high_conf) - wins
        win_rate = wins / len(high_conf) * 100
        pnl = wins * 227 - losses * 250
        roi = pnl / (len(high_conf) * 250) * 100
    else:
        wins = losses = win_rate = pnl = roi = 0
    
    # Get heat importance
    heat_feature = f"opp_heat_{name.split('-')[0]}"
    heat_imp = model.feature_importances_[features.index(heat_feature)]
    
    results[name] = {
        'mae': mae,
        'heat_importance': heat_imp,
        'bets': len(high_conf),
        'wins': int(wins),
        'losses': int(losses),
        'win_rate': win_rate,
        'pnl': int(pnl),
        'roi': roi,
        'avg_per_bet': pnl / len(high_conf) if len(high_conf) > 0 else 0
    }
    
    print(f"  MAE: {mae:.3f}")
    print(f"  Heat importance: {heat_imp:.3f}")
    print(f"  High conf bets (<1.0): {len(high_conf)}")
    print(f"  Win rate: {win_rate:.1f}%")
    print(f"  P&L: ${pnl:+,}")
    print(f"  ROI: {roi:+.1f}%")

# Final comparison
print("\n" + "="*70)
print("FINAL COMPARISON — All Heat Windows")
print("="*70)

print(f"\n{'Window':<12} {'MAE':<8} {'Bets':<8} {'Win%':<8} {'P&L':<15} {'ROI':<8} {'Heat Imp'}")
print("-"*70)

for name, r in results.items():
    print(f"{name:<12} {r['mae']:<8.3f} {r['bets']:<8} {r['win_rate']:<8.1f} ${r['pnl']:<14,} {r['roi']:<8.1f} {r['heat_importance']:.3f}")

# Find best by different metrics
best_mae = min(results.items(), key=lambda x: x[1]['mae'])
best_pnl = max(results.items(), key=lambda x: x[1]['pnl'])
best_roi = max(results.items(), key=lambda x: x[1]['roi'])

print(f"\n🏆 Best MAE: {best_mae[0]} ({best_mae[1]['mae']:.3f})")
print(f"🏆 Best P&L: {best_pnl[0]} (${best_pnl[1]['pnl']:,})")
print(f"🏆 Best ROI: {best_roi[0]} ({best_roi[1]['roi']:.1f}%)")

# Save results
with open('heat_window_comparison.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved to: heat_window_comparison.json")
print("\n" + "="*70)
print("✨ Comparison complete!")
