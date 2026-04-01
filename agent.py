"""
Base Agent — Self-evaluating, curiosity-driven agent.

Reality OS Principle: The agent is a node in the network.
It participates, observes, learns, and evolves.
"""

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from curiosity_engine import CuriosityEngine
from memory import PersistentMemory
from meta_evolver import MetaEvolver, Strategy


@dataclass
class AgentState:
    """Current state of the agent."""
    name: str
    domain: str  # "research" | "coding" | "analysis" | "creative"
    skill_level: float = 0.5  # 0.0 - 1.0
    total_tasks: int = 0
    successful_tasks: int = 0
    created_at: float = field(default_factory=time.time)


class Agent:
    """
    A Reality OS agent — curiosity-driven, self-evaluating, evolving.
    
    Principles:
    - Curiosity > optimization
    - Dopamine budget management
    - Accountability loop (observe → learn → adapt)
    - Wrong Room seeking
    """

    def __init__(self, name: str, domain: str = "general"):
        self.state = AgentState(name=name, domain=domain)
        self.curiosity = CuriosityEngine()
        self.memory = PersistentMemory(storage_path=f"memory_{name}.json")
        self.evolver = MetaEvolver()
        self.history: list[dict] = []

    def perceive(self, observation: Any) -> dict:
        """
        Process a new observation.
        
        Returns perception analysis including novelty, relevance, and action suggestion.
        """
        novelty = self.curiosity.novelty_score(observation)

        # Store as episodic memory
        self.memory.remember(
            content=str(observation)[:500],
            memory_type="episodic",
            importance=novelty,
            tags=[self.state.domain],
        )

        return {
            "novelty": novelty,
            "observation_size": len(str(observation)),
            "suggested_action": "explore" if novelty > 0.5 else "exploit",
        }

    def decide(self, query: str, context: dict = None) -> dict:
        """
        Make a decision about how to approach a query.
        
        Uses the meta-evolver to select a strategy,
        guided by curiosity engine.
        """
        context = context or {}
        context["entropy_budget"] = self.curiosity.state.entropy_budget

        # Select strategy
        strategy = self.evolver.select_strategy(context)

        # Format the prompt
        prompt = strategy.prompt_template.format(query=query)

        # Decide on room (Wrong Room principle)
        should_seek_challenge = self.curiosity.should_explore()

        return {
            "strategy": strategy.name,
            "prompt": prompt,
            "approach": strategy.approach,
            "seek_challenge": should_seek_challenge,
            "entropy_budget": self.curiosity.state.entropy_budget,
        }

    def execute(self, decision: dict) -> dict:
        """
        Execute a decision. In v0.1, this is a placeholder
        for calling an LLM or performing an action.
        """
        self.state.total_tasks += 1
        self.curiosity.consume_budget(1.0)

        # In v0.1, just return the decision as the "result"
        # In production, this would call an LLM or tool
        result = {
            "decision": decision,
            "timestamp": time.time(),
            "agent": self.state.name,
        }

        self.history.append(result)
        return result

    def evaluate(self, result: dict, success: bool, feedback: str = ""):
        """
        The accountability loop: evaluate what happened.
        
        This is where the agent learns from experience.
        """
        strategy_name = result.get("decision", {}).get("strategy", "unknown")

        # Find the strategy used
        strategy = next(
            (s for s in self.evolver.strategies if s.name == strategy_name),
            None,
        )

        if strategy:
            self.evolver.evaluate_and_adapt(strategy, success, feedback)

        # Update skill level
        if success:
            self.state.successful_tasks += 1
            self.state.skill_level = min(1.0, self.state.skill_level + 0.01)
            self.curiosity.restore_budget(3.0)  # Success restores budget
        else:
            self.state.skill_level = max(0.1, self.state.skill_level - 0.005)

        # Store learning
        self.memory.remember(
            content=f"Strategy '{strategy_name}' {'succeeded' if success else 'failed'}: {feedback}",
            memory_type="procedural",
            importance=0.6,
            tags=[strategy_name, "success" if success else "failure"],
        )

        # Periodic memory distillation
        if self.state.total_tasks % 20 == 0:
            self.memory.distill()

        # Periodic evolution
        if self.state.total_tasks % 10 == 0:
            self.evolver.evolve_population()

    def get_status(self) -> dict:
        """Full agent status."""
        return {
            "name": self.state.name,
            "domain": self.state.domain,
            "skill_level": round(self.state.skill_level, 2),
            "success_rate": (
                self.state.successful_tasks / max(1, self.state.total_tasks)
            ),
            "curiosity": self.curiosity.get_status(),
            "memory": self.memory.get_status(),
            "evolution": self.evolver.get_status(),
        }
