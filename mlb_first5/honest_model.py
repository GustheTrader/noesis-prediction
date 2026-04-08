#!/usr/bin/env python3
"""
honest_model.py — Build truly leak-free model
ONLY use features that are known BEFORE game time:
- Pitcher's prior season stats (career/season averages from BEFORE this game)
- No opponent stats that include current game
- No heat checks computed with current game
- Handedness (known before game)
- Days rest (schedule info)
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

print('='*70)
print('HONEST MODEL — Strictly Leak-Free Features Only')
print('='*70)

df = pd.read_csv('data/processed/model_data_v4.csv')
print(f"\n📊 Loaded {len(df)} records")

# LEAK-FREE FEATURES ONLY:
# These are all known BEFORE the game starts
leak_free_features = [
    'pitcher_era',      # Prior season/career ERA (not including this game)
    'pitcher_whip',     # Prior WHIP
    'pitcher_k9',       # Prior K/9
    'pitcher_bb9',      # Prior BB/9
    'pitcher_ip',       # Innings pitched (career/season prior)
    'pitcher_k_pct',    # Strikeout %
    'pitcher_hr_pct',   # HR %
    'is_lhp',           # Handedness (known)
    'pitcher_days_rest' # Days since last start (schedule)
]

# Check which features exist
available_features = [f for f in leak_free_features if f in df.columns]
print(f"\n✅ Using {len(available_features)} leak-free features:")
for f in available_features:
    print(f"  - {f}")

# Train/test
train_df = df[df['year'].isin([2021, 2022, 2023])]
test_df = df[df['year'] == 2025]

X_train = train_df[available_features].fillna(0)
y_train = train_df['first_5_runs_allowed']
X_test = test_df[available_features].fillna(0)
y_test = test_df['first_5_runs_allowed']

print(f"\n🤖 Training HONEST model...")
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)
preds = model.predict(X_test)

mae = mean_absolute_error(y_test, preds)
print(f"\n📈 HONEST Model Results:")
print(f"  MAE: {mae:.3f}")

# Betting simulation
test_df = test_df.copy()
test_df['pred'] = preds

print(f"\n💰 Realistic Betting Performance:")

for threshold in [1.0, 1.5, 2.0, 2.5]:
    high_conf = test_df[test_df['pred'] < threshold]
    if len(high_conf) == 0:
        continue
    
    wins = (high_conf['first_5_runs_allowed'] < 2.5).sum()
    losses = len(high_conf) - wins
    win_rate = wins / len(high_conf) * 100
    
    pnl = wins * 227 - losses * 250
    roi = pnl / (len(high_conf) * 250) * 100
    
    print(f"  Pred < {threshold}: {len(high_conf):4d} bets, {win_rate:5.1f}% win, ${pnl:10,} P&L, {roi:+.1f}% ROI")

# Naive baseline
naive_mae = mean_absolute_error(y_test, [2.0] * len(y_test))
print(f"\n📊 Baseline (always predict 2.0): MAE = {naive_mae:.3f}")

# Feature importance
importance = pd.DataFrame({
    'feature': available_features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n🔍 Feature Importance (HONEST model):")
for _, row in importance.iterrows():
    print(f"  {row['feature']:20s}: {row['importance']:.3f}")

print("\n" + "="*70)
print("⚠️  This is the REAL expected performance without data leakage")
print("="*70)
