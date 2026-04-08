#!/usr/bin/env python3
"""
dual_system_betting.py — Dual heat check system with portfolio edge management
14-game heat: Base layer (volume, 50% Kelly)
21-game heat: Conviction layer (selective, full Kelly)
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
import json

print('='*70)
print('DUAL SYSTEM — 14-day Base + 21-day Conviction')
print('='*70)

# Load data with both heat features
df = pd.read_csv('data/processed/model_data_v6.csv')  # Has both 14 and 21 game heat
print(f"\n📊 Loaded {len(df)} records")

# Train both models
train_df = df[df['year'].isin([2021, 2022, 2023])]
test_df = df[df['year'] == 2025]

y_train = train_df['first_5_runs_allowed']
y_test = test_df['first_5_runs_allowed']

# Model 1: 14-game heat (base layer)
features_14 = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'opp_avg_runs_allowed', 'opp_avg_first5_allowed',
    'is_lhp', 'opp_batting_first5', 'platoon_score',
    'opp_heat_14', 'heat_differential'
]

# Model 2: 21-game heat (conviction layer)
features_21 = [
    'pitcher_era', 'pitcher_whip', 'pitcher_k9', 'pitcher_bb9',
    'pitcher_ip', 'pitcher_k_pct', 'pitcher_hr_pct',
    'opp_avg_runs_allowed', 'opp_avg_first5_allowed',
    'is_lhp', 'opp_batting_first5', 'platoon_score',
    'opp_heat_21', 'heat_21_differential'
]

print("\n🤖 Training dual models...")

# Train 14-game model
model_14 = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
model_14.fit(train_df[features_14].fillna(0), y_train)
preds_14 = model_14.predict(test_df[features_14].fillna(0))

# Train 21-game model
model_21 = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=42)
model_21.fit(train_df[features_21].fillna(0), y_train)
preds_21 = model_21.predict(test_df[features_21].fillna(0))

# Add predictions to test data
test_df = test_df.copy()
test_df['pred_14'] = preds_14
test_df['pred_21'] = preds_21

# Dual System Strategy:
# Tier 1: Both 14-game AND 21-game predict < 1.0 → MAX conviction (full Kelly)
# Tier 2: Only 14-game predicts < 1.0 → Base bet (50% Kelly)
# Tier 3: Only 21-game predicts < 1.0 → Secondary conviction (75% Kelly)

tier1 = test_df[(test_df['pred_14'] < 1.0) & (test_df['pred_21'] < 1.0)]
tier2 = test_df[(test_df['pred_14'] < 1.0) & (test_df['pred_21'] >= 1.0)]
tier3 = test_df[(test_df['pred_14'] >= 1.0) & (test_df['pred_21'] < 1.0)]

print(f"\n{'='*70}")
print("DUAL SYSTEM BREAKDOWN")
print(f"{'='*70}")

def analyze_tier(tier_df, name, stake_mult):
    """Analyze a betting tier"""
    if len(tier_df) == 0:
        return {'bets': 0, 'wins': 0, 'win_rate': 0, 'pnl': 0, 'stake_mult': stake_mult}
    
    wins = (tier_df['first_5_runs_allowed'] < 2.5).sum()
    losses = len(tier_df) - wins
    win_rate = wins / len(tier_df) * 100
    
    # Apply stake multiplier
    win_amount = 227 * stake_mult
    loss_amount = 250 * stake_mult
    
    pnl = wins * win_amount - losses * loss_amount
    
    return {
        'bets': len(tier_df),
        'wins': int(wins),
        'losses': int(losses),
        'win_rate': win_rate,
        'pnl': int(pnl),
        'stake_mult': stake_mult,
        'avg_stake': 250 * stake_mult
    }

# Analyze each tier
results_tier1 = analyze_tier(tier1, "MAX Conviction (Both)", 2.0)  # 2x stake
results_tier2 = analyze_tier(tier2, "Base (14-game only)", 0.5)    # 50% stake
results_tier3 = analyze_tier(tier3, "Secondary (21-game only)", 1.0)  # 1x stake

print(f"\nTier 1 — MAX Conviction (Both 14 & 21 day < 1.0):")
print(f"  Bets: {results_tier1['bets']}")
print(f"  Win Rate: {results_tier1['win_rate']:.1f}%")
print(f"  Stake: ${results_tier1['avg_stake']:.0f} per bet (2x)")
print(f"  P&L: ${results_tier1['pnl']:,}")

print(f"\nTier 2 — Base Layer (14-day only < 1.0):")
print(f"  Bets: {results_tier2['bets']}")
print(f"  Win Rate: {results_tier2['win_rate']:.1f}%")
print(f"  Stake: ${results_tier2['avg_stake']:.0f} per bet (0.5x)")
print(f"  P&L: ${results_tier2['pnl']:,}")

print(f"\nTier 3 — Secondary (21-day only < 1.0):")
print(f"  Bets: {results_tier3['bets']}")
print(f"  Win Rate: {results_tier3['win_rate']:.1f}%")
print(f"  Stake: ${results_tier3['avg_stake']:.0f} per bet (1x)")
print(f"  P&L: ${results_tier3['pnl']:,}")

# Portfolio totals
total_bets = results_tier1['bets'] + results_tier2['bets'] + results_tier3['bets']
total_wins = results_tier1['wins'] + results_tier2['wins'] + results_tier3['wins']
total_pnl = results_tier1['pnl'] + results_tier2['pnl'] + results_tier3['pnl']
total_staked = (results_tier1['bets'] * results_tier1['avg_stake'] + 
                results_tier2['bets'] * results_tier2['avg_stake'] + 
                results_tier3['bets'] * results_tier3['avg_stake'])

print(f"\n{'='*70}")
print("PORTFOLIO TOTALS")
print(f"{'='*70}")
print(f"Total Bets: {total_bets}")
print(f"Total Wins: {total_wins}")
print(f"Overall Win Rate: {total_wins/total_bets*100:.1f}%" if total_bets > 0 else "N/A")
print(f"Total P&L: ${total_pnl:,}")
print(f"Total Staked: ${total_staked:,.0f}")
print(f"Portfolio ROI: {total_pnl/total_staked*100:.1f}%" if total_staked > 0 else "N/A")

# Compare to single systems
single_14 = test_df[test_df['pred_14'] < 1.0]
single_21 = test_df[test_df['pred_21'] < 1.0]

wins_14 = (single_14['first_5_runs_allowed'] < 2.5).sum()
pnl_14 = wins_14 * 227 - (len(single_14) - wins_14) * 250

wins_21 = (single_21['first_5_runs_allowed'] < 2.5).sum()
pnl_21 = wins_21 * 227 - (len(single_21) - wins_21) * 250

print(f"\n{'='*70}")
print("COMPARISON TO SINGLE SYSTEMS")
print(f"{'='*70}")
print(f"14-game only:  {len(single_14)} bets, ${pnl_14:,} P&L")
print(f"21-game only:  {len(single_21)} bets, ${pnl_21:,} P&L")
print(f"DUAL SYSTEM:   {total_bets} bets, ${total_pnl:,} P&L")

improvement = total_pnl - max(pnl_14, pnl_21)
print(f"\nImprovement over best single: ${improvement:,}")

# Save results
results = {
    'dual_system': {
        'total_bets': total_bets,
        'total_wins': int(total_wins),
        'total_pnl': int(total_pnl),
        'roi': total_pnl/total_staked*100 if total_staked > 0 else 0,
        'tiers': {
            'tier1_max_conviction': results_tier1,
            'tier2_base': results_tier2,
            'tier3_secondary': results_tier3
        }
    },
    'single_systems': {
        '14_game': {'bets': len(single_14), 'pnl': int(pnl_14)},
        '21_game': {'bets': len(single_21), 'pnl': int(pnl_21)}
    }
}

with open('dual_system_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved to: dual_system_results.json")
print("\n" + "="*70)
print("✨ Dual System Analysis Complete!")
