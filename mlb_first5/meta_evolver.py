#!/usr/bin/env python3
"""
meta_evolver.py
Meta-Evolver for the Wrong Room Collective agent framework.

Learns from prediction outcomes and evolves the agent's strategy over time.
"""
import json
import os
from typing import Dict, Any, List, Optional
from collections import defaultdict
from datetime import datetime


class MetaEvolver:
    """
    Meta-Evolver: Self-improvement through experience.
    
    Tracks prediction outcomes and evolves strategy:
    - Learn from correct predictions
    - Learn from mistakes
    - Adjust confidence based on track record
    - Evolve curiosity thresholds
    """
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or '/root/mlb-first5/data/sequences'
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.history = []
        self.pitcher_records = defaultdict(lambda: {
            'total': 0,
            'correct': 0,
            'under_correct': 0,
            'over_correct': 0,
            'flat_correct': 0,
        })
        
        self.era_records = defaultdict(lambda: {'total': 0, 'correct': 0})
        self.edge_records = defaultdict(lambda: {'total': 0, 'correct': 0})
        
        # Strategy parameters (evolvable)
        self.params = {
            'under_threshold': -1.5,
            'over_threshold': 1.5,
            'confidence_boost': 0.05,
            'elite_era_threshold': 3.0,
            'curiosity_weight': 0.3,
        }
        
        self.evolution_log = []
        
        # Load existing history if available
        self._load_history()
    
    def record_outcome(self, prediction: Dict[str, Any], actual_result: float) -> Dict[str, Any]:
        """
        Record a prediction outcome and learn from it.
        
        Args:
            prediction: Dict with 'predicted', 'threshold', 'recommended_action', 'pitcher', etc.
            actual_result: Actual first-5 runs allowed
        
        Returns:
            Learning result
        """
        threshold = prediction.get('threshold', 2.5)
        action = prediction.get('recommended_action', 'FLAT')
        pitcher = prediction.get('pitcher', 'Unknown')
        predicted = prediction.get('predicted_f5', prediction.get('predicted', threshold))
        
        # Determine if correct
        if action == 'UNDER':
            correct = actual_result < threshold
        elif action == 'OVER':
            correct = actual_result > threshold
        else:  # FLAT or PASS
            # For flat, we're right if it's close
            correct = abs(actual_result - predicted) < 0.5
        
        # Record
        outcome = {
            'timestamp': datetime.now().isoformat(),
            'pitcher': pitcher,
            'predicted': predicted,
            'threshold': threshold,
            'action': action,
            'actual': actual_result,
            'correct': correct,
            'error': abs(actual_result - threshold),
            'params': dict(self.params),
        }
        
        self.history.append(outcome)
        
        # Update pitcher record
        p_record = self.pitcher_records[pitcher]
        p_record['total'] += 1
        if correct:
            p_record['correct'] += 1
            if action == 'UNDER':
                p_record['under_correct'] += 1
            elif action == 'OVER':
                p_record['over_correct'] += 1
            else:
                p_record['flat_correct'] += 1
        
        # Update edge bucket record
        edge = predicted - threshold
        edge_bucket = 'MEDIUM'
        if abs(edge) < 1.0:
            edge_bucket = 'SMALL'
        elif abs(edge) > 2.0:
            edge_bucket = 'LARGE'
        
        self.era_records[edge_bucket]['total'] += 1
        if correct:
            self.era_records[edge_bucket]['correct'] += 1
        
        # Learn and evolve
        self._evolve()
        
        # Save
        self._save_history()
        
        return outcome
    
    def _evolve(self):
        """Evolve strategy based on recent history."""
        recent = self.history[-20:]  # Last 20 predictions
        
        if len(recent) < 5:
            return
        
        # Calculate accuracy by action type
        under_preds = [h for h in recent if h['action'] == 'UNDER']
        over_preds = [h for h in recent if h['action'] == 'OVER']
        flat_preds = [h for h in recent if h['action'] == 'FLAT']
        
        under_acc = sum(1 for h in under_preds if h['correct']) / len(under_preds) if under_preds else 0.5
        over_acc = sum(1 for h in over_preds if h['correct']) / len(over_preds) if over_preds else 0.5
        flat_acc = sum(1 for h in flat_preds if h['correct']) / len(flat_preds) if flat_preds else 0.5
        
        evolution_entry = {
            'timestamp': datetime.now().isoformat(),
            'under_acc': under_acc,
            'over_acc': over_acc,
            'flat_acc': flat_acc,
            'total_predictions': len(self.history),
        }
        
        # Adjust thresholds based on accuracy
        if under_acc > 0.6:
            # UNDER is working well - be more aggressive
            self.params['under_threshold'] = max(-2.5, self.params['under_threshold'] - 0.1)
            evolution_entry['change'] = 'UNDER threshold decreased'
        elif under_acc < 0.4:
            # UNDER is failing - be less aggressive
            self.params['under_threshold'] = min(-0.5, self.params['under_threshold'] + 0.1)
            evolution_entry['change'] = 'UNDER threshold increased'
        
        if over_acc > 0.6:
            self.params['over_threshold'] = min(2.5, self.params['over_threshold'] + 0.1)
            evolution_entry['change'] = 'OVER threshold increased'
        elif over_acc < 0.4:
            self.params['over_threshold'] = max(0.5, self.params['over_threshold'] - 0.1)
            evolution_entry['change'] = 'OVER threshold decreased'
        
        # Adjust confidence boost
        overall_acc = sum(1 for h in recent if h['correct']) / len(recent)
        if overall_acc > 0.55:
            self.params['confidence_boost'] = min(0.15, self.params['confidence_boost'] + 0.01)
        else:
            self.params['confidence_boost'] = max(0.01, self.params['confidence_boost'] - 0.01)
        
        self.evolution_log.append(evolution_entry)
    
    def get_adjusted_confidence(self, base_confidence: float, pitcher: str = None) -> float:
        """
        Adjust confidence based on track record.
        
        Args:
            base_confidence: Base confidence from prediction
            pitcher: Optional pitcher name for pitcher-specific adjustment
        
        Returns:
            Adjusted confidence
        """
        boost = self.params['confidence_boost']
        
        # Pitcher-specific adjustment
        if pitcher:
            p_record = self.pitcher_records.get(pitcher)
            if p_record and p_record['total'] >= 3:
                pitcher_acc = p_record['correct'] / p_record['total']
                if pitcher_acc > 0.6:
                    boost *= 1.5
                elif pitcher_acc < 0.4:
                    boost *= 0.5
        
        # Overall track record adjustment
        recent = self.history[-50:]
        if len(recent) >= 10:
            recent_acc = sum(1 for h in recent if h['correct']) / len(recent)
            boost *= (0.5 + recent_acc)
        
        return min(0.95, base_confidence + boost)
    
    def get_pitcher_accuracy(self, pitcher: str) -> Dict[str, float]:
        """Get accuracy stats for a specific pitcher."""
        record = self.pitcher_records.get(pitcher, {'total': 0, 'correct': 0})
        if record['total'] == 0:
            return {'total': 0, 'accuracy': None}
        return {
            'total': record['total'],
            'correct': record['correct'],
            'accuracy': record['correct'] / record['total'],
            'under_accuracy': record['under_correct'] / max(1, record['total']),
            'over_accuracy': record['over_correct'] / max(1, record['total']),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall evolution stats."""
        if not self.history:
            return {
                'total_predictions': 0,
                'overall_accuracy': None,
                'params': self.params,
            }
        
        recent = self.history[-50:]
        recent_acc = sum(1 for h in recent if h['correct']) / len(recent)
        overall_acc = sum(1 for h in self.history if h['correct']) / len(self.history)
        
        return {
            'total_predictions': len(self.history),
            'overall_accuracy': overall_acc,
            'recent_accuracy': recent_acc,
            'recent_sample_size': len(recent),
            'params': self.params,
            'unique_pitchers': len(self.pitcher_records),
            'evolution_steps': len(self.evolution_log),
        }
    
    def _save_history(self):
        """Save history to disk."""
        path = os.path.join(self.data_dir, 'evolution_history.json')
        with open(path, 'w') as f:
            json.dump({
                'history': self.history,
                'params': self.params,
                'pitcher_records': dict(self.pitcher_records),
            }, f, indent=2)
    
    def _load_history(self):
        """Load history from disk."""
        path = os.path.join(self.data_dir, 'evolution_history.json')
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                self.history = data.get('history', [])
                self.params = data.get('params', self.params)
                self.pitcher_records = defaultdict(
                    lambda: {'total': 0, 'correct': 0, 'under_correct': 0, 'over_correct': 0, 'flat_correct': 0},
                    data.get('pitcher_records', {})
                )
            except Exception as e:
                print(f"Failed to load history: {e}")
    
    def reset(self):
        """Reset all learning."""
        self.history = []
        self.pitcher_records = defaultdict(lambda: {
            'total': 0, 'correct': 0, 'under_correct': 0, 'over_correct': 0, 'flat_correct': 0
        })
        self.evolution_log = []
        self.params = {
            'under_threshold': -1.5,
            'over_threshold': 1.5,
            'confidence_boost': 0.05,
            'elite_era_threshold': 3.0,
            'curiosity_weight': 0.3,
        }


def create_meta_evolver(data_dir: str = None) -> MetaEvolver:
    """Factory function."""
    return MetaEvolver(data_dir=data_dir)


if __name__ == '__main__':
    print("=== Meta-Evolver Test ===")
    
    evolver = MetaEvolver()
    
    # Simulate some predictions
    test_cases = [
        {'pitcher': 'Gerrit Cole', 'predicted_f5': 1.35, 'threshold': 1.5, 'recommended_action': 'UNDER'},
        {'pitcher': 'Shane Bieber', 'predicted_f5': 1.32, 'threshold': 1.5, 'recommended_action': 'UNDER'},
        {'pitcher': 'Luis Castillo', 'predicted_f5': 3.27, 'threshold': 3.5, 'recommended_action': 'OVER'},
        {'pitcher': 'Clayton Kershaw', 'predicted_f5': 1.68, 'threshold': 1.5, 'recommended_action': 'UNDER'},
    ]
    
    actuals = [1, 3, 2, 2]  # 1=under, 3=over, 2=under, 2=flat-ish
    
    for pred, actual in zip(test_cases, actuals):
        outcome = evolver.record_outcome(pred, actual)
        print(f"{pred['pitcher']}: {'✓' if outcome['correct'] else '✗'} actual={actual}, pred={pred['recommended_action']}")
    
    print(f"\nStats: {evolver.get_stats()}")
    print(f"Params: {evolver.params}")
    
    # Test confidence adjustment
    print(f"\nAdjusted confidence for Gerrit Cole: {evolver.get_adjusted_confidence(0.7, 'Gerrit Cole'):.3f}")
    print(f"Adjusted confidence (unknown pitcher): {evolver.get_adjusted_confidence(0.7):.3f}")
