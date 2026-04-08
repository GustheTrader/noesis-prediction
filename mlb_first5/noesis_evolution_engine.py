#!/usr/bin/env python3
"""
noesis_evolution_engine.py — RL-based model evolution from losers + auto-research
Learn from mistakes, discover new features, evolve the model
"""
import pandas as pd
import numpy as np
import json
from collections import defaultdict
from datetime import datetime
import subprocess

print('='*70)
print('NOESIS EVOLUTION ENGINE — Learning from Losers')
print('='*70)

# Load 2026 results
print("\n📊 Loading 2026 YTD results...")
with open('v369_production/daily_predictions/2026_ytd_results.json', 'r') as f:
    results_2026 = json.load(f)

results = results_2026['results']
print(f"✅ Loaded {len(results)} results")

# Separate wins and losses
wins = [r for r in results if r['result'] == 'WIN']
losses = [r for r in results if r['result'] == 'LOSS']

print(f"\n🏆 Wins: {len(wins)}")
print(f"💔 Losses: {len(losses)}")

# PHASE 1: Analyze loss patterns
print("\n" + "="*70)
print("PHASE 1: LOSS PATTERN ANALYSIS")
print("="*70)

# Common patterns in losses
loss_patterns = defaultdict(list)

for loss in losses:
    # Pattern: Predicted runs vs actual
    pred = loss['predicted']
    actual = loss['actual']
    diff = actual - pred
    
    # Categorize by prediction range
    if pred < 1.5:
        category = "Tier_1_high_conf"
    elif pred < 2.5:
        category = "Tier_2_medium_conf"
    else:
        category = "Tier_3_no_bet"
    
    # Categorize by miss magnitude
    if diff > 3:
        miss_type = "Blowout_3+"
    elif diff > 1.5:
        miss_type = "Big_miss_1.5-3"
    else:
        miss_type = "Close_miss_<1.5"
    
    loss_patterns[category].append({
        'game': loss['game'],
        'predicted': pred,
        'actual': actual,
        'diff': diff,
        'miss_type': miss_type
    })

print("\nLoss Patterns by Category:")
for cat, items in loss_patterns.items():
    print(f"\n  {cat}: {len(items)} losses")
    miss_counts = defaultdict(int)
    for item in items:
        miss_counts[item['miss_type']] += 1
    for miss, count in miss_counts.items():
        print(f"    - {miss}: {count}")

# PHASE 2: Identify improvement opportunities
print("\n" + "="*70)
print("PHASE 2: IMPROVEMENT OPPORTUNITIES")
print("="*70)

opportunities = []

# Opportunity 1: Over-confident Tier 1 predictions
tier1_losses = loss_patterns.get('Tier_1_high_conf', [])
if tier1_losses:
    avg_diff = np.mean([l['diff'] for l in tier1_losses])
    opportunities.append({
        'type': 'Calibration',
        'issue': 'Tier 1 over-confidence',
        'count': len(tier1_losses),
        'avg_miss': round(avg_diff, 2),
        'action': 'Increase Tier 1 threshold from 1.5 to 1.3',
        'potential_impact': f"Avoid {len(tier1_losses)} losses"
    })

# Opportunity 2: Blowout games
blowout_losses = [l for l in losses if l['actual'] - l['predicted'] > 3]
if blowout_losses:
    opportunities.append({
        'type': 'Feature_Gap',
        'issue': 'Missing blowout indicator',
        'count': len(blowout_losses),
        'avg_actual': round(np.mean([l['actual'] for l in blowout_losses]), 2),
        'action': 'Add weather/wind features for high-scoring conditions',
        'potential_impact': f"Filter {len(blowout_losses)} high-risk games"
    })

# Opportunity 3: Close games (near misses)
close_losses = [l for l in losses if l['actual'] - l['predicted'] < 1]
if close_losses:
    opportunities.append({
        'type': 'Fine_Tuning',
        'issue': 'Near misses (within 1 run)',
        'count': len(close_losses),
        'action': 'Add umpire strike zone features',
        'potential_impact': 'Improve edge detection by 5-10%'
    })

print("\nTop Opportunities:")
for i, opp in enumerate(opportunities, 1):
    print(f"\n{i}. {opp['type']}: {opp['issue']}")
    print(f"   Occurrences: {opp['count']}")
    print(f"   Action: {opp['action']}")
    print(f"   Impact: {opp['potential_impact']}")

# PHASE 3: Auto-research suggestions
print("\n" + "="*70)
print("PHASE 3: AUTO-RESEARCH IDEAS")
print("="*70)

