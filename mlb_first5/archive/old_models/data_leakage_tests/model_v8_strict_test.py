#!/usr/bin/env python3
"""
model_v8_strict_test.py — Test with strictly leak-free heat check
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
import json

print('='*70)
print('STRICT MODEL — Leak-Free Heat Check Only')
print('='*70)

# Load strict data
df = pd.read_csv('data/processed/model_data_v8_strict.csv')
print(f"\n📊 Loaded {len(df)} records")

# Use STRICT heat features only
feature_cols = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'opp_avg_runs_allowed', 'opp_avg_first5_allowed',
    'is_lhp', 'opp_batting_first5', 'platoon_score',
    'heat_14_strict'  # Using STRICT leak-free heat
]

# Train/test split
train_df = df[df['year'].isin([2021, 2022, 2023])]
test_df = df[df['year'] == 2025]

X_train = train_df[feature_cols].fillna(0)
y_train = train_df['first_5_runs_allowed']
X_test = test_df[feature_cols].fillna(0)
y_test = test_df['first_5_runs_allowed']

print(f"\n🤖 Training with STRICT leak-free features...")
print(f"  Train: {len(X_train)} samples")
print(f"  Test:  {len(X_test)} samples")

model = GradientBoostingRegressor(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    random_state=42
)
model.fit(X_train, y_train)
preds = model.predict(X_test)

mae = mean_absolute_error(y_test, preds)
print(f"\n📈 Results with STRICT heat check:")
print(f"  MAE: {mae:.3f}")

# Betting simulation
test_df = test_df.copy()
test_df['pred'] = preds

print(f"\n💰 Betting Simulation (UNDER 2.5 when pred < 1.0):")

for threshold in [0.5, 1.0, 1.5, 2.0]:
    high_conf = test_df[test_df['pred'] < threshold]
    if len(high_conf) == 0:
        continue
    
    wins = (high_conf['first_5_runs_allowed'] < 2.5).sum()
    losses = len(high_conf) - wins
    win_rate = wins / len(high_conf) * 100
    
    pnl = wins * 227 - losses * 250
    
    print(f"  Threshold < {threshold}: {len(high_conf)} bets, {win_rate:.1f}% win, ${pnl:+,} P&L")

# Feature importance
importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n🔍 Feature Importance:")
for _, row in importance.head(10).iterrows():
    print(f"  {row['feature']:25s}: {row['importance']:.3f}")

print("\n" + "="*70)
print("✨ Realistic expectations with leak-free model")
print("="*70)
