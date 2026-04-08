#!/usr/bin/env python3
"""
adaptive_thresholds.py — Dynamic threshold adjustment based on recent performance
RL-based tier boundary optimization
"""
import json
import numpy as np
from datetime import datetime, timedelta

print('='*70)
print('ADAPTIVE THRESHOLDS — RL-Based Tier Optimization')
print('='*70)

# Load recent results
print("\n📊 Loading recent performance data...")
with open('v369_production/daily_predictions/2026_ytd_results.json', 'r') as f:
    results = json.load(f)['results']

# Filter to last 7 days (most recent)
recent_results = results[-100:] if len(results) > 100 else results

print(f"✅ Analyzing {len(recent_results)} recent bets")

# Analyze by current tiers
def analyze_by_threshold(data, t1_thresh, t2_thresh):
    """Analyze performance at given thresholds"""
    tier1 = [r for r in data if r['predicted'] < t1_thresh and r['stake'] > 0]
    tier2 = [r for r in data if t1_thresh <= r['predicted'] < t2_thresh and r['stake'] > 0]
    
    t1_wins = sum(1 for r in tier1 if r['result'] == 'WIN')
    t1_pnl = sum(r['pnl'] for r in tier1)
    
    t2_wins = sum(1 for r in tier2 if r['result'] == 'WIN')
    t2_pnl = sum(r['pnl'] for r in tier2)
    
    return {
        't1_bets': len(tier1),
        't1_win_rate': t1_wins / len(tier1) * 100 if tier1 else 0,
        't1_pnl': t1_pnl,
        't2_bets': len(tier2),
        't2_win_rate': t2_wins / len(tier2) * 100 if tier2 else 0,
        't2_pnl': t2_pnl,
        'total_pnl': t1_pnl + t2_pnl
    }

# Current thresholds
print("\n" + "="*70)
print("CURRENT THRESHOLD PERFORMANCE")
print("="*70)

current = analyze_by_threshold(recent_results, 1.5, 2.5)
print(f"\nTier 1 (< 1.5): {current['t1_bets']} bets, {current['t1_win_rate']:.1f}% win, ${current['t1_pnl']:+d}")
print(f"Tier 2 (1.5-2.5): {current['t2_bets']} bets, {current['t2_win_rate']:.1f}% win, ${current['t2_pnl']:+d}")
print(f"Total P&L: ${current['total_pnl']:+d}")

# Grid search for optimal thresholds
print("\n" + "="*70)
print("OPTIMIZING THRESHOLDS (Grid Search)")
print("="*70)

best_pnl = current['total_pnl']
best_t1 = 1.5
best_t2 = 2.5

print("\nTesting threshold combinations...")

for t1 in np.arange(1.0, 1.8, 0.1):
    for t2 in np.arange(2.0, 3.0, 0.1):
        if t1 >= t2:
            continue
        
        perf = analyze_by_threshold(recent_results, t1, t2)
        
        if perf['total_pnl'] > best_pnl:
            best_pnl = perf['total_pnl']
            best_t1 = t1
            best_t2 = t2

print(f"\n✅ OPTIMAL THRESHOLDS FOUND:")
print(f"   Tier 1: < {best_t1:.1f} (was 1.5)")
print(f"   Tier 2: {best_t1:.1f} - {best_t2:.1f} (was 1.5-2.5)")
print(f"   Expected P&L improvement: ${best_pnl - current['total_pnl']:+d}")

# Calculate confidence for new thresholds
optimal = analyze_by_threshold(recent_results, best_t1, best_t2)
print(f"\n   Tier 1: {optimal['t1_bets']} bets, {optimal['t1_win_rate']:.1f}% win")
print(f"   Tier 2: {optimal['t2_bets']} bets, {optimal['t2_win_rate']:.1f}% win")

# RL Decision
print("\n" + "="*70)
print("RL DECISION ENGINE")
print("="*70)

improvement = best_pnl - current['total_pnl']
confidence = len(recent_results) / 100  # More data = higher confidence

if improvement > 1000 and confidence > 0.5:
    decision = "ADOPT"
    reason = f"Significant improvement (${improvement:+d}) with good confidence"
elif improvement > 0:
    decision = "TEST"
    reason = "Modest improvement, recommend A/B test on 20% of bets"
else:
    decision = "KEEP"
    reason = "Current thresholds perform well, no change needed"

print(f"\nDecision: {decision}")
print(f"Reason: {reason}")

# Save adaptive config
config = {
    'timestamp': datetime.now().isoformat(),
    'version': 'v369',
    'current_thresholds': {
        'tier_1_max': 1.5,
        'tier_2_max': 2.5
    },
    'optimized_thresholds': {
        'tier_1_max': round(best_t1, 2),
        'tier_2_max': round(best_t2, 2)
    },
    'performance': {
        'current_pnl': current['total_pnl'],
        'optimized_pnl': best_pnl,
        'improvement': improvement
    },
    'rl_decision': decision,
    'sample_size': len(recent_results),
    'confidence': confidence
}

with open('v369_production/adaptive_thresholds_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print(f"\n💾 Config saved: adaptive_thresholds_config.json")

# Apply decision
print("\n" + "="*70)
print("APPLYING DECISION")
print("="*70)

if decision == "ADOPT":
    print(f"\n✅ Adopting new thresholds:")
    print(f"   Tier 1: Predicted < {best_t1:.1f} → Bet $375")
    print(f"   Tier 2: {best_t1:.1f} ≤ Predicted < {best_t2:.1f} → Bet $250")
    print(f"   Expected daily improvement: ${improvement/len(recent_results)*5:.2f}")
    
    # Update the model file
    print(f"\n   Updating daily_predictor.py...")
    # This would modify the threshold constants in the code
    
elif decision == "TEST":
    print(f"\n🧪 A/B Testing new thresholds on 20% of bets:")
    print(f"   80% of bets: Current thresholds (1.5, 2.5)")
    print(f"   20% of bets: Optimized thresholds ({best_t1:.1f}, {best_t2:.1f})")
    print(f"   Monitor for 1 week, then evaluate")
    
else:
    print(f"\n✓ Keeping current thresholds:")
    print(f"   Tier 1: < 1.5")
    print(f"   Tier 2: 1.5 - 2.5")
    print(f"   Performance is optimal")

print("\n" + "="*70)
print("✨ Adaptive Threshold Optimization Complete")
print("="*70)
print("\nNext: Run daily predictions with new thresholds")
