#!/usr/bin/env python3
"""
honest_model_enhanced.py — Enhanced honest model with handedness interactions
Leak-free features + handedness edge combinations
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
import json

print('='*70)
print('ENHANCED HONEST MODEL — With Handedness Interactions')
print('='*70)

df = pd.read_csv('data/processed/model_data_v4.csv')
print(f"\n📊 Loaded {len(df)} records")

# Create handedness interaction features (all leak-free)
# These capture how handedness combines with other pitcher traits

df['lhp_x_era'] = df['is_lhp'] * df['pitcher_era']           # Lefty with high ERA (bad combo)
df['lhp_x_ip'] = df['is_lhp'] * df['pitcher_ip']             # Experienced lefties
df['lhp_x_k9'] = df['is_lhp'] * df['pitcher_k9']             # Strikeout lefties
df['lhp_x_bb9'] = df['is_lhp'] * df['pitcher_bb9']           # Walk-prone lefties
df['lhp_x_hr_pct'] = df['is_lhp'] * df['pitcher_hr_pct']     # HR-prone lefties

# Also create non-LHP versions for symmetry
df['rhp_x_era'] = (1 - df['is_lhp']) * df['pitcher_era']
df['rhp_x_ip'] = (1 - df['is_lhp']) * df['pitcher_ip']

print("✅ Created handedness interaction features:")
print("  - lhp_x_era: Left-handedness × ERA")
print("  - lhp_x_ip: Left-handedness × Innings Pitched")
print("  - lhp_x_k9: Left-handedness × K/9")
print("  - lhp_x_bb9: Left-handedness × BB/9")
print("  - lhp_x_hr_pct: Left-handedness × HR%")

# All leak-free features + interactions
features = [
    # Base pitcher stats
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'is_lhp', 'pitcher_days_rest',
    # Handedness interactions
    'lhp_x_era', 'lhp_x_ip', 'lhp_x_k9', 'lhp_x_bb9', 'lhp_x_hr_pct'
]

# Train/test
train_df = df[df['year'].isin([2021, 2022, 2023])]
test_df = df[df['year'] == 2025]

X_train = train_df[features].fillna(0)
y_train = train_df['first_5_runs_allowed']
X_test = test_df[features].fillna(0)
y_test = test_df['first_5_runs_allowed']

print(f"\n🤖 Training enhanced model with {len(features)} features...")
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)
preds = model.predict(X_test)

mae = mean_absolute_error(y_test, preds)
print(f"\n📈 Results:")
print(f"  MAE: {mae:.3f}")

# Add predictions
test_df = test_df.copy()
test_df['pred'] = preds

# DUAL TIER ANALYSIS
print(f"\n{'='*70}")
print("ENHANCED DUAL TIER SYSTEM")
print(f"{'='*70}")

def analyze_tier(df, name, pred_min, pred_max, stake_mult):
    tier = df[(df['pred'] >= pred_min) & (df['pred'] < pred_max)]
    if len(tier) == 0:
        return {'bets': 0, 'wins': 0, 'win_rate': 0, 'pnl': 0}
    
    wins = (tier['first_5_runs_allowed'] < 2.5).sum()
    losses = len(tier) - wins
    win_rate = wins / len(tier) * 100
    
    win_amt = 227 * stake_mult
    loss_amt = 250 * stake_mult
    pnl = wins * win_amt - losses * loss_amt
    
    return {
        'bets': len(tier), 'wins': int(wins), 'losses': int(losses),
        'win_rate': win_rate, 'pnl': int(pnl),
        'stake_mult': stake_mult, 'avg_stake': 250 * stake_mult
    }

# Tier 1: High confidence
tier1 = analyze_tier(test_df, "High Conf", 0, 1.5, 1.5)
print(f"\nTier 1 — HIGH CONFIDENCE (pred < 1.5):")
print(f"  Bets: {tier1['bets']}, Win Rate: {tier1['win_rate']:.1f}%, P&L: ${tier1['pnl']:,}")

# Tier 2: Medium confidence
tier2 = analyze_tier(test_df, "Medium Conf", 1.5, 2.5, 1.0)
print(f"\nTier 2 — MEDIUM CONFIDENCE (1.5 ≤ pred < 2.5):")
print(f"  Bets: {tier2['bets']}, Win Rate: {tier2['win_rate']:.1f}%, P&L: ${tier2['pnl']:,}")

# Portfolio totals
total_bets = tier1['bets'] + tier2['bets']
total_pnl = tier1['pnl'] + tier2['pnl']
total_staked = tier1['bets'] * tier1['avg_stake'] + tier2['bets'] * tier2['avg_stake']

print(f"\n{'='*70}")
print("PORTFOLIO TOTALS (Enhanced)")
print(f"{'='*70}")
print(f"Total Bets: {total_bets}")
print(f"Total P&L: ${total_pnl:,}")
print(f"Portfolio ROI: {total_pnl/total_staked*100:.1f}%")

# Feature importance
importance = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n{'='*70}")
print("FEATURE IMPORTANCE (Enhanced)")
print(f"{'='*70}")

# Show base features vs handedness interactions
base_features = importance[~importance['feature'].str.startswith('lhp_')]
handedness_features = importance[importance['feature'].str.startswith('lhp_')]

print("\nBase Features:")
for _, row in base_features.head(8).iterrows():
    print(f"  {row['feature']:20s}: {row['importance']:.3f}")

print("\nHandedness Interactions:")
for _, row in handedness_features.iterrows():
    print(f"  {row['feature']:20s}: {row['importance']:.3f}")

total_handedness = handedness_features['importance'].sum()
print(f"\nTotal Handedness Importance: {total_handedness:.3f} ({total_handedness*100:.1f}%)")

# Compare to basic model
print(f"\n{'='*70}")
print("COMPARISON: Basic vs Enhanced")
print(f"{'='*70}")
print(f"Basic Model (9 features):  See honest_dual_system.py")
print(f"Enhanced Model (14 features): This run")
print(f"  MAE: {mae:.3f}")
print(f"  Total P&L: ${total_pnl:,}")
print(f"  ROI: {total_pnl/total_staked*100:.1f}%")

# Save
results = {
    'model': 'enhanced_honest',
    'mae': mae,
    'features': features,
    'handedness_importance': float(total_handedness),
    'tier1': tier1,
    'tier2': tier2,
    'total_pnl': total_pnl,
    'roi': total_pnl/total_staked*100
}

with open('enhanced_honest_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved: enhanced_honest_results.json")
print("\n" + "="*70)
print("✨ Enhanced Model Complete with Handedness Edge!")
print("="*70)
