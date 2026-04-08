#!/usr/bin/env python3
"""
manual_lookup.py — Manual pitcher lookup for quick predictions

Use when:
- ESPN lineups not updated yet
- You know the starters from another source
- Need quick prediction before game time

Usage: python manual_lookup.py "Pitcher Name"
"""

import pandas as pd
import sys

print('='*70)
print('MLB First-5 — Manual Pitcher Lookup')
print('='*70)

# Load data
df = pd.read_csv('/root/noesis-prediction/mlb_first5/data/processed/model_data_v4.csv')

def get_pitcher_prediction(pitcher_name):
    """Get prediction for a specific pitcher"""
    
    # Search by last name
    last_name = pitcher_name.split()[-1]
    matches = df[df['pitcher_name'].str.contains(last_name, case=False, na=False)]
    
    if len(matches) == 0:
        print(f'❌ No data found for {pitcher_name}')
        return None
    
    # Get most recent stats
    latest = matches[matches['year'] == matches['year'].max()].iloc[0]
    
    # Simple prediction model
    base = latest['pitcher_era'] * 0.4
    opp_factor = latest['opp_avg_first5_allowed'] * 0.3
    whip_factor = latest['pitcher_whip'] * 0.2
    k_factor = (10 - latest['pitcher_k9']) * 0.1
    
    prediction = base + opp_factor + whip_factor + k_factor
    
    if latest['is_lhp']:
        prediction *= 0.95
    
    prediction = max(0, min(5, prediction))
    
    return {
        'name': latest['pitcher_name'],
        'era': latest['pitcher_era'],
        'whip': latest['pitcher_whip'],
        'k9': latest['pitcher_k9'],
        'is_lhp': bool(latest['is_lhp']),
        'predicted': prediction,
        'last_season': int(latest['year'])
    }

def main():
    # Interactive mode
    if len(sys.argv) > 1:
        # Command line argument
        pitcher_name = ' '.join(sys.argv[1:])
        result = get_pitcher_prediction(pitcher_name)
        
        if result:
            print(f"\n✅ Found: {result['name']}")
            print(f"  Last season: {result['last_season']}")
            print(f"  ERA: {result['era']:.2f}")
            print(f"  WHIP: {result['whip']:.2f}")
            print(f"  K/9: {result['k9']:.2f}")
            print(f"  Hand: {'LHP' if result['is_lhp'] else 'RHP'}")
            print(f"  ➜ Predicted runs allowed: {result['predicted']:.2f}")
            
            if result['predicted'] < 1.0:
                print(f"  🎯 QUALIFIES: Bet Opponent UNDER 2.5")
            elif result['predicted'] < 1.5:
                print(f"  ⚠️  BORDERLINE: Consider small bet")
            else:
                print(f"  ❌ NO BET: Prediction too high")
    else:
        # Interactive loop
        print("\nEnter pitcher names (or 'quit' to exit):")
        
        while True:
            print()
            name = input('Pitcher name: ').strip()
            
            if name.lower() in ['quit', 'exit', 'q']:
                break
            
            if not name:
                continue
            
            result = get_pitcher_prediction(name)
            
            if result:
                print(f"\n  {result['name']} ({result['last_season']})")
                print(f"  ERA: {result['era']:.2f} | WHIP: {result['whip']:.2f} | K/9: {result['k9']:.2f}")
                print(f"  Predicted: {result['predicted']:.2f} runs")
                
                if result['predicted'] < 1.0:
                    print(f"  ✅ QUALIFIES — Bet Opponent UNDER 2.5")
                elif result['predicted'] < 1.5:
                    print(f"  ⚠️  BORDERLINE")
                else:
                    print(f"  ❌ NO BET")

if __name__ == '__main__':
    main()