research_ideas = [
    {
        'idea': 'Bullpen fatigue indicator',
        'hypothesis': 'Tired bullpens lead to earlier starter pulls and more runs',
        'data_source': 'ESPN team rosters / pitcher usage',
        'feature_name': 'bullpen_ip_last_3_days',
        'expected_improvement': '+2-3% win rate'
    },
    {
        'idea': 'Umpire strike zone tightness',
        'hypothesis': 'Umpires with small zones favor hitters',
        'data_source': 'Baseball Savant umpire data',
        'feature_name': 'umpire_zone_size',
        'expected_improvement': '+1-2% win rate'
    },
    {
        'idea': 'Travel fatigue',
        'hypothesis': 'Teams on long road trips underperform',
        'data_source': 'ESPN schedule data',
        'feature_name': 'days_on_road',
        'expected_improvement': '+1-2% win rate'
    },
    {
        'idea': 'Division rival intensity',
        'hypothesis': 'Division games have different scoring patterns',
        'data_source': 'ESPN standings / game matchups',
        'feature_name': 'is_division_game',
        'expected_improvement': '+1% win rate'
    },
    {
        'idea': 'Weather-adjusted fly ball rate',
        'hypothesis': 'Wind affects HR rates differently by park',
        'data_source': 'Weather APIs + park dimensions',
        'feature_name': 'wind_adjusted_hr_factor',
        'expected_improvement': '+2-3% win rate'
    }
]

print("\nResearch Queue:")
for i, idea in enumerate(research_ideas, 1):
    print(f"\n{i}. {idea['idea']}")
    print(f"   Hypothesis: {idea['hypothesis']}")
    print(f"   Data: {idea['data_source']}")
    print(f"   Feature: {idea['feature_name']}")
    print(f"   Expected: {idea['expected_improvement']}")

# PHASE 4: RL Feedback Loop Design
print("\n" + "="*70)
print("PHASE 4: RL FEEDBACK LOOP ARCHITECTURE")
print("="*70)

rl_framework = """
┌─────────────────────────────────────────────────────────────┐
│                    NOESIS RL EVOLUTION                      │
└─────────────────────────────────────────────────────────────┘

STEP 1: PREDICT
   ↓
Model makes prediction → Place bet

STEP 2: OBSERVE
   ↓
Game completes → Record actual result

STEP 3: REWARD
   ↓
Win: +1 reward, update feature weights positively
Loss: -1 reward, analyze why

STEP 4: ANALYZE LOSS
   ↓
Was it:
   • Over-confidence? → Lower threshold
   • Missing feature? → Add to research queue
   • Random variance? → No action

STEP 5: ADAPT
   ↓
• Adjust tier thresholds (dynamic)
• Update feature importance weights
• Retrain model weekly with new data

STEP 6: RESEARCH
   ↓
Auto-scrape new data sources
Test new features on holdout data
A/B test vs current model

STEP 7: DEPLOY
   ↓
If new model beats current by >2%:
   Deploy as v370
Else:
   Keep v369, queue improvements

┌─────────────────────────────────────────────────────────────┐
│  EVOLUTION METRICS                                          │
│  • Prediction error trend (should decrease)                │
│  • Loss rate by category (target specific patterns)        │
│  • Feature importance drift (detect concept drift)         │
│  • New feature contribution (validate research)            │
└─────────────────────────────────────────────────────────────┘
"""

print(rl_framework)

# PHASE 5: Generate evolution report
print("\n" + "="*70)
print("PHASE 5: EVOLUTION REPORT")
print("="*70)

report = {
    'timestamp': datetime.now().isoformat(),
    'version': 'v369',
    'analysis_period': '2026-03-26 to 2026-04-07',
    'summary': {
        'total_games': len(results),
        'wins': len(wins),
        'losses': len(losses),
        'win_rate': len(wins) / len([r for r in results if r['stake'] > 0]) * 100
    },
    'loss_analysis': {
        'tier_1_losses': len(tier1_losses),
        'blowout_losses': len(blowout_losses),
        'close_losses': len(close_losses)
    },
    'improvement_opportunities': opportunities,
    'research_queue': research_ideas[:3],  # Top 3
    'recommended_actions': [
        'Increase Tier 1 threshold from 1.5 to 1.3',
        'Add bullpen fatigue feature',
        'Implement weekly model retraining',
        'A/B test new features on 10% of bets'
    ]
}

# Save report
with open('v369_production/evolution_report_latest.json', 'w') as f:
    json.dump(report, f, indent=2)

print("\n✅ Evolution report saved: evolution_report_latest.json")

# PHASE 6: Next steps
print("\n" + "="*70)
print("PHASE 6: IMPLEMENTATION ROADMAP")
print("="*70)

roadmap = """
WEEK 1: Immediate Fixes
• Adjust Tier 1 threshold to 1.3 (avoid over-confidence)
• Document loss patterns for future reference

WEEK 2: Feature Engineering  
• Scrape bullpen usage data from ESPN
• Calculate bullpen fatigue metric
• Test on 2025 holdout data

WEEK 3: Model Retraining
• Retrain v369 with new features
• Validate no data leakage
• Compare vs baseline

WEEK 4: A/B Testing
• Deploy v370 to 20% of predictions
• Monitor win rate vs v369
• If +2% improvement, full deploy

ONGOING: Auto-Research
• Daily: Scrape new data sources
• Weekly: Retrain model
• Monthly: Evaluate new features
• Quarterly: Major version release
"""

print(roadmap)

print("\n" + "="*70)
print("✨ EVOLUTION ENGINE ANALYSIS COMPLETE")
print("="*70)
print("\nNext Action: Implement Tier 1 threshold adjustment")
print("Command: python3 v369_production/core/adapt_thresholds.py")
