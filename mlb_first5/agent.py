#!/usr/bin/env python3
"""
agent.py - Wrong Room Collective Agent with Noesis (nanoGPT) intuition integration.
Provides probabilistic insights for baseball first-5 predictions.
"""
import os
import sys
import json
from typing import Optional, Dict, Any, List

# Try to import noesis engine
try:
    sys.path.insert(0, '/root/mlb-first5/noesis')
    from noesis_engine import NoesisEngine, load_noesis
    NOESIS_AVAILABLE = True
except ImportError:
    NOESIS_AVAILABLE = False
    print("Warning: Noesis engine not available")

class WrongRoomAgent:
    """
    Wrong Room Collective Agent for MLB first-5 predictions.
    
    Integrates:
    - Noesis (nanoGPT intuition module) for probabilistic insights
    - Curiosity Engine for exploring interesting patterns
    - Meta-Evolver for self-improvement
    - Memory for persistent context
    """
    
    def __init__(self, name="Claw", use_noesis=True, noesis_checkpoint_dir=None):
        self.name = name
        self.use_noesis = use_noesis and NOESIS_AVAILABLE
        self.noesis = None
        self.conversation_history = []
        self.memory = {
            'insights': [],
            'predictions': [],
            'anomalies': [],
        }
        
        # Initialize Noesis if available
        if self.use_noesis:
            self._init_noesis(noesis_checkpoint_dir)
        
        print(f"[{self.name}] Wrong Room Collective Agent initialized")
        if self.noesis:
            print(f"[{self.name}] Noesis intuition module: ACTIVE")
        else:
            print(f"[{self.name}] Noesis intuition module: INACTIVE (no checkpoint)")
    
    def _init_noesis(self, checkpoint_dir=None):
        """Initialize the Noesis intuition engine."""
        try:
            self.noesis = NoesisEngine(checkpoint_dir=checkpoint_dir)
            if self.noesis.is_ready():
                print(f"[{self.name}] Noesis loaded successfully")
            else:
                print(f"[{self.name}] Noesis checkpoint not found - intuition disabled")
                self.noesis = None
        except Exception as e:
            print(f"[{self.name}] Failed to load Noesis: {e}")
            self.noesis = None
    
    def noesis_call(self, prompt: str, max_tokens: int = 100) -> str:
        """
        Query Noesis (nanoGPT) for probabilistic intuition.
        
        This is the "intuition step" before rational analysis.
        The model generates text based on its training on baseball corpus,
        providing probabilistic insights about matchups.
        
        Args:
            prompt: The question or context to ask Noesis about
        
        Returns:
            Generated intuition string
        """
        if not self.noesis:
            return "[Noesis not available - train model first]"
        
        try:
            result = self.noesis.generate(prompt, max_new_tokens=max_tokens, temperature=0.7)
            return result
        except Exception as e:
            return f"[Noesis error: {e}]"
    
    def ask_noesis(self, pitcher: str, opponent: str = None, question: str = None) -> Dict[str, Any]:
        """
        Ask Noesis about a specific pitcher matchup.
        
        Args:
            pitcher: Pitcher name
            opponent: Opponent team (optional)
            question: Specific question (optional)
        
        Returns:
            Dict with 'prompt', 'intuition', 'insight_type'
        """
        # Build prompt
        prompt = f"Analysis of {pitcher}"
        if opponent:
            prompt += f" vs {opponent}"
        prompt += " in first 5 innings:\nIntuition:"
        
        intuition = self.noesis_call(prompt, max_tokens=150)
        
        # Store in memory
        insight = {
            'type': 'noesis_intuition',
            'pitcher': pitcher,
            'opponent': opponent,
            'intuition': intuition,
        }
        self.memory['insights'].append(insight)
        
        return {
            'prompt': prompt,
            'intuition': intuition,
            'insight_type': 'probabilistic_intuition',
        }
    
    def analyze_with_noesis(self, pitcher_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze pitcher data using Noesis intuition.
        
        Args:
            pitcher_data: Dict with pitcher stats (name, era, whip, k9, etc.)
        
        Returns:
            Analysis result with intuition and structured insights
        """
        pitcher_name = pitcher_data.get('name', pitcher_data.get('pitcher_name', 'Unknown'))
        era = pitcher_data.get('era', pitcher_data.get('pitcher_era', '?'))
        whip = pitcher_data.get('whip', pitcher_data.get('pitcher_whip', '?'))
        k9 = pitcher_data.get('k9', pitcher_data.get('pitcher_k9', '?'))
        predicted = pitcher_data.get('predicted_f5', pitcher_data.get('predicted', '?'))
        
        # Ask noesis for intuition
        prompt = f"{pitcher_name}: ERA={era}, WHIP={whip}, K/9={k9}. Predicted First5={predicted}.\nIntuition:"
        intuition = self.noesis_call(prompt, max_tokens=100)
        
        # Extract potential insights from intuition text
        insights = {
            'pitcher': pitcher_name,
            'era': era,
            'predicted': predicted,
            'noesis_intuition': intuition,
            'analysis_type': 'noesis_augmented',
        }
        
        # Store prediction
        self.memory['predictions'].append(insights)
        
        return insights
    
    def what_if_scenario(self, scenario: str) -> str:
        """
        Generate a "what-if" scenario analysis using Noesis.
        
        Args:
            scenario: What-if scenario description
        
        Returns:
            Generated scenario analysis
        """
        prompt = f"What-if scenario: {scenario}\nAnalysis:"
        return self.noesis_call(prompt, max_tokens=200)
    
    def detect_anomaly(self, pitcher_data: Dict) -> Dict[str, Any]:
        """
        Flag unusual first-5 patterns for a pitcher.
        
        Args:
            pitcher_data: Pitcher stats
        
        Returns:
            Anomaly detection result
        """
        pitcher_name = pitcher_data.get('name', 'Unknown')
        predicted = pitcher_data.get('predicted_f5', 2.5)
        opp_avg = pitcher_data.get('opp_avg_first5_allowed', 2.5)
        
        # Simple heuristic for now
        edge = float(predicted) - float(opp_avg)
        is_anomaly = abs(edge) > 2.0
        
        result = {
            'pitcher': pitcher_name,
            'predicted': predicted,
            'opponent_avg': opp_avg,
            'edge': edge,
            'is_anomaly': is_anomaly,
            'message': f"Unusual edge detected: {edge:.2f}" if is_anomaly else "Within normal range"
        }
        
        if is_anomaly:
            self.memory['anomalies'].append(result)
        
        return result
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of agent memory."""
        return {
            'total_insights': len(self.memory['insights']),
            'total_predictions': len(self.memory['predictions']),
            'total_anomalies': len(self.memory['anomalies']),
            'recent_insights': self.memory['insights'][-5:] if self.memory['insights'] else [],
        }
    
    def think(self, context: str) -> str:
        """
        Agent thinking/reasoning step.
        
        Args:
            context: Current context or question
        
        Returns:
            Reasoning output
        """
        return f"[{self.name}] Processing: {context}"


def create_agent(use_noesis=True, noesis_checkpoint_dir=None) -> WrongRoomAgent:
    """Factory function to create a Wrong Room agent."""
    return WrongRoomAgent(use_noesis=use_noesis, noesis_checkpoint_dir=noesis_checkpoint_dir)


if __name__ == '__main__':
    print("=== Wrong Room Collective Agent Test ===\n")
    
    # Create agent with Noesis
    agent = create_agent(use_noesis=True)
    
    print(f"\nNoesis available: {agent.noesis is not None}")
    
    if agent.noesis:
        print("\n--- Test: Ask Noesis about a pitcher ---")
        result = agent.ask_noesis("Gerrit Cole", opponent="Yankees")
        print(f"Prompt: {result['prompt']}")
        print(f"Intuition: {result['intuition']}")
        
        print("\n--- Test: What-if scenario ---")
        print(agent.what_if_scenario("What if Gerrit Cole faces a weak lineup after 5 days rest?"))
        
        print("\n--- Test: Analyze pitcher data ---")
        sample_data = {
            'name': 'Shane Bieber',
            'era': 3.18,
            'whip': 1.22,
            'k9': 12.5,
            'predicted_f5': 1.32,
        }
        analysis = agent.analyze_with_noesis(sample_data)
        print(f"Analysis: {analysis}")
    
    print("\n--- Test: Anomaly detection ---")
    anomaly = agent.detect_anomaly({
        'name': 'Luis Castillo',
        'predicted_f5': 3.27,
        'opp_avg_first5_allowed': 6.0,
    })
    print(f"Anomaly: {anomaly}")
    
    print("\n--- Memory summary ---")
    print(agent.get_memory_summary())
