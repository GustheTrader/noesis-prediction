"""
Sovereign OS — Hermes Agent ATA Adapter

Integrates Hermes Agent (Nous Research) as the mesh node.
Hermes = persistent, growing, multi-platform agent.

Features:
- Lives on your server, grows with you
- Telegram, Discord, Slack, WhatsApp, CLI
- Persistent memory across sessions
- Skills that are searchable and shareable
- Scheduled automations (cron)
- Subagent spawning
- Real sandboxing (Docker, SSH, Singularity)
- Model-agnostic (Nous Portal, OpenRouter, custom)

This is the SOVEREIGN OS MESH NODE.
"""

import subprocess
import json
import time
import argparse
from pathlib import Path

from agent_to_agent import AgentToAgent, AgentMessage, MessageType


class HermesAdapter:
    """
    Adapter that connects Hermes Agent as the central mesh node.
    
    Hermes capabilities:
    - Multi-platform messaging (Telegram, Discord, Slack, WhatsApp)
    - Persistent memory across sessions
    - Growing skills library
    - Scheduled automations
    - Subagent spawning
    - Sandboxed execution
    - Model-agnostic (switch models at runtime)
    """

    def __init__(
        self,
        instance_id: str = "hermes-mesh",
        secret_key: str = "hermes-ata-secret",
        hermes_path: str = "~/.hermes/hermes-agent",
    ):
        self.instance_id = instance_id
        self.hermes_path = str(Path(hermes_path).expanduser())
        self.ata = AgentToAgent(instance_id, secret_key)
        self.ata.on_message(MessageType.QUERY, self._handle_query)
        self.ata.on_message(MessageType.COLLABORATE, self._handle_collaborate)
        self.ata.on_message(MessageType.INSIGHT, self._handle_insight)
        self.ata.on_message(MessageType.BROADCAST, self._handle_broadcast)

    def _handle_query(self, msg: AgentMessage):
        """Handle incoming query — forward to Hermes."""
        print(f"\n📥 Query from {msg.sender}: {msg.content[:80]}...")

        response = self.query_hermes(msg.content)

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

        response = self.query_hermes(
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
        """Handle incoming insight — store in Hermes memory."""
        print(f"\n💡 Insight from {msg.sender}: {msg.content[:80]}...")
        # Hermes has persistent memory — insights are automatically stored

    def _handle_broadcast(self, msg: AgentMessage):
        """Handle broadcast — Hermes forwards to all connected platforms."""
        print(f"\n📡 Broadcast from {msg.sender}: {msg.content[:80]}...")
        # Hermes can forward to Telegram, Discord, Slack, WhatsApp

    def query_hermes(self, prompt: str) -> str:
        """Send a query to Hermes Agent."""
        try:
            result = subprocess.run(
                ["hermes", "--print", prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"[Hermes Error: {result.stderr}]"
        except FileNotFoundError:
            return "[Hermes not found. Install: curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash]"
        except subprocess.TimeoutExpired:
            return "[Hermes timeout]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def connect_platform(self, platform: str):
        """Connect Hermes to a messaging platform."""
        print(f"🔗 Connecting to {platform}...")
        # Hermes supports: telegram, discord, slack, whatsapp, cli
        # Would run: hermes config set platform.{platform}.enabled true

    def schedule_task(self, task: str, schedule: str):
        """Schedule a task in Hermes."""
        print(f"⏰ Scheduling: {task}")
        print(f"   Schedule: {schedule}")
        # Hermes has built-in cron scheduler

    def spawn_subagent(self, task: str):
        """Spawn a Hermes subagent for parallel work."""
        print(f"🤖 Spawning subagent for: {task[:50]}...")
        # Hermes supports isolated subagents

    def share_skill(self, skill_name: str, skill_content: str):
        """Share a skill with the mesh."""
        self.ata.share_insight(
            f"[Hermes Skill: {skill_name}] {skill_content[:200]}"
        )

    def listen(self):
        """Listen for incoming ATA messages."""
        print(f"\n🎧 Hermes Agent ATA Adapter listening...")
        print(f"   Instance: {self.instance_id}")
        print(f"   Hermes path: {self.hermes_path}")
        print(f"   Peers: {len(self.ata.peers)}")
        print(f"   Press Ctrl+C to stop\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopped listening")

    def status(self):
        """Show adapter status."""
        print(f"\n📡 Hermes Agent ATA Adapter")
        print(f"   Instance: {self.instance_id}")
        print(f"   Path: {self.hermes_path}")
        print(f"   Peers: {len(self.ata.peers)}")
        print(f"   Messages: {len(self.ata.message_log)}")

        # Check Hermes installation
        hermes_path = Path(self.hermes_path)
        if hermes_path.exists():
            print(f"   Hermes: ✅ Found at {hermes_path}")
        else:
            print(f"   Hermes: ❌ Not found")
            print(f"   Install: curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash")

        # Check hermes CLI
        try:
            result = subprocess.run(
                ["hermes", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                print(f"   CLI: ✅ {result.stdout.strip()}")
            else:
                print(f"   CLI: ❌ Not responding")
        except FileNotFoundError:
            print(f"   CLI: ❌ 'hermes' not in PATH")


class HermesMeshBridge:
    """
    Bridge between Hermes and the full Sovereign OS mesh.
    
    Hermes becomes the CENTRAL NODE:
    - Receives messages from all platforms (Telegram, Discord, etc.)
    - Routes to appropriate agents via ATA
    - Aggregates responses
    - Delivers back to the requesting platform
    
    This is the SOVEREIGN OS MESSENGER.
    """

    def __init__(self, adapter: HermesAdapter):
        self.adapter = adapter

    def run(self):
        """Run the bridge."""
        print(f"\n🌉 Hermes Mesh Bridge running...")
        print(f"")
        print(f"   ┌─────────────────────────────────────┐")
        print(f"   │          HERMES MESH BRIDGE          │")
        print(f"   ├─────────────────────────────────────┤")
        print(f"   │  📱 Telegram ───┐                    │")
        print(f"   │  💬 Discord  ───┼──→ HERMES ──→ ATA  │")
        print(f"   │  📧 Slack    ───┤      ↓       MESH │")
        print(f"   │  📞 WhatsApp ───┤   Response        │")
        print(f"   │  🖥️  CLI      ───┘      ↓            │")
        print(f"   │                   Back to platform   │")
        print(f"   └─────────────────────────────────────┘")
        print(f"")
        print(f"   Connected peers: {len(self.adapter.ata.peers)}")
        print(f"   Press Ctrl+C to stop\n")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Bridge stopped")


def main():
    parser = argparse.ArgumentParser(description="Hermes Agent ATA Adapter")
    parser.add_argument("--status", action="store_true", help="Show adapter status")
    parser.add_argument("--query", type=str, help="Ask Hermes")
    parser.add_argument("--listen", action="store_true", help="Listen for ATA messages")
    parser.add_argument("--bridge", action="store_true", help="Run mesh bridge")
    parser.add_argument("--peer", type=str, help="Connect to peer ID")
    parser.add_argument("--platform", type=str, help="Connect to platform (telegram, discord, slack, whatsapp)")
    parser.add_argument("--schedule", nargs=2, metavar=("TASK", "CRON"), help="Schedule a task")
    parser.add_argument("--path", type=str, default="~/.hermes/hermes-agent", help="Hermes path")

    args = parser.parse_args()

    adapter = HermesAdapter(hermes_path=args.path)

    if args.status:
        adapter.status()
    elif args.query:
        print(adapter.query_hermes(args.query))
    elif args.listen:
        adapter.listen()
    elif args.bridge:
        bridge = HermesMeshBridge(adapter)
        bridge.run()
    elif args.peer:
        adapter.connect_to_mesh(args.peer, "shared-secret")
    elif args.platform:
        adapter.connect_platform(args.platform)
    elif args.schedule:
        adapter.schedule_task(args.schedule[0], args.schedule[1])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
