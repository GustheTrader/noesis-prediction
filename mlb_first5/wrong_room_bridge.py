#!/usr/bin/env python3
"""
wrong_room_bridge.py
Connects the MLB first-5 prediction pipeline to the Wrong Room Collective agent architecture.

The agent can now:
1. PERCEIVE: Read MLB data
2. INTUIT: Use Noesis (nanoGPT) for probabilistic insights
3. DECIDE: Use curiosity engine logic
4. EXECUTE: Run model predictions
5. EVOLVE: Learn from outcomes via meta-evolver
"""
import os
import sys
import csv
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add mlb-first5 to path
sys.path.insert(0, '/root/mlb-first5')

from agent import WrongRoomAgent, create_agent


class WrongRoomBridge:
    """
    Bridge between MLB prediction pipeline and Wrong Room Collective agent.
    
    Orchestrates the agent's perception → intuition → decision → execution → evolution cycle.
    """
    
    def __init__(self, data_csv=None, model_path=None, use_noesis=True):
        self.data_csv = data_csv or '/root/mlb-first5/data/processed/model_data.csv'
        self.model_path = model_path or '/root/mlb-first5/data/sequences/baserunner.pt'
        
        # Create agent with Noesis
        self.agent = create_agent(use_noesis=use_noesis)
        
        # MLB data cache
        self.game_data = []
        self.pitcher_cache = {}
        
        # Load data
        self._load_data()
        
        print(f"[Bridge] Initialized with {len(self.game_data)} game records")
    
    def _load_data(self):
        """Load MLB data from CSV."""
        if not os.path.exists(self.data_csv):
            print(f"[Bridge] Warning: Data file not found: {self.data_csv}")
            return
        
        with open(self.data_csv, 'r') as f:
            reader = csv.DictReader(f)
            self.game_data = list(reader)
        
        # Build pitcher cache
        for row in self.game_data:
            pitcher_id = row.get('pitcher_id')
            if pitcher_id not in self.pitcher_cache:
                self.pitcher_cache[pitcher_id] = {
                    'name': row.get('pitcher_name'),
                    'era': row.get('pitcher_era'),
                    'whip': row.get('pitcher_whip'),
                    'k9': row.get('pitcher_k9'),
                    'bb9': row.get('pitcher_bb9'),
                    'kbb': row.get('pitcher_kbb'),
                    'wins': row.get('pitcher_wins'),
                    'losses': row.get('pitcher_losses'),
                    'ip': row.get('pitcher_ip'),
                    'games': [],
                }
            self.pitcher_cache[pitcher_id]['games'].append(row)
        
        print(f"[Bridge] Loaded {len(self.pitcher_cache)} unique pitchers")
    
    def perceive_mlb_data(self, pitcher_name=None, pitcher_id=None, limit=10) -> List[Dict]:
        """
        PERCEIVE: Read and filter MLB data.
        
        Args:
            pitcher_name: Filter by pitcher name
            pitcher_id: Filter by pitcher ID
            limit: Max records to return
        
        Returns:
            List of matching game records
        """
        results = self.game_data
        
        if pitcher_name:
            results = [r for r in results if pitcher_name.lower() in r.get('pitcher_name', '').lower()]
        if pitcher_id:
            results = [r for r in results if r.get('pitcher_id') == pitcher_id]
        
        return results[:limit]
    
    def intuit_with_noesis(self, pitcher_data: Dict) -> Dict[str, Any]:
        """
        INTUIT: Use Noesis (nanoGPT) to generate probabilistic intuition.
        
        Args:
            pitcher_data: Pitcher stats
        
        Returns:
            Noesis intuition result
        """
        return self.agent.analyze_with_noesis(pitcher_data)
    
    def decide_with_curiosity(self, pitcher_data: Dict, noesis_intuition: str = None) -> Dict[str, Any]:
        """
        DECIDE: Use curiosity engine logic to decide on prediction strategy.
        
        Args:
            pitcher_data: Pitcher stats
            noesis_intuition: Optional Noesis output to inform decision
        
        Returns:
            Decision with confidence and reasoning
        """
        pitcher_name = pitcher_data.get('pitcher_name', pitcher_data.get('name', 'Unknown'))
        predicted_f5 = float(pitcher_data.get('predicted_f5', pitcher_data.get('predicted', 2.5)))
        opp_avg = float(pitcher_data.get('opp_avg_first5_allowed', 2.5))
        era = float(pitcher_data.get('pitcher_era', 4.0))
        
        # Calculate edge
        edge = predicted_f5 - opp_avg
        
        # Curiosity: flag interesting cases
        curiosity_flags = []
        
        if abs(edge) > 2.0:
            curiosity_flags.append("LARGE_EDGE")
        if era < 3.0:
            curiosity_flags.append("ELITE_PITCHER")
        if predicted_f5 < 1.5:
            curiosity_flags.append("LOW_PREDICTION")
        if predicted_f5 > 3.5:
            curiosity_flags.append("HIGH_PREDICTION")
        
        # Decision logic
        if edge < -1.5:
            decision = "UNDER"
            confidence = min(0.95, 0.7 + abs(edge) * 0.1)
            reasoning = f"Pitcher likely to outperform - edge of {edge:.2f} vs opponent average"
        elif edge > 1.5:
            decision = "OVER"
            confidence = min(0.95, 0.7 + edge * 0.1)
            reasoning = f"Elevated risk - edge of {edge:.2f} vs opponent average"
        else:
            decision = "NEUTRAL"
            confidence = 0.55
            reasoning = "No significant edge detected, playing it safe"
        
        # Incorporate Noesis intuition if available
        if noesis_intuition:
            reasoning = f"{reasoning}. Noesis intuition: {noesis_intuition[:100]}..."
        
        return {
            'pitcher': pitcher_name,
            'decision': decision,
            'confidence': confidence,
            'predicted_f5': predicted_f5,
            'edge': edge,
            'reasoning': reasoning,
            'curiosity_flags': curiosity_flags,
            'curiosity_level': len(curiosity_flags),
        }
    
    def execute_prediction(self, decision: Dict) -> Dict[str, Any]:
        """
        EXECUTE: Run prediction based on decision.
        
        Args:
            decision: Decision from decide_with_curiosity
        
        Returns:
            Execution result with final prediction
        """
        predicted = decision['predicted_f5']
        confidence = decision['confidence']
        decision_type = decision['decision']
        
        # Set thresholds based on decision type
        if decision_type == "UNDER":
            threshold = predicted - 0.3
            expected_value = max(0, threshold - predicted)
        elif decision_type == "OVER":
            threshold = predicted + 0.3
            expected_value = max(0, predicted - threshold)
        else:
            threshold = predicted
            expected_value = 0.1
        
        return {
            'prediction': f"{decision_type} {threshold:.2f}",
            'confidence': confidence,
            'expected_value': expected_value,
            'threshold': threshold,
            'recommended_action': decision_type,
        }
    
    def evolve_from_outcome(self, prediction: Dict, actual_result: float) -> Dict[str, Any]:
        """
        EVOLVE: Learn from prediction outcome.
        
        Args:
            prediction: The prediction we made
            actual_result: Actual first-5 runs allowed
        
        Returns:
            Learning result
        """
        threshold = prediction.get('threshold', 2.5)
        correct = (actual_result < threshold and prediction['recommended_action'] == 'UNDER') or \
                  (actual_result > threshold and prediction['recommended_action'] == 'OVER')
        
        learning = {
            'was_correct': correct,
            'actual_result': actual_result,
            'predicted_threshold': threshold,
            'error': abs(actual_result - threshold),
            'lesson': None,
        }
        
        if correct:
            learning['lesson'] = f"Correct! Prediction of {prediction['recommended_action']} at {threshold:.2f} was right (actual: {actual_result})"
        else:
            learning['lesson'] = f"Incorrect. Actual {actual_result} vs threshold {threshold:.2f} for {prediction['recommended_action']}"
        
        return learning
    
    def full_cycle(self, pitcher_name: str, use_noesis: bool = True) -> Dict[str, Any]:
        """
        Run the full PERCEIVE → INTUIT → DECIDE → EXECUTE cycle.
        
        Args:
            pitcher_name: Name of pitcher to analyze
        
        Returns:
            Complete analysis result
        """
        print(f"\n{'='*60}")
        print(f"[CYCLE] Analyzing: {pitcher_name}")
        print(f"{'='*60}")
        
        # 1. PERCEIVE
        print("\n[1/4] PERCEIVE: Reading MLB data...")
        games = self.perceive_mlb_data(pitcher_name=pitcher_name, limit=5)
        if not games:
            return {'error': f'No data found for pitcher: {pitcher_name}'}
        
        # Use most recent game data
        pitcher_data = games[0]
        print(f"  Found {len(games)} recent games")
        print(f"  ERA: {pitcher_data.get('pitcher_era')}, Predicted: {pitcher_data.get('predicted_f5')}")
        
        # 2. INTUIT (optional)
        noesis_intuition = None
        if use_noesis and self.agent.noesis:
            print("\n[2/4] INTUIT: Querying Noesis (nanoGPT)...")
            noesis_result = self.intuit_with_noesis(pitcher_data)
            noesis_intuition = noesis_result.get('noesis_intuition', '')
            print(f"  Intuition: {noesis_intuition[:150]}...")
        else:
            print("\n[2/4] INTUIT: Skipped (Noesis not available)")
        
        # 3. DECIDE
        print("\n[3/4] DECIDE: Applying curiosity engine...")
        decision = self.decide_with_curiosity(pitcher_data, noesis_intuition)
        print(f"  Decision: {decision['decision']}")
        print(f"  Confidence: {decision['confidence']:.2%}")
        print(f"  Reasoning: {decision['reasoning'][:100]}...")
        if decision['curiosity_flags']:
            print(f"  Curiosity flags: {decision['curiosity_flags']}")
        
        # 4. EXECUTE
        print("\n[4/4] EXECUTE: Generating prediction...")
        execution = self.execute_prediction(decision)
        print(f"  Prediction: {execution['prediction']}")
        print(f"  Expected value: {execution['expected_value']:.3f}")
        
        return {
            'pitcher': pitcher_name,
            'perceived_games': len(games),
            'pitcher_data': pitcher_data,
            'noesis_intuition': noesis_intuition,
            'decision': decision,
            'execution': execution,
            'timestamp': datetime.now().isoformat(),
        }
    
    def run_whatif(self, scenario: str) -> str:
        """
        Run a what-if scenario through Noesis.
        
        Args:
            scenario: What-if scenario description
        
        Returns:
            Generated scenario analysis
        """
        if not self.agent.noesis:
            return "[Noesis not available]"
        
        return self.agent.what_if_scenario(scenario)
    
    def batch_analysis(self, pitcher_names: List[str], use_noesis: bool = True) -> List[Dict]:
        """
        Run analysis on multiple pitchers.
        
        Args:
            pitcher_names: List of pitcher names
            use_noesis: Whether to use Noesis
        
        Returns:
            List of analysis results
        """
        results = []
        for name in pitcher_names:
            result = self.full_cycle(name, use_noesis=use_noesis)
            results.append(result)
        return results


