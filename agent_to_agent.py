"""
Sovereign OS — Agent-to-Agent (ATA) Protocol

Agents communicate, collaborate, and co-evolve.
Not through a central server. Direct peer-to-peer.
"""

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum

from api_gateway import SovereignAPIGateway, SovereignEncryption
from llm_abstraction import SovereignLLM


class MessageType(Enum):
    """Types of agent-to-agent messages."""
    QUERY = "query"              # Ask another agent a question
    RESPONSE = "response"        # Answer to a query
    BROADCAST = "broadcast"      # Message to all agents
    INSIGHT = "insight"          # Share a discovery
    PREDICTION = "prediction"    # Share a prediction
    COLLABORATE = "collaborate"  # Request collaboration
    EVOLVE = "evolve"            # Share evolution data
    HEARTBEAT = "heartbeat"      # Health check


@dataclass
class AgentMessage:
    """An agent-to-agent message."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.QUERY
    sender: str = ""
    recipient: str = ""  # "" = broadcast
    content: str = ""
    metadata: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    reply_to: Optional[str] = None  # For responses


class AgentToAgent:
    """
    Agent-to-Agent communication protocol.
    
    Features:
    - Direct messaging between agents
    - Broadcasting to all agents
    - Encrypted communication
    - Message routing
    - Collaboration requests
    - Insight sharing
    """

    def __init__(self, instance_id: str, secret_key: str):
        self.instance_id = instance_id
        self.gateway = SovereignAPIGateway(instance_id, secret_key)
        self.message_handlers: dict[MessageType, list[Callable]] = {}
        self.message_log: list[AgentMessage] = []
        self.peers: dict[str, dict] = {}  # peer_id -> {name, domain, capabilities}

    def register_peer(self, peer_id: str, name: str, domain: str, capabilities: list = None):
        """Register a peer agent."""
        self.peers[peer_id] = {
            "name": name,
            "domain": domain,
            "capabilities": capabilities or [],
            "last_seen": time.time(),
        }

    def on_message(self, msg_type: MessageType, handler: Callable):
        """Register a handler for a message type."""
        if msg_type not in self.message_handlers:
            self.message_handlers[msg_type] = []
        self.message_handlers[msg_type].append(handler)

    def send(self, msg: AgentMessage) -> bool:
        """Send a message to another agent."""
        # Serialize
        data = json.dumps({
            "id": msg.id,
            "type": msg.type.value,
            "sender": msg.sender,
            "recipient": msg.recipient,
            "content": msg.content,
            "metadata": msg.metadata,
            "timestamp": msg.timestamp,
            "reply_to": msg.reply_to,
        })

        # Encrypt
        wire = self.gateway.send(data, msg.recipient)

        if wire:
            self.message_log.append(msg)
            return True
        return False

    def receive(self, wire: str, from_peer: str = "") -> Optional[AgentMessage]:
        """Receive and decrypt a message."""
        data = self.gateway.receive(wire, from_peer)
        if not data:
            return None

        try:
            parsed = json.loads(data)
            msg = AgentMessage(
                id=parsed["id"],
                type=MessageType(parsed["type"]),
                sender=parsed["sender"],
                recipient=parsed.get("recipient", ""),
                content=parsed["content"],
                metadata=parsed.get("metadata", {}),
                timestamp=parsed["timestamp"],
                reply_to=parsed.get("reply_to"),
            )

            # Update peer last seen
            if msg.sender in self.peers:
                self.peers[msg.sender]["last_seen"] = time.time()

            # Call handlers
            handlers = self.message_handlers.get(msg.type, [])
            for handler in handlers:
                handler(msg)

            self.message_log.append(msg)
            return msg

        except Exception:
            return None

    def query(self, peer_id: str, question: str, timeout: int = 30) -> Optional[str]:
        """Ask another agent a question. Returns response or None."""
        msg = AgentMessage(
            type=MessageType.QUERY,
            sender=self.instance_id,
            recipient=peer_id,
            content=question,
        )

        if not self.send(msg):
            return None

        # Wait for response (in production, use async)
        start = time.time()
        while time.time() - start < timeout:
            for log_msg in reversed(self.message_log):
                if (log_msg.type == MessageType.RESPONSE and
                        log_msg.reply_to == msg.id):
                    return log_msg.content
            time.sleep(0.5)

        return None

    def broadcast(self, content: str, msg_type: MessageType = MessageType.BROADCAST):
        """Broadcast a message to all peers."""
        results = {}
        for peer_id in self.peers:
            msg = AgentMessage(
                type=msg_type,
                sender=self.instance_id,
                recipient=peer_id,
                content=content,
            )
            results[peer_id] = self.send(msg)
        return results

    def share_insight(self, insight: str, domain: str = "", tags: list = None):
        """Share an insight with all peers."""
        return self.broadcast(
            insight,
            msg_type=MessageType.INSIGHT,
        )

    def request_collaboration(self, peer_id: str, task: str, context: dict = None):
        """Request collaboration from another agent."""
        msg = AgentMessage(
            type=MessageType.COLLABORATE,
            sender=self.instance_id,
            recipient=peer_id,
            content=task,
            metadata=context or {},
        )
        return self.send(msg)

    def share_evolution(self, strategy: str, fitness: float, mutations: list = None):
        """Share evolution data with peers."""
        data = json.dumps({
            "strategy": strategy,
            "fitness": fitness,
            "mutations": mutations or [],
            "agent": self.instance_id,
        })
        return self.broadcast(data, msg_type=MessageType.EVOLVE)

    def get_peer_status(self) -> dict:
        """Status of all peers."""
        now = time.time()
        return {
            peer_id: {
                "name": info["name"],
                "domain": info["domain"],
                "capabilities": info["capabilities"],
                "online": (now - info["last_seen"]) < 60,
                "last_seen": info["last_seen"],
            }
            for peer_id, info in self.peers.items()
        }

    def get_message_stats(self) -> dict:
        """Message statistics."""
        by_type = {}
        for msg in self.message_log:
            t = msg.type.value
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total": len(self.message_log),
            "by_type": by_type,
            "peers": len(self.peers),
        }


class AgentMesh:
    """
    Mesh network of agents.
    
    Multiple AgentToAgent instances connected.
    Decentralized. Encrypted. Sovereign.
    """

    def __init__(self, mesh_id: str = "default"):
        self.mesh_id = mesh_id
        self.nodes: dict[str, AgentToAgent] = {}

    def add_node(self, node: AgentToAgent):
        """Add a node to the mesh."""
        self.nodes[node.instance_id] = node

        # Register all existing nodes as peers
        for existing_id, existing in self.nodes.items():
            if existing_id != node.instance_id:
                existing.register_peer(
                    node.instance_id,
                    node.instance_id,
                    "agent",
                )
                node.register_peer(
                    existing_id,
                    existing_id,
                    "agent",
                )

    def broadcast_all(self, content: str):
        """Broadcast to entire mesh."""
        results = {}
        for node_id, node in self.nodes.items():
            for peer_id in node.peers:
                results[f"{node_id}->{peer_id}"] = node.broadcast(content)
        return results

    def get_mesh_status(self) -> dict:
        """Status of entire mesh."""
        return {
            "mesh_id": self.mesh_id,
            "nodes": len(self.nodes),
            "total_peers": sum(len(n.peers) for n in self.nodes.values()),
            "total_messages": sum(len(n.message_log) for n in self.nodes.values()),
        }
