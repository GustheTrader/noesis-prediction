#!/usr/bin/env python3
"""
model_v5_test.py — Test model with 2-game heat check feature
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

print('='*70)
print('MLB First-5 Model v5 — With 2-Game Heat Check')
print('='*70)

# Load v5 data
df = pd.read_csv('data/processed/model_data_v5.csv')
print(f"\n📊 Loaded {len(df)} records")

# Features including new 2-game heat check
feature_cols = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'opp_avg_runs_allowed', 'opp_avg_first5_allowed',
    'is_lhp', 'opp_batting_first5', 'platoon_score',
    'opp_heat_14', 'heat_differential',  # Original 14-game
    'opp_heat_2', 'heat_2_differential'   # New 2-game
]

# Train on 2021-2023, test on 2025
train_df = df[df['year'].isin([2021, 2022, 2023])]
test_df = df[df['year'] == 2025]

X_train = train_df[feature_cols].fillna(0)
y_train = train_df['first_5_runs_allowed']
X_test = test_df[feature_cols].fillna(0)
y_test = test_df['first_5_runs_allowed']

print(f"\n🤖 Training model...")
print(f"  Train: {len(X_train)} samples (2021-2023)")
print(f"  Test:  {len(X_test)} samples (2025)")

model = GradientBoostingRegressor(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    random_state=42
)
model.fit(X_train, y_train)

# Predictions
preds = model.predict(X_test)
mae = mean_absolute_error(y_test, preds)

print(f"\n📈 Results:")
print(f"  Test MAE: {mae:.3f}")
print(f"  Naive MAE (predicting 2.0): {mean_absolute_error(y_test, [2.0]*len(y_test)):.3f}")

# Feature importance
importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n🔍 Top Features:")
for _, row in importance.head(10).iterrows():
    print(f"  {row['feature']:25s}: {row['importance']:.3f}")

# Check 2-game heat importance specifically
heat_2_importance = importance[importance['feature'] == 'opp_heat_2']['importance'].values
if len(heat_2_importance) > 0:
    print(f"\n  📊 2-game heat check importance: {heat_2_importance[0]:.3f}")

# Compare with just 14-game heat
feature_cols_14 = [f for f in feature_cols if '2' not in f]
X_train_14 = train_df[feature_cols_14].fillna(0)
X_test_14 = test_df[feature_cols_14].fillna(0)

model_14 = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
model_14.fit(X_train_14, y_train)
preds_14 = model_14.predict(X_test_14)
mae_14 = mean_absolute_error(y_test, preds_14)

print(f"\n📊 Comparison:")
print(f"  With 14-game heat only: {mae_14:.3f} MAE")
print(f"  With 2-game + 14-game:  {mae:.3f} MAE")
print(f"  Improvement:            {mae_14 - mae:+.3f}")

print("\n" + "="*70)
print("✨ Model v5 test complete!")
