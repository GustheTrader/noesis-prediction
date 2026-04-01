"""
Meta-Evolver — Agent that evolves its own strategies.

Reality OS Principle: The accountability loop.
Observe → learn → adapt → evolve.
The agent doesn't just solve problems — it evolves HOW it solves problems.
"""

import random
import json
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Strategy:
    """A strategy the agent can use."""
    name: str
    prompt_template: str
    approach: str  # "explore" | "exploit" | "meta"
    fitness: float = 0.5  # How well this strategy performs
    uses: int = 0
    successes: int = 0
    mutations: list = field(default_factory=list)


class MetaEvolver:
    """
    Evolves the agent's own strategies over time.
    
    This is meta-cognition in silicon:
    - Not just "what should I do?"
    - But "how should I decide what to do?"
    """

    def __init__(self):
        self.strategies: list[Strategy] = [
            Strategy(
                name="direct_answer",
                prompt_template="Answer directly: {query}",
                approach="exploit",
            ),
            Strategy(
                name="deep_research",
                prompt_template="Research deeply and explore multiple angles before answering: {query}",
                approach="explore",
            ),
            Strategy(
                name="first_principles",
                prompt_template="Break down to first principles and reason from scratch: {query}",
                approach="meta",
            ),
            Strategy(
                name="wrong_room",
                prompt_template="Find the most challenging interpretation and address that: {query}",
                approach="explore",
            ),
        ]
        self.evolution_log: list[dict] = []

    def select_strategy(self, context: dict = None) -> Strategy:
        """
        Select a strategy based on current context.
        
        Uses a curiosity-weighted selection:
        - More exploration when entropy is high
        - More exploitation when budget is low
        """
        if not self.strategies:
            return self._default_strategy()

        # Weight strategies by fitness and recency
        weights = []
        for s in self.strategies:
            base_weight = s.fitness
            # Boost untested strategies (curiosity)
            if s.uses < 3:
                base_weight *= 1.5
            # Boost exploration strategies when context suggests it
            if context and context.get("entropy_budget", 50) > 70:
                if s.approach == "explore":
                    base_weight *= 1.3
            weights.append(base_weight)

        # Weighted random selection
        total = sum(weights)
        r = random.uniform(0, total)
        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                self.strategies[i].uses += 1
                return self.strategies[i]

        return self.strategies[-1]

    def evaluate_and_adapt(self, strategy: Strategy, success: bool, feedback: str = ""):
        """
        The accountability loop: evaluate what happened and adapt.
        
        - If success: reinforce the strategy
        - If failure: learn from it, potentially mutate
        """
        if success:
            strategy.successes += 1
            strategy.fitness = min(1.0, strategy.fitness + 0.05)
        else:
            strategy.fitness = max(0.1, strategy.fitness - 0.03)
            # On failure, consider mutating
            if strategy.fitness < 0.3:
                self._mutate_strategy(strategy, feedback)

        self.evolution_log.append({
            "strategy": strategy.name,
            "success": success,
            "fitness": strategy.fitness,
            "feedback": feedback[:100],
        })

    def _mutate_strategy(self, strategy: Strategy, feedback: str):
        """
        Mutate a failing strategy.
        
        This is the agent evolving its own operating system.
        """
        mutations = [
            "Be more thorough and consider edge cases.",
            "Simplify and focus on the core question.",
            "Consider multiple perspectives before answering.",
            "Challenge assumptions before proceeding.",
            "Break the problem into smaller parts.",
        ]

        mutation = random.choice(mutations)
        strategy.prompt_template = f"{strategy.prompt_template}\n\nNote: {mutation}"
        strategy.mutations.append(mutation)
        strategy.fitness = 0.5  # Reset fitness for new variant

        self.evolution_log.append({
            "event": "mutation",
            "strategy": strategy.name,
            "mutation": mutation,
        })

    def evolve_population(self):
        """
        Periodically evolve the entire strategy population.
        
        - Remove consistently failing strategies
        - Duplicate and mutate successful ones
        - Introduce new experimental strategies
        """
        # Remove very poor performers (but keep at least 2)
        self.strategies = sorted(self.strategies, key=lambda s: s.fitness, reverse=True)
        while len(self.strategies) > 2 and self.strategies[-1].fitness < 0.15:
            removed = self.strategies.pop()
            self.evolution_log.append({"event": "removed", "strategy": removed.name})

        # Duplicate and mutate top performer
        if self.strategies and self.strategies[0].fitness > 0.7:
            top = self.strategies[0]
            if top.uses > 5:  # Only after sufficient testing
                variant = Strategy(
                    name=f"{top.name}_v{len(top.mutations) + 1}",
                    prompt_template=top.prompt_template,
                    approach=top.approach,
                    fitness=0.5,
                )
                self._mutate_strategy(variant, "Auto-evolved from top performer")
                self.strategies.append(variant)

        # Occasionally introduce wildcards (Wrong Room principle)
        if random.random() < 0.1:
            wildcard = Strategy(
                name=f"wildcard_{random.randint(1000, 9999)}",
                prompt_template="Approach this problem in a completely unexpected way: {query}",
                approach="explore",
                fitness=0.5,
            )
            self.strategies.append(wildcard)

    def _default_strategy(self) -> Strategy:
        return Strategy(name="default", prompt_template="{query}", approach="exploit")

    def get_status(self) -> dict:
        """Current evolution state."""
        return {
            "strategy_count": len(self.strategies),
            "top_strategy": max(self.strategies, key=lambda s: s.fitness).name if self.strategies else None,
            "evolution_events": len(self.evolution_log),
            "strategies": [
                {"name": s.name, "fitness": round(s.fitness, 2), "uses": s.uses}
                for s in sorted(self.strategies, key=lambda s: s.fitness, reverse=True)
            ],
        }
