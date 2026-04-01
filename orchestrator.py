"""
Orchestrator — Multi-agent coordination.

Reality OS Principle: Agentic amplification.
Multiple specialized agents working together,
each bringing their domain expertise to the collective.
"""

from agent import Agent


class Orchestrator:
    """
    Coordinates multiple agents toward a shared goal.
    
    Modes:
    - Parallel: agents work independently, results merged
    - Sequential: agents build on each other's work
    - Competitive: agents compete, best result wins
    - Cooperative: agents collaborate, sharing insights
    """

    def __init__(self, mode: str = "cooperative"):
        self.agents: dict[str, Agent] = {}
        self.mode = mode
        self.shared_memory: list[dict] = []

    def register_agent(self, agent: Agent):
        """Add an agent to the team."""
        self.agents[agent.state.name] = agent

    def distribute_task(self, task: str) -> list[dict]:
        """
        Distribute a task to all agents based on their domains.
        """
        results = []

        for name, agent in self.agents.items():
            decision = agent.decide(task, context={"mode": self.mode})
            result = agent.execute(decision)

            # Share results in cooperative mode
            if self.mode == "cooperative":
                self._share_insight(name, result)

            results.append({
                "agent": name,
                "domain": agent.state.domain,
                "result": result,
            })

        return results

    def _share_insight(self, agent_name: str, result: dict):
        """Share an agent's insight with the collective."""
        insight = {
            "from": agent_name,
            "content": result,
            "timestamp": result.get("timestamp", 0),
        }
        self.shared_memory.append(insight)

        # Other agents can learn from shared insights
        for name, agent in self.agents.items():
            if name != agent_name:
                agent.memory.remember(
                    content=f"Insight from {agent_name}: {str(result)[:200]}",
                    memory_type="episodic",
                    importance=0.4,
                    tags=["shared", agent_name],
                )

    def evaluate_all(self, results: list[dict], feedback: dict = None):
        """Evaluate all agents' results."""
        feedback = feedback or {}

        for r in results:
            agent_name = r["agent"]
            if agent_name in self.agents:
                success = feedback.get(agent_name, {}).get("success", True)
                fb = feedback.get(agent_name, {}).get("feedback", "")
                self.agents[agent_name].evaluate(r["result"], success, fb)

    def get_collective_status(self) -> dict:
        """Status of the entire agent collective."""
        return {
            "mode": self.mode,
            "agent_count": len(self.agents),
            "agents": {
                name: agent.get_status()
                for name, agent in self.agents.items()
            },
            "shared_memory_size": len(self.shared_memory),
        }
