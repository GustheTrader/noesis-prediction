#!/usr/bin/env python3
"""
adjust_predictions.py — Adjust base predictions with lineup analysis
Apply platoon matchup factors to update betting tiers
"""
import json
import argparse
from datetime import datetime
from pathlib import Path

def load_predictions(date_str, time_period):
    """Load base predictions"""
    pred_file = Path(f'v369_production/daily_predictions/{date_str}_predictions_{time_period}.json')
    if not pred_file.exists():
        # Try to load from todays_predictions
        pred_file = Path(f'v369_production/daily_predictions/2026-04/2026-04-08_predictions.json')
    
    if pred_file.exists():
        with open(pred_file, 'r') as f:
            return json.load(f)
    return []

def load_platoon_analysis(date_str):
    """Load platoon matchup analysis"""
    analysis_file = Path(f'v369_production/daily_predictions/{date_str}_platoon_analysis.json')
    if not analysis_file.exists():
        return []
    
    with open(analysis_file, 'r') as f:
        return json.load(f)

def adjust_prediction(base_pred, strength_score):
    """Adjust prediction based on lineup strength"""
    # Apply lineup factor
    adjusted = base_pred * strength_score
    return round(adjusted, 2)

def get_tier_and_stake(adjusted_pred):
    """Determine tier and stake based on adjusted prediction"""
    if adjusted_pred < 1.0:
        return 'ELITE', 500
    elif adjusted_pred < 1.5:
        return 'TIER 1', 375
    elif adjusted_pred < 2.5:
        return 'TIER 2', 250
    else:
        return 'NO BET', 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--time', choices=['early', 'late', 'all'], default='all')
    args = parser.parse_args()
    
    date_str = datetime.now().strftime('%Y%m%d')
    
    print("="*70)
    print(f"ADJUSTING PREDICTIONS WITH LINEUP DATA ({args.time.upper()})")
    print("="*70)
    
    # Load base predictions
    predictions = load_predictions(date_str, args.time)
    if not predictions:
        print(f"No predictions found for {date_str}")
        return
    
    # Load platoon analysis
    platoon_data = load_platoon_analysis(date_str)
    if not platoon_data:
        print(f"No platoon analysis found. Run analyze_platoon_matchups.py first.")
        return
    
    # Create lookup by team
    platoon_lookup = {p['team']: p for p in platoon_data}
    
    # Adjust predictions
    adjusted_predictions = []
    changes = []
    
    for pred in predictions:
        team = pred.get('team', '')
        base_pred = pred.get('pred', 2.0)
        original_tier = pred.get('tier', 'TIER 2')
        
        # Check if we have platoon data for this team
        if team in platoon_lookup:
            platoon = platoon_lookup[team]
            strength_score = platoon['strength_score']
            
            # Adjust prediction
            adjusted = adjust_prediction(base_pred, strength_score)
            new_tier, new_stake = get_tier_and_stake(adjusted)
            
            # Track changes
            if original_tier != new_tier:
                changes.append({
                    'team': team,
                    'pitcher': pred.get('pitcher', ''),
                    'original': f"{base_pred} ({original_tier})",
                    'adjusted': f"{adjusted} ({new_tier})",
                    'reason': platoon['adjustment']
                })
            
            adjusted_predictions.append({
                **pred,
                'original_pred': base_pred,
                'adjusted_pred': adjusted,
                'strength_score': strength_score,
                'platoon_advantage': platoon['platoon_advantage_pct'],
                'tier': new_tier,
                'stake': new_stake
            })
        else:
            # No platoon data, keep original
            adjusted_predictions.append(pred)
    
    # Save adjusted predictions
    output_file = Path(f'v369_production/daily_predictions/{date_str}_adjusted_{args.time}.json')
    with open(output_file, 'w') as f:
        json.dump(adjusted_predictions, f, indent=2)
    
    print(f"\n✅ Adjusted {len(adjusted_predictions)} predictions")
    print(f"   Saved to: {output_file}")
    
    # Report changes
    if changes:
        print(f"\n⚠️  TIER CHANGES ({len(changes)}):")
        for change in changes[:10]:  # Show first 10
            print(f"  {change['team']} - {change['pitcher']}")
            print(f"    {change['original']} → {change['adjusted']}")
            print(f"    Reason: {change['reason']}")
    else:
        print(f"\n✓ No tier changes. All predictions stable.")
    
    # Summary
    elite = sum(1 for p in adjusted_predictions if p.get('tier') == 'ELITE')
    tier1 = sum(1 for p in adjusted_predictions if p.get('tier') == 'TIER 1')
    tier2 = sum(1 for p in adjusted_predictions if p.get('tier') == 'TIER 2')
    no_bet = sum(1 for p in adjusted_predictions if p.get('tier') == 'NO BET')
    
    print(f"\n" + "="*70)
    print("FINAL BETTING RECOMMENDATIONS")
    print("="*70)
    print(f"  ELITE (Bet $500):  {elite}")
    print(f"  TIER 1 (Bet $375): {tier1}")
    print(f"  TIER 2 (Bet $250): {tier2}")
    print(f"  NO BET:            {no_bet}")
    
    total_stake = elite * 500 + tier1 * 375 + tier2 * 250
    print(f"\n  Total Daily Stake: ${total_stake:,}")

if __name__ == "__main__":
    main()
