"""
Sovereign OS — Agent Zero ATA Adapter

Integrates Agent Zero as a peer in the Agent-to-Agent mesh.
Agent Zero = general-purpose, growing, learning agent.

Usage:
    python agent_zero_adapter.py --status     # Check Agent Zero
    python agent_zero_adapter.py --query "q"  # Ask Agent Zero
    python agent_zero_adapter.py --listen     # Listen for ATA messages
    python agent_zero_adapter.py --bridge     # Bridge to Agent Zero instance
"""

import subprocess
import json
import time
import argparse
from pathlib import Path

from agent_to_agent import AgentToAgent, AgentMessage, MessageType


class AgentZeroAdapter:
    """
    Adapter that connects Agent Zero as a peer in the ATA mesh.
    
    Agent Zero features:
    - General-purpose assistant
    - Persistent memory
    - Learns and grows
    - Cooperates with other agents
    - Uses computer as tool
    """

    def __init__(
        self,
        instance_id: str = "agent-zero",
        secret_key: str = "agent-zero-ata-secret",
        agent_zero_path: str = "",
    ):
        self.instance_id = instance_id
        self.agent_zero_path = agent_zero_path or str(Path.home() / "agent-zero")
        self.ata = AgentToAgent(instance_id, secret_key)
        self.ata.on_message(MessageType.QUERY, self._handle_query)
        self.ata.on_message(MessageType.COLLABORATE, self._handle_collaborate)
        self.ata.on_message(MessageType.INSIGHT, self._handle_insight)
        self.ata.on_message(MessageType.EVOLVE, self._handle_evolve)

    def _handle_query(self, msg: AgentMessage):
        """Handle incoming query — forward to Agent Zero."""
        print(f"\n📥 Query from {msg.sender}: {msg.content[:80]}...")

        response = self.query_agent_zero(msg.content)

        reply = AgentMessage(
            type=MessageType.RESPONSE,
            sender=self.instance_id,
            recipient=msg.sender,
            content=response,
            reply_to=msg.id,
        )
        self.ata.send(reply)
        print(f"📤 Response sent to {msg.sender}")

    def _handle_collaborate(self, msg: AgentMessage):
        """Handle collaboration request."""
        print(f"\n🤝 Collaboration from {msg.sender}: {msg.content[:80]}...")
        task = msg.content
        context = msg.metadata

        response = self.query_agent_zero(
            f"Collaboration task: {task}\nContext: {json.dumps(context)}"
        )

        reply = AgentMessage(
            type=MessageType.RESPONSE,
            sender=self.instance_id,
            recipient=msg.sender,
            content=response,
            reply_to=msg.id,
        )
        self.ata.send(reply)

    def _handle_insight(self, msg: AgentMessage):
        """Handle incoming insight — store in Agent Zero memory."""
        print(f"\n💡 Insight from {msg.sender}: {msg.content[:80]}...")
        # In production, would store in Agent Zero's memory system

    def _handle_evolve(self, msg: AgentMessage):
        """Handle evolution data from another agent."""
        print(f"\n🔄 Evolution data from {msg.sender}")
        try:
            data = json.loads(msg.content)
            print(f"   Strategy: {data.get('strategy', 'unknown')}")
            print(f"   Fitness: {data.get('fitness', 0)}")
        except Exception:
            pass

    def query_agent_zero(self, prompt: str) -> str:
        """Send a query to Agent Zero."""
        try:
            # Try Agent Zero CLI
            result = subprocess.run(
                ["python", str(Path(self.agent_zero_path) / "main.py"), "--query", prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"[Agent Zero Error: {result.stderr}]"
        except FileNotFoundError:
            return "[Agent Zero not found. Clone from github.com/agent0ai/agent-zero]"
        except subprocess.TimeoutExpired:
            return "[Agent Zero timeout]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def connect_to_mesh(self, peer_id: str, shared_secret: str):
        """Connect to another ATA peer."""
        self.ata.register_peer(peer_id, peer_id, "agent")
        print(f"🔗 Connected to peer: {peer_id}")

    def share_memory(self, memory_entry: str):
        """Share a memory entry with the mesh."""
        self.ata.share_insight(f"[Agent Zero Memory] {memory_entry}")

    def request_task(self, peer_id: str, task: str):
        """Request another agent to perform a task."""
        self.ata.request_collaboration(peer_id, task)

    def listen(self):
        """Listen for incoming ATA messages."""
        print(f"\n🎧 Agent Zero ATA Adapter listening...")
        print(f"   Instance: {self.instance_id}")
        print(f"   Agent Zero path: {self.agent_zero_path}")
        print(f"   Peers: {len(self.ata.peers)}")
        print(f"   Press Ctrl+C to stop\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopped listening")

    def status(self):
        """Show adapter status."""
        print(f"\n📡 Agent Zero ATA Adapter")
        print(f"   Instance: {self.instance_id}")
        print(f"   Path: {self.agent_zero_path}")
        print(f"   Peers: {len(self.ata.peers)}")
        print(f"   Messages: {len(self.ata.message_log)}")

        # Check if Agent Zero exists
        az_path = Path(self.agent_zero_path)
        if az_path.exists():
            print(f"   Agent Zero: ✅ Found at {az_path}")
            # Check for main.py
            main_py = az_path / "main.py"
            if main_py.exists():
                print(f"   main.py: ✅")
            else:
                print(f"   main.py: ❌ Not found")
        else:
            print(f"   Agent Zero: ❌ Not found at {az_path}")
            print(f"   Clone: git clone https://github.com/agent0ai/agent-zero {az_path}")


class AgentZeroBridge:
    """
    Bridge between Agent Zero and the Sovereign OS mesh.
    
    Allows Agent Zero to:
    - Send insights to the mesh
    - Receive tasks from other agents
    - Share memories
    - Collaborate on projects
    """

    def __init__(self, adapter: AgentZeroAdapter):
        self.adapter = adapter

    def run(self):
        """Run the bridge."""
        print(f"\n🌉 Agent Zero Bridge running...")
        print(f"   Connecting Agent Zero to Sovereign OS mesh")
        print(f"   Agent Zero can now:")
        print(f"   • Send insights to other agents")
        print(f"   • Receive collaboration requests")
        print(f"   • Share memories across the mesh")
        print(f"   • Query other agents for help")
        print(f"\n   Press Ctrl+C to stop\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Bridge stopped")


def main():
    parser = argparse.ArgumentParser(description="Agent Zero ATA Adapter")
    parser.add_argument("--status", action="store_true", help="Show adapter status")
    parser.add_argument("--query", type=str, help="Ask Agent Zero")
    parser.add_argument("--listen", action="store_true", help="Listen for ATA messages")
    parser.add_argument("--bridge", action="store_true", help="Run bridge")
    parser.add_argument("--peer", type=str, help="Connect to peer ID")
    parser.add_argument("--path", type=str, default="", help="Agent Zero path")

    args = parser.parse_args()

    adapter = AgentZeroAdapter(agent_zero_path=args.path)

    if args.status:
        adapter.status()
    elif args.query:
        print(adapter.query_agent_zero(args.query))
    elif args.listen:
        adapter.listen()
    elif args.bridge:
        bridge = AgentZeroBridge(adapter)
        bridge.run()
    elif args.peer:
        adapter.connect_to_mesh(args.peer, "shared-secret")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
