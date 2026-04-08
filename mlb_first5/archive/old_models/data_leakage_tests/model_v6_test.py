#!/usr/bin/env python3
"""
model_v6_test.py — Test model with 21-game heat check feature
Compare 14-day vs 21-day rolling windows
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

print('='*70)
print('MLB First-5 Model v6 — With 21-Game Heat Check (3 weeks)')
print('='*70)

# Load v6 data
df = pd.read_csv('data/processed/model_data_v6.csv')
print(f"\n📊 Loaded {len(df)} records")

# Test 1: Original model (14-game heat)
feature_cols_14 = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'opp_avg_runs_allowed', 'opp_avg_first5_allowed',
    'is_lhp', 'opp_batting_first5', 'platoon_score',
    'opp_heat_14', 'heat_differential'
]

# Test 2: 21-game heat instead of 14
feature_cols_21 = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'opp_avg_runs_allowed', 'opp_avg_first5_allowed',
    'is_lhp', 'opp_batting_first5', 'platoon_score',
    'opp_heat_21', 'heat_21_differential'
]

# Test 3: Both heat features
feature_cols_both = feature_cols_14 + ['opp_heat_21', 'heat_21_differential']

# Train/test split
train_df = df[df['year'].isin([2021, 2022, 2023])]
test_df = df[df['year'] == 2025]

y_train = train_df['first_5_runs_allowed']
y_test = test_df['first_5_runs_allowed']

print(f"\n🤖 Training models...")
print(f"  Train: {len(y_train)} samples (2021-2023)")
print(f"  Test:  {len(y_test)} samples (2025)")

results = []

for name, features in [
    ('14-game heat only', feature_cols_14),
    ('21-game heat only', feature_cols_21),
    ('Both 14 + 21 game', feature_cols_both)
]:
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
    
    # Get heat check importance
    if 'opp_heat_21' in features:
        heat_imp = model.feature_importances_[features.index('opp_heat_21')]
    else:
        heat_imp = model.feature_importances_[features.index('opp_heat_14')]
    
    results.append({
        'name': name,
        'mae': mae,
        'heat_importance': heat_imp,
        'features': len(features)
    })
    
    print(f"\n  {name}:")
    print(f"    MAE: {mae:.3f}")
    print(f"    Heat importance: {heat_imp:.3f}")

print("\n" + "="*70)
print("📊 COMPARISON")
print("="*70)
print(f"{'Model':<20} {'MAE':<10} {'Heat Imp':<12} {'vs 14-day'}")
print("-"*70)

baseline_mae = results[0]['mae']
for r in results:
    diff = baseline_mae - r['mae']
    print(f"{r['name']:<20} {r['mae']:<10.3f} {r['heat_importance']:<12.3f} {diff:+.3f}")

best = min(results, key=lambda x: x['mae'])
print(f"\n✅ Best: {best['name']} with {best['mae']:.3f} MAE")

print("\n" + "="*70)
print("✨ Model v6 test complete!")
