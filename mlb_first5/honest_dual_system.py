#!/usr/bin/env python3
"""
honest_dual_system.py — Dual tier system with ONLY leak-free features
Tier 1: High confidence (predicted < 1.5) — 1.5x stake
Tier 2: Medium confidence (predicted 1.5-2.5) — 1.0x stake
Tier 3: Low confidence (predicted > 2.5) — No bet
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
import json

print('='*70)
print('HONEST DUAL SYSTEM — Leak-Free Features Only')
print('='*70)

df = pd.read_csv('data/processed/model_data_v4.csv')
print(f"\n📊 Loaded {len(df)} records")

# LEAK-FREE FEATURES ONLY
features = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'is_lhp', 'pitcher_days_rest'
]

# Train/test
train_df = df[df['year'].isin([2021, 2022, 2023])]
test_df = df[df['year'] == 2025]

X_train = train_df[features].fillna(0)
y_train = train_df['first_5_runs_allowed']
X_test = test_df[features].fillna(0)
y_test = test_df['first_5_runs_allowed']

print(f"\n🤖 Training honest model...")
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
model.fit(X_train, y_train)
preds = model.predict(X_test)

mae = mean_absolute_error(y_test, preds)
print(f"  MAE: {mae:.3f}")

# Add predictions
test_df = test_df.copy()
test_df['pred'] = preds

# DUAL TIER SYSTEM
def analyze_tier(df, name, pred_min, pred_max, stake_mult):
    """Analyze a betting tier"""
    tier = df[(df['pred'] >= pred_min) & (df['pred'] < pred_max)]
    
    if len(tier) == 0:
        return {'bets': 0, 'wins': 0, 'win_rate': 0, 'pnl': 0, 'stake_mult': stake_mult}
    
    wins = (tier['first_5_runs_allowed'] < 2.5).sum()
    losses = len(tier) - wins
    win_rate = wins / len(tier) * 100
    
    win_amt = 227 * stake_mult
    loss_amt = 250 * stake_mult
    pnl = wins * win_amt - losses * loss_amt
    
    return {
        'bets': len(tier),
        'wins': int(wins),
        'losses': int(losses),
        'win_rate': win_rate,
        'pnl': int(pnl),
        'stake_mult': stake_mult,
        'avg_stake': 250 * stake_mult
    }

print(f"\n{'='*70}")
print("HONEST DUAL TIER SYSTEM")
print(f"{'='*70}")

# Tier 1: High confidence (predicted < 1.5)
tier1 = analyze_tier(test_df, "High Conf", 0, 1.5, 1.5)
print(f"\nTier 1 — HIGH CONFIDENCE (pred < 1.5):")
print(f"  Bets: {tier1['bets']}")
print(f"  Win Rate: {tier1['win_rate']:.1f}%")
print(f"  Stake: ${tier1['avg_stake']:.0f} per bet")
print(f"  P&L: ${tier1['pnl']:,}")

# Tier 2: Medium confidence (predicted 1.5-2.5)
tier2 = analyze_tier(test_df, "Medium Conf", 1.5, 2.5, 1.0)
print(f"\nTier 2 — MEDIUM CONFIDENCE (1.5 ≤ pred < 2.5):")
print(f"  Bets: {tier2['bets']}")
print(f"  Win Rate: {tier2['win_rate']:.1f}%")
print(f"  Stake: ${tier2['avg_stake']:.0f} per bet")
print(f"  P&L: ${tier2['pnl']:,}")

# Tier 3: Low confidence (predicted > 2.5) — NO BET
tier3 = analyze_tier(test_df, "Low Conf", 2.5, 999, 0)
print(f"\nTier 3 — LOW CONFIDENCE (pred ≥ 2.5):")
print(f"  Bets: 0 (NO BET)")
print(f"  Would have been: {len(test_df[test_df['pred'] >= 2.5])} games")

# Portfolio totals
total_bets = tier1['bets'] + tier2['bets']
total_wins = tier1['wins'] + tier2['wins']
total_pnl = tier1['pnl'] + tier2['pnl']
total_staked = (tier1['bets'] * tier1['avg_stake'] + tier2['bets'] * tier2['avg_stake'])

print(f"\n{'='*70}")
print("PORTFOLIO TOTALS (Honest)")
print(f"{'='*70}")
print(f"Total Bets: {total_bets}")
print(f"Total Wins: {total_wins}")
print(f"Overall Win Rate: {total_wins/total_bets*100:.1f}%")
print(f"Total P&L: ${total_pnl:,}")
print(f"Total Staked: ${total_staked:,.0f}")
print(f"Portfolio ROI: {total_pnl/total_staked*100:.1f}%")

# Feature importance
importance = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\n{'='*70}")
print("FEATURE IMPORTANCE")
print(f"{'='*70}")
for _, row in importance.iterrows():
    print(f"  {row['feature']:20s}: {row['importance']:.3f}")

# Save results
results = {
    'model': 'honest_dual_system',
    'mae': mae,
    'total_bets': total_bets,
    'total_wins': total_wins,
    'win_rate': total_wins/total_bets*100,
    'total_pnl': total_pnl,
    'roi': total_pnl/total_staked*100,
    'tiers': {
        'tier1_high': tier1,
        'tier2_medium': tier2
    },
    'feature_importance': importance.to_dict()
}

with open('honest_dual_system_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved: honest_dual_system_results.json")
print("\n" + "="*70)
print("✨ HONEST Dual System Complete — Realistic Expectations")
print("="*70)
