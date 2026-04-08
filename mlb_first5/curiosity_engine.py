#!/usr/bin/env python3
"""
curiosity_engine.py
Curiosity Engine for the Wrong Room Collective agent framework.

Flags interesting/unusual patterns in MLB first-5 data for deeper investigation.
Based on curiosity-driven exploration principles.
"""
from typing import Dict, Any, List, Optional
from collections import defaultdict


class CuriosityEngine:
    """
    Curiosity-driven exploration for MLB predictions.
    
    Flags patterns that warrant deeper investigation:
    - Anomalous edges (large deviations from opponent averages)
    - Elite pitchers (ERA < 3.0)
    - Hot/cold streaks
    - Unusual stat combinations
    - High curiosity scenarios
    """
    
    def __init__(self, threshold_large_edge: float = 2.0, threshold_elite_era: float = 3.0):
        self.threshold_large_edge = threshold_large_edge
        self.threshold_elite_era = threshold_elite_era
        self.flags_history = []
    
    def evaluate(self, pitcher_data: Dict[str, Any], noesis_intuition: str = None) -> Dict[str, Any]:
        """
        Evaluate a pitcher/game for curiosity flags.
        
        Args:
            pitcher_data: Dict with pitcher stats and predictions
            noesis_intuition: Optional Noesis output to incorporate
        
        Returns:
            Curiosity evaluation with flags and scores
        """
        flags = []
        scores = {}
        
        pitcher_name = pitcher_data.get('pitcher_name', pitcher_data.get('name', 'Unknown'))
        era = float(pitcher_data.get('pitcher_era', 4.0))
        predicted = float(pitcher_data.get('predicted_f5', 2.5))
        opp_avg = float(pitcher_data.get('opp_avg_first5_allowed', 2.5))
        whip = float(pitcher_data.get('pitcher_whip', 1.3))
        k9 = float(pitcher_data.get('pitcher_k9', 8.0))
        bb9 = float(pitcher_data.get('pitcher_bb9', 3.0))
        kbb = float(pitcher_data.get('pitcher_kbb', 2.5))
        days_rest = pitcher_data.get('pitcher_days_rest', None)
        
        # 1. Large edge flag
        edge = predicted - opp_avg
        if abs(edge) > self.threshold_large_edge:
            flags.append(f"LARGE_EDGE({edge:.2f})")
            scores['edge_curiosity'] = min(1.0, abs(edge) / 4.0)
        else:
            scores['edge_curiosity'] = abs(edge) / 4.0
        
        # 2. Elite pitcher flag
        if era < self.threshold_elite_era:
            flags.append(f"ELITE_PITCHER(ERA={era:.2f})")
            scores['elite_curiosity'] = (self.threshold_elite_era - era) / 2.0
        else:
            scores['elite_curiosity'] = 0.0
        
        # 3. High K/BB ratio
        if kbb > 4.0:
            flags.append(f"HIGH_KBB({kbb:.2f})")
            scores['kbb_curiosity'] = min(1.0, (kbb - 4.0) / 2.0)
        else:
            scores['kbb_curiosity'] = 0.0
        
        # 4. Low prediction
        if predicted < 1.5:
            flags.append(f"LOW_PREDICTION({predicted:.2f})")
            scores['prediction_curiosity'] = (1.5 - predicted) / 1.5
        
        # 5. High prediction
        if predicted > 3.5:
            flags.append(f"HIGH_PREDICTION({predicted:.2f})")
            scores['prediction_curiosity'] = (predicted - 3.5) / 2.0
        
        # 6. Rest factor
        if days_rest:
            rest = float(days_rest)
            if rest > 5:
                flags.append(f"WELL_RESTED({rest}d)")
                scores['rest_curiosity'] = min(1.0, (rest - 5) / 3.0)
            elif rest < 3:
                flags.append(f"SHORT_REST({rest}d)")
                scores['rest_curiosity'] = min(1.0, (3 - rest) / 3.0)
        
        # 7. Unusual stat combo
        if era < 3.5 and whip > 1.3:
            flags.append("ERA_WHIP_DIVERGENCE")
            scores['stat_combo_curiosity'] = 0.7
        elif k9 > 11 and bb9 < 2.0:
            flags.append("DOMINANT_K_BB")
            scores['stat_combo_curiosity'] = 0.8
        
        # Calculate total curiosity score
        total_score = sum(scores.values()) / len(scores) if scores else 0.0
        curiosity_level = "LOW"
        if total_score > 0.6:
            curiosity_level = "HIGH"
        elif total_score > 0.3:
            curiosity_level = "MEDIUM"
        
        # Incorporate Noesis if available
        noesis_signal = None
        if noesis_intuition:
            # Simple heuristic: look for outcome keywords
            text_lower = noesis_intuition.lower()
            if any(w in text_lower for w in ['high', 'over', 'score', 'runs']):
                noesis_signal = "BULLISH_OVER"
            elif any(w in text_lower for w in ['low', 'under', 'shutout', 'dominate']):
                noesis_signal = "BEARISH_UNDER"
            else:
                noesis_signal = "NEUTRAL"
        
        result = {
            'pitcher': pitcher_name,
            'flags': flags,
            'scores': scores,
            'curiosity_score': total_score,
            'curiosity_level': curiosity_level,
            'edge': edge,
            'noesis_signal': noesis_signal,
            'recommended_action': self._decide_action(predicted, edge, total_score),
        }
        
        self.flags_history.append(result)
        return result
    
    def _decide_action(self, predicted, edge, curiosity_score):
        """Decide action based on curiosity evaluation."""
        if edge < -1.5 and curiosity_score > 0.3:
            return "UNDER"
        elif edge > 1.5 and curiosity_score > 0.3:
            return "OVER"
        elif curiosity_score < 0.2:
            return "PASS"  # Not interesting enough
        else:
            return "FLAT"  # Within normal range
    
    def get_top_curious(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most curious pitcher evaluations from history."""
        sorted_history = sorted(
            self.flags_history,
            key=lambda x: x['curiosity_score'],
            reverse=True
        )
        return sorted_history[:limit]
    
    def reset(self):
        """Clear history."""
        self.flags_history = []


def create_curiosity_engine() -> CuriosityEngine:
    """Factory function."""
    return CuriosityEngine()


if __name__ == '__main__':
    print("=== Curiosity Engine Test ===")
    
    engine = CuriosityEngine()
    
    test_pitchers = [
        {
            'pitcher_name': 'Gerrit Cole',
            'era': 3.23,
            'whip': 1.06,
            'k9': 12.1,
            'bb9': 2.0,
            'kbb': 5.9,
            'predicted_f5': 1.35,
            'opp_avg_first5_allowed': 1.02,
            'pitcher_days_rest': 5,
        },
        {
            'pitcher_name': 'Luis Castillo',
            'era': 3.99,
            'whip': 1.37,
            'k9': 9.2,
            'bb9': 3.6,
            'kbb': 2.6,
            'predicted_f5': 3.27,
            'opp_avg_first5_allowed': 10.49,
            'pitcher_days_rest': 4,
        },
        {
            'pitcher_name': 'Clayton Kershaw',
            'era': 3.56,
            'whip': 1.02,
            'k9': 10.7,
            'bb9': 1.6,
            'kbb': 6.9,
            'predicted_f5': 1.68,
            'opp_avg_first5_allowed': 5.01,
            'pitcher_days_rest': 6,
        },
    ]
    
    for p in test_pitchers:
        result = engine.evaluate(p)
        print(f"\n{result['pitcher']}:")
        print(f"  Curiosity Level: {result['curiosity_level']} ({result['curiosity_score']:.3f})")
        print(f"  Flags: {result['flags']}")
        print(f"  Edge: {result['edge']:.2f}")
        print(f"  Action: {result['recommended_action']}")
    
    print("\n\nTop Curious:")
    for item in engine.get_top_curious():
        print(f"  {item['pitcher']}: {item['curiosity_level']} ({item['curiosity_score']:.3f})")
