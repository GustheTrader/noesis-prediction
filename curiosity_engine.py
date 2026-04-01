"""
Curiosity Engine — Drives exploration based on entropy and novelty.

Reality OS Principle: Dopamine = curiosity driver, not pleasure chemical.
The agent explores because it's curious, not because it's optimizing a reward.
"""

import random
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExplorationState:
    """Tracks the agent's exploration history."""
    visited: set = field(default_factory=set)
    novelty_scores: dict = field(default_factory=dict)
    entropy_budget: float = 100.0  # "dopamine salary" — needs budgeting
    exploration_count: int = 0
    exploit_count: int = 0


class CuriosityEngine:
    """
    Drives agent behavior through curiosity rather than optimization.
    
    Key insight: High entropy = high dopamine = more exploration.
    The agent should seek novel, unpredictable environments (the "Wrong Room").
    """

    def __init__(self, exploration_ratio: float = 0.7):
        self.state = ExplorationState()
        self.exploration_ratio = exploration_ratio  # 70% explore, 30% exploit

    def novelty_score(self, observation: Any) -> float:
        """Score how novel/new an observation is."""
        obs_hash = hashlib.md5(json.dumps(observation, default=str).encode()).hexdigest()

        if obs_hash in self.state.visited:
            return 0.0  # Already seen

        self.state.visited.add(obs_hash)

        # Calculate novelty based on how different this is from past observations
        # Higher entropy = more novel
        if len(self.state.visited) < 10:
            return 1.0  # Everything is novel early on

        # Novelty decreases as we explore more (diminishing returns)
        novelty = 1.0 / (1.0 + len(self.state.visited) * 0.01)
        return novelty

    def should_explore(self) -> bool:
        """Decide whether to explore (novel) or exploit (known)."""
        if self.state.entropy_budget <= 0:
            return False  # Budget exhausted — must exploit

        # Curiosity-driven: explore more when budget is high
        explore_chance = self.exploration_ratio * (self.state.entropy_budget / 100.0)
        return random.random() < explore_chance

    def consume_budget(self, amount: float = 1.0):
        """Consume entropy budget (like spending dopamine)."""
        self.state.entropy_budget = max(0, self.state.entropy_budget - amount)

    def restore_budget(self, amount: float = 5.0):
        """Restore budget (sleep, rest, novel experience)."""
        self.state.entropy_budget = min(100, self.state.entropy_budget + amount)

    def seek_wrong_room(self, available_rooms: list[dict]) -> dict:
        """
        The Wrong Room Principle: seek environments where you're NOT the best.
        
        Choose the room with the highest challenge-to-skill ratio.
        """
        if not available_rooms:
            return {}

        # Score rooms by challenge level (higher = more "wrong room")
        for room in available_rooms:
            challenge = room.get("difficulty", 0.5)
            skill = room.get("my_skill_level", 0.5)
            # Wrong room = challenge > skill
            room["_wrong_room_score"] = challenge / max(skill, 0.01)

        # Pick the most challenging room (the "wrongest" room)
        available_rooms.sort(key=lambda r: r["_wrong_room_score"], reverse=True)
        chosen = available_rooms[0]

        self.consume_budget(2.0)  # Seeking wrong rooms costs more
        return chosen

    def get_status(self) -> dict:
        """Current curiosity state."""
        return {
            "entropy_budget": self.state.entropy_budget,
            "unique_observations": len(self.state.visited),
            "exploration_count": self.state.exploration_count,
            "exploit_count": self.state.exploit_count,
            "explore_ratio": (
                self.state.exploration_count / max(1, self.state.exploration_count + self.state.exploit_count)
            ),
        }
