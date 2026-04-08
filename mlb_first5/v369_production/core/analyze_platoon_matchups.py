#!/usr/bin/env python3
"""
analyze_platoon_matchups.py — Calculate platoon advantage and lineup strength
"""
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

print('='*70)
print('PLATOON MATCHUP ANALYZER')
print('='*70)

def load_lineups(date_str):
    """Load confirmed lineups for date"""
    lineup_file = Path(f'v369_production/daily_predictions/{date_str}_confirmed_lineups.json')
    if not lineup_file.exists():
        return []
    
    with open(lineup_file, 'r') as f:
        return json.load(f)

def load_historical_splits():
    """Load historical OPS splits from database"""
    # This would come from a database of player splits
    # For now, using league averages
    return {
        'L_vs_LHP': 0.698,
        'L_vs_RHP': 0.765,
        'R_vs_LHP': 0.788,
        'R_vs_RHP': 0.738,
        'S_vs_LHP': 0.732,
        'S_vs_RHP': 0.748
    }

def calculate_platoon_advantage(lineup, pitcher_hand):
    """Calculate platoon advantage percentage for a lineup"""
    splits = load_historical_splits()
    
    advantages = 0
    total_ops = 0
    
    for spot in lineup:
        hand = spot['hand']  # L, R, or S
        
        # Get expected OPS based on matchup
        key = f"{hand}_vs_{pitcher_hand}"
        expected_ops = splits.get(key, 0.730)  # Default to league avg
        
        # Platoon advantage if OPS > 0.750
        if expected_ops > 0.750:
            advantages += 1
        
        total_ops += expected_ops
    
    avg_ops = total_ops / len(lineup) if lineup else 0.730
    advantage_pct = advantages / len(lineup) if lineup else 0.5
    
    return {
        'platoon_advantage_pct': round(advantage_pct, 3),
        'avg_ops_vs_pitcher': round(avg_ops, 3),
        'num_batters': len(lineup)
    }

def calculate_lineup_strength_score(platoon_stats, base_prediction):
    """Calculate lineup strength adjustment factor"""
    adv_pct = platoon_stats['platoon_advantage_pct']
    avg_ops = platoon_stats['avg_ops_vs_pitcher']
    
    # Base factor is 1.0 (neutral)
    factor = 1.0
    
    # Adjust based on platoon advantage
    if adv_pct > 0.60:  # Strong advantage
        factor += 0.15
    elif adv_pct > 0.50:  # Moderate advantage
        factor += 0.08
    elif adv_pct < 0.30:  # Disadvantage
        factor -= 0.12
    elif adv_pct < 0.40:  # Slight disadvantage
        factor -= 0.06
    
    # Additional adjustment for OPS
    ops_diff = avg_ops - 0.730  # League average
    factor += ops_diff * 0.5  # Scale factor
    
    return round(factor, 3)

def analyze_all_matchups(date_str):
    """Analyze all confirmed lineups for a date"""
    lineups = load_lineups(date_str)
    
    if not lineups:
        print(f"No confirmed lineups found for {date_str}")
        return []
    
    print(f"\nAnalyzing {len(lineups)} lineups...\n")
    
    results = []
    
    for lu in lineups:
        print(f"{lu['team_abbr']} vs {lu['pitcher']} ({lu['pitcher_hand']})")
        
        # Get platoon stats
        platoon = calculate_platoon_advantage(lu['lineup'], lu['pitcher_hand'])
        
        # Calculate strength score (would need base prediction from model)
        strength_score = calculate_lineup_strength_score(platoon, 2.0)
        
        # Determine recommendation
        if strength_score > 1.15:
            rec = "STRONG (+0.4 runs)"
        elif strength_score > 1.05:
            rec = "FAVORABLE (+0.2 runs)"
        elif strength_score < 0.85:
            rec = "WEAK (-0.4 runs)"
        elif strength_score < 0.95:
            rec = "UNFAVORABLE (-0.2 runs)"
        else:
            rec = "NEUTRAL (no change)"
        
        print(f"  Platoon Advantage: {platoon['platoon_advantage_pct']:.1%}")
        print(f"  Avg OPS vs {lu['pitcher_hand']}: {platoon['avg_ops_vs_pitcher']}")
        print(f"  Strength Score: {strength_score}")
        print(f"  Adjustment: {rec}")
        print()
        
        results.append({
            'game_id': lu['game_id'],
            'team': lu['team'],
            'team_abbr': lu['team_abbr'],
            'pitcher': lu['pitcher'],
            'pitcher_hand': lu['pitcher_hand'],
            'platoon_advantage_pct': platoon['platoon_advantage_pct'],
            'avg_ops': platoon['avg_ops_vs_pitcher'],
            'strength_score': strength_score,
            'adjustment': rec
        })
    
    return results

def save_analysis(results, date_str):
    """Save matchup analysis"""
    output_file = Path(f'v369_production/daily_predictions/{date_str}_platoon_analysis.json')
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Analysis saved: {output_file}")
    return output_file

def main():
    # Get today's date
    today = datetime.now().strftime('%Y%m%d')
    
    print(f"Analyzing matchups for {today}...")
    
    # Analyze all matchups
    results = analyze_all_matchups(today)
    
    if results:
        # Save results
        save_analysis(results, today)
        
        # Summary
        strong = sum(1 for r in results if r['strength_score'] > 1.15)
        weak = sum(1 for r in results if r['strength_score'] < 0.85)
        
        print("="*70)
        print("SUMMARY")
        print("="*70)
        print(f"Total lineups analyzed: {len(results)}")
        print(f"Strong lineups (>1.15): {strong}")
        print(f"Weak lineups (<0.85): {weak}")
        print(f"\nNext: Run adjust_predictions.py to update betting decisions")
    else:
        print("\n⚠️  No lineups to analyze. Run fetch_confirmed_lineups.py first.")

if __name__ == "__main__":
    main()