def main():
    parser = argparse.ArgumentParser(description='Wrong Room Bridge - MLB Agent')
    parser.add_argument('--pitcher', '-p', type=str, help='Pitcher name to analyze')
    parser.add_argument('--whatif', '-w', type=str, help='What-if scenario')
    parser.add_argument('--batch', '-b', action='store_true', help='Run batch analysis')
    parser.add_argument('--no-noesis', action='store_true', help='Disable Noesis')
    args = parser.parse_args()
    
    bridge = WrongRoomBridge(use_noesis=not args.no_noesis)
    
    if args.whatif:
        print("\n=== WHAT-IF SCENARIO ===")
        print(f"Scenario: {args.whatif}")
        result = bridge.run_whatif(args.whatif)
        print(f"\nAnalysis:\n{result}")
        return
    
    if args.pitcher:
        result = bridge.full_cycle(args.pitcher, use_noesis=not args.no_noesis)
        print(f"\nFinal Result:")
        print(json.dumps(result, indent=2, default=str))
        return
    
    if args.batch:
        # Sample pitchers for batch analysis
        pitchers = ['Gerrit Cole', 'Shane Bieber', 'Luis Castillo', 'Clayton Kershaw', 'Aaron Nola']
        results = bridge.batch_analysis(pitchers, use_noesis=not args.no_noesis)
        print(f"\nBatch Analysis Complete: {len(results)} pitchers analyzed")
        for r in results:
            print(f"  {r['pitcher']}: {r['execution']['prediction']} (conf: {r['decision']['confidence']:.2%})")
        return
    
    # Default: run a sample analysis
    print("=== Wrong Room Collective - MLB Bridge ===")
    print("Run with --pitcher <name> or --whatif <scenario>")
    
    result = bridge.full_cycle("Gerrit Cole", use_noesis=not args.no_noesis)
    print(f"\nSample Analysis:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
