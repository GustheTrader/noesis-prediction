"""
Sovereign OS — Claude Code ATA Adapter

Integrates Claude Code as a peer in the Agent-to-Agent mesh.
Supports Claude iOS remote connect.

Usage:
    python claude_adapter.py --connect          # Start Claude Code peer
    python claude_adapter.py --query "question"  # Send query to Claude
    python claude_adapter.py --listen            # Listen for ATA messages
"""

import subprocess
import json
import time
import argparse
from pathlib import Path

from agent_to_agent import AgentToAgent, AgentMessage, MessageType
from api_gateway import SovereignAPIGateway


class ClaudeCodeAdapter:
    """
    Adapter that connects Claude Code as a peer in the ATA mesh.
    
    Supports:
    - Claude Code CLI integration
    - Claude iOS remote connect
    - Bidirectional messaging
    - Code generation and review
    """

    def __init__(
        self,
        instance_id: str = "claude-code",
        secret_key: str = "claude-ata-secret",
        claude_command: str = "claude",
    ):
        self.instance_id = instance_id
        self.claude_command = claude_command
        self.ata = AgentToAgent(instance_id, secret_key)
        self.ata.on_message(MessageType.QUERY, self._handle_query)
        self.ata.on_message(MessageType.COLLABORATE, self._handle_collaborate)

    def _handle_query(self, msg: AgentMessage):
        """Handle incoming query — forward to Claude Code."""
        print(f"\n📥 Query from {msg.sender}: {msg.content[:80]}...")

        response = self.query_claude(msg.content)

        # Send response back
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

        response = self.query_claude(
            f"Collaboration request: {task}\nContext: {json.dumps(context)}\n\nProvide your analysis and recommendations."
        )

        reply = AgentMessage(
            type=MessageType.RESPONSE,
            sender=self.instance_id,
            recipient=msg.sender,
            content=response,
            reply_to=msg.id,
        )
        self.ata.send(reply)

    def query_claude(self, prompt: str) -> str:
        """Send a query to Claude Code CLI."""
        try:
            # Use Claude Code CLI
            result = subprocess.run(
                [self.claude_command, "--print", prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return f"[Claude Code Error: {result.stderr}]"
        except FileNotFoundError:
            return "[Claude Code not found. Install with: npm install -g @anthropic-ai/claude-code]"
        except subprocess.TimeoutExpired:
            return "[Claude Code timeout]"
        except Exception as e:
            return f"[Error: {str(e)}]"

    def connect_to_mesh(self, peer_id: str, shared_secret: str):
        """Connect to another ATA peer."""
        self.ata.register_peer(peer_id, peer_id, "agent")
        # In production, would exchange secrets via handshake
        print(f"🔗 Connected to peer: {peer_id}")

    def listen(self):
        """Listen for incoming ATA messages."""
        print(f"\n🎧 Claude Code ATA Adapter listening...")
        print(f"   Instance: {self.instance_id}")
        print(f"   Peers: {len(self.ata.peers)}")
        print(f"   Press Ctrl+C to stop\n")

        try:
            while True:
                # In production, would listen on a socket
                # For now, just keep alive
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopped listening")

    def status(self):
        """Show adapter status."""
        print(f"\n📡 Claude Code ATA Adapter")
        print(f"   Instance: {self.instance_id}")
        print(f"   Claude CLI: {self.claude_command}")
        print(f"   Peers: {len(self.ata.peers)}")
        print(f"   Messages: {len(self.ata.message_log)}")

        # Test Claude connection
        try:
            result = subprocess.run(
                [self.claude_command, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                print(f"   Claude Code: ✅ {result.stdout.strip()}")
            else:
                print(f"   Claude Code: ❌ Not responding")
        except FileNotFoundError:
            print(f"   Claude Code: ❌ Not installed")


class ClaudeRemoteConnect:
    """
    Claude iOS Remote Connect integration.
    
    Allows Claude on iOS to connect to the ATA mesh
    via a bridge server.
    """

    def __init__(self, adapter: ClaudeCodeAdapter, port: int = 8888):
        self.adapter = adapter
        self.port = port

    def start_bridge(self):
        """Start the bridge server for iOS remote connect."""
        print(f"\n🌉 Starting Claude Remote Bridge on port {self.port}...")
        print(f"   Connect from iOS Claude app using:")
        print(f"   http://<your-ip>:{self.port}")
        print(f"\n   iOS Claude → Settings → Remote Connect → Enter URL")
        print(f"\n   Waiting for connections...\n")

        # In production, would run a WebSocket or HTTP server
        # For now, show the concept
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Bridge stopped")

    def handle_ios_message(self, message: str) -> str:
        """Handle message from iOS Claude."""
        print(f"📱 iOS message: {message[:80]}...")

        # Forward to Claude Code
        response = self.adapter.query_claude(message)

        # Also broadcast to ATA mesh if relevant
        if "?" in message:
            self.adapter.ata.share_insight(f"iOS query: {message[:50]}...")

        return response


def main():
    parser = argparse.ArgumentParser(description="Claude Code ATA Adapter")
    parser.add_argument("--connect", action="store_true", help="Start Claude Code peer")
    parser.add_argument("--query", type=str, help="Send query to Claude")
    parser.add_argument("--listen", action="store_true", help="Listen for ATA messages")
    parser.add_argument("--status", action="store_true", help="Show adapter status")
    parser.add_argument("--bridge", action="store_true", help="Start iOS remote bridge")
    parser.add_argument("--peer", type=str, help="Connect to peer ID")
    parser.add_argument("--port", type=int, default=8888, help="Bridge port")

    args = parser.parse_args()

    adapter = ClaudeCodeAdapter()

    if args.status:
        adapter.status()
    elif args.query:
        print(adapter.query_claude(args.query))
    elif args.listen:
        adapter.listen()
    elif args.bridge:
        bridge = ClaudeRemoteConnect(adapter, args.port)
        bridge.start_bridge()
    elif args.peer:
        adapter.connect_to_mesh(args.peer, "shared-secret")
    elif args.connect:
        adapter.status()
        adapter.listen()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
