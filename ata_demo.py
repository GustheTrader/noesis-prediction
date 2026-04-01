"""
Agent-to-Agent (ATA) Demo

Demonstrates direct agent communication.
"""

from agent_to_agent import AgentToAgent, AgentMesh, MessageType
import time


def demo():
    """Run ATA demo."""

    print("=" * 60)
    print("🌅 SOVEREIGN OS — Agent-to-Agent Demo")
    print("=" * 60)

    # Create agents
    researcher = AgentToAgent("agent-researcher", "secret-123")
    analyzer = AgentToAgent("agent-analyzer", "secret-456")
    creative = AgentToAgent("agent-creative", "secret-789")

    # Create mesh
    mesh = AgentMesh("wrong-room-mesh")
    mesh.add_node(researcher)
    mesh.add_node(analyzer)
    mesh.add_node(creative)

    print(f"\n📡 Mesh created: {mesh.mesh_id}")
    print(f"   Nodes: {len(mesh.nodes)}")

    # Register peers
    researcher.register_peer("agent-analyzer", "analyzer", "analysis")
    researcher.register_peer("agent-creative", "creative", "creative")

    analyzer.register_peer("agent-researcher", "researcher", "research")
    analyzer.register_peer("agent-creative", "creative", "creative")

    print(f"\n🤖 Peers registered:")
    for node_id, node in mesh.nodes.items():
        print(f"  {node_id}: {len(node.peers)} peers")

    # Send direct message
    print(f"\n📤 Direct message: researcher → analyzer")
    sent = researcher.send(AgentToAgent.__bases__[0].__subclasses__()  # Just use the class directly
    # Actually let's do it properly:
    from agent_to_agent import AgentMessage

    msg = AgentMessage(
        type=MessageType.QUERY,
        sender="agent-researcher",
        recipient="agent-analyzer",
        content="What's your analysis on the BTC covered call strategy?",
    )
    result = researcher.send(msg)
    print(f"   Sent: {result}")

    # Receive on analyzer side
    wire = researcher.gateway.send(
        '{"type":"response","sender":"agent-analyzer","content":"BTC calls are yielding 14.2% annualized. Recommend 30-day expiry."}',
        "agent-researcher"
    )
    received = analyzer.receive(wire, "agent-researcher")
    print(f"   Received: {received.content if received else 'None'}")

    # Broadcast insight
    print(f"\n📡 Broadcasting insight to all peers:")
    results = researcher.share_insight(
        "Discovered: covered calls on ETH yield more during high volatility periods"
    )
    print(f"   Broadcast to {len(results)} peers")

    # Collaboration request
    print(f"\n🤝 Collaboration request:")
    researcher.request_collaboration(
        "agent-creative",
        "Help design the NOESIS market UI",
        context={"priority": "high", "deadline": "2026-04-15"}
    )
    print(f"   Request sent to creative agent")

    # Share evolution
    print(f"\n🔄 Sharing evolution data:")
    analyzer.share_evolution(
        strategy="first_principles",
        fitness=0.85,
        mutations=["Added edge case handling", "Improved confidence calibration"]
    )
    print(f"   Evolution data shared with all peers")

    # Mesh status
    print(f"\n📊 Mesh Status:")
    status = mesh.get_mesh_status()
    print(f"   Mesh: {status['mesh_id']}")
    print(f"   Nodes: {status['nodes']}")
    print(f"   Total peers: {status['total_peers']}")
    print(f"   Total messages: {status['total_messages']}")

    # Agent status
    print(f"\n🤖 Agent Message Stats:")
    for node_id, node in mesh.nodes.items():
        stats = node.get_message_stats()
        print(f"   {node_id}: {stats['total']} messages")

    print("\n" + "=" * 60)
    print("🌅 ATA Protocol — Agents communicating directly.")
    print("   No central server. No corporate middleman.")
    print("   Encrypted. Sovereign. Peer-to-peer.")
    print("=" * 60)


if __name__ == "__main__":
    demo()
