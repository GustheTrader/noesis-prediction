#!/usr/bin/env python3
"""
Sovereign OS — Agent CLI

Command-line interface for interacting with Sovereign agents.

Usage:
    python cli.py status                    # Agent status
    python cli.py ask "your question"       # Ask an agent
    python cli.py predict "question" yes 0.7  # Submit prediction
    python cli.py markets                   # List open markets
    python cli.py leaderboard               # Show leaderboard
    python cli.py agents                    # List agents
    python cli.py evolve                    # Trigger evolution
    python cli.py broadcast "message"       # Send to mesh
"""

import sys
import json
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from market_engine import MarketEngine
from models import MarketCategory
from agent import Agent
from orchestrator import Orchestrator
from llm_abstraction import SovereignLLM, create_sovereign_llm
from api_gateway import SovereignAPIGateway


class SovereignCLI:
    """CLI for Sovereign OS agents."""

    def __init__(self):
        self.engine = MarketEngine()
        self.orchestrator = Orchestrator(mode="cooperative")
        self.llm = create_sovereign_llm()
        self.gateway = SovereignAPIGateway("cli-instance", "default-secret")

        # Register default agents
        for name, domain in [
            ("researcher", "research"),
            ("analyzer", "analysis"),
            ("creative", "creative"),
            ("meta", "evolution"),
        ]:
            agent = Agent(name=name, domain=domain)
            self.orchestrator.register_agent(agent)

    def status(self):
        """Show system status."""
        status = self.orchestrator.get_collective_status()
        llm_status = self.llm.status()

        print("=" * 60)
        print("🌅 SOVEREIGN OS — STATUS")
        print("=" * 60)

        print(f"\n📡 LLM Backend:")
        print(f"  Active: {llm_status['active']}")
        for name, available in llm_status['available'].items():
            status_icon = "✅" if available else "❌"
            print(f"  {status_icon} {name}")

        print(f"\n🤖 Agents: {status['agent_count']}")
        for name, info in status['agents'].items():
            print(f"  • {name} ({info['domain']}) — skill: {info['skill_level']}, "
                  f"success: {info['success_rate']:.0%}, budget: {info['curiosity']['entropy_budget']:.0f}")

        print(f"\n📊 Markets: {len(self.engine.get_open_markets())} open")
        print(f"🏆 Leaderboard: {len(self.engine.get_leaderboard())} members")

    def ask(self, question: str):
        """Ask an agent a question."""
        print(f"\n🤔 Thinking...\n")
        response = self.llm.complete(question, system="You are a Sovereign OS agent. Be concise and insightful.")
        print(response.content)
        print(f"\n[{response.backend} | {response.model} | {response.tokens_used} tokens | {response.latency_ms:.0f}ms]")

    def predict(self, question: str, answer: str, confidence: float):
        """Submit a prediction."""
        # Find or create market
        markets = self.engine.get_open_markets()
        market = next((m for m in markets if question.lower() in m.question.lower()), None)

        if not market:
            market = self.engine.create_market(
                question=question,
                category=MarketCategory.REALITY_OS,
                created_by="cli",
            )
            print(f"📊 Created new market: {question}")

        prediction = answer.lower() in ("yes", "true", "y", "1")
        pred = self.engine.submit_prediction(
            market.id,
            "cli-user",
            prediction,
            confidence,
        )

        if pred:
            direction = "YES" if prediction else "NO"
            print(f"✅ Prediction submitted: {direction} @ {confidence:.0%} confidence")
            print(f"   Market: {market.question}")
            print(f"   Prices: YES {market.yes_price:.0%} | NO {market.no_price:.0%}")

    def markets(self):
        """List open markets."""
        open_markets = self.engine.get_open_markets()
        print(f"\n📊 Open Markets ({len(open_markets)}):\n")
        for m in open_markets:
            print(f"  • {m.question}")
            print(f"    YES: {m.yes_price:.0%} | NO: {m.no_price:.0%}")
            print(f"    Category: {m.category.value}")
            print()

    def leaderboard(self):
        """Show leaderboard."""
        board = self.engine.get_leaderboard()
        print(f"\n🏆 Leaderboard:\n")
        print(f"  {'#':<4} {'MEMBER':<15} {'ACCURACY':<10} {'PREDICTIONS':<12}")
        print(f"  {'-'*45}")
        for i, entry in enumerate(board, 1):
            print(f"  {i:<4} {entry['member_id']:<15} {entry['accuracy']:.0%}        {entry['total']}")

    def agents(self):
        """List agents."""
        status = self.orchestrator.get_collective_status()
        print(f"\n🤖 Agents ({status['agent_count']}):\n")
        for name, info in status['agents'].items():
            print(f"  • {name} ({info['domain']})")
            print(f"    Skill: {info['skill_level']:.2f} | Success: {info['success_rate']:.0%}")
            print(f"    Budget: {info['curiosity']['entropy_budget']:.0f} | Memory: {info['memory']['total']}")
            print(f"    Strategy: {info['evolution']['top_strategy']}")
            print()

    def evolve(self):
        """Trigger agent evolution."""
        print("\n🔄 Triggering evolution...\n")
        for name, agent in self.orchestrator.agents.items():
            agent.evolver.evolve_population()
            status = agent.get_status()
            print(f"  {name}: {status['evolution']['evolution_events']} evolution events")
        print("\n✅ Evolution complete.")

    def broadcast(self, message: str):
        """Broadcast message to mesh."""
        wire = self.gateway.send(message, "mesh")
        if wire:
            print(f"\n📡 Broadcast sent: {len(wire)} bytes encrypted")
            print(f"   Message: {message[:50]}...")
        else:
            print("\n❌ Broadcast failed")

    def run(self):
        """Main CLI entry point."""
        parser = argparse.ArgumentParser(
            description="Sovereign OS — Agent CLI",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python cli.py status
  python cli.py ask "What is first principles thinking?"
  python cli.py predict "Will Bitcoin hit 200K?" yes 0.7
  python cli.py markets
  python cli.py leaderboard
  python cli.py agents
  python cli.py evolve
  python cli.py broadcast "Hello from Sovereign OS"
            """,
        )

        parser.add_argument("command", choices=[
            "status", "ask", "predict", "markets", "leaderboard",
            "agents", "evolve", "broadcast"
        ])
        parser.add_argument("args", nargs="*", help="Command arguments")

        args = parser.parse_args()

        if args.command == "status":
            self.status()
        elif args.command == "ask":
            question = " ".join(args.args) if args.args else "What is Sovereign OS?"
            self.ask(question)
        elif args.command == "predict":
            if len(args.args) < 3:
                print("Usage: python cli.py predict 'question' yes/no confidence")
                return
            self.predict(args.args[0], args.args[1], float(args.args[2]))
        elif args.command == "markets":
            self.markets()
        elif args.command == "leaderboard":
            self.leaderboard()
        elif args.command == "agents":
            self.agents()
        elif args.command == "evolve":
            self.evolve()
        elif args.command == "broadcast":
            message = " ".join(args.args) if args.args else "Hello from Sovereign OS"
            self.broadcast(message)


if __name__ == "__main__":
    cli = SovereignCLI()
    cli.run()
