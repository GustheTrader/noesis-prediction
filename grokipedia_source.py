"""
Sovereign OS — Grokipedia Knowledge Source + Validation Engine

Grokipedia = AI-generated encyclopedia by xAI (Grok).
Structured knowledge for validation, fact-checking, and market creation.

KNOWLEDGE GRAPH → VALIDATION → PREDICTION MARKETS

The interaction:
1. Knowledge Graph provides GROUND TRUTH (facts, relationships, context)
2. Validation Engine checks CLAIMS against ground truth
3. Prediction Markets use validation to SCORE predictions
4. Leaderboard tracks ACCURACY over time
5. Agents LEARN from validation feedback

This creates a FEEDBACK LOOP:
Claims → Validate against graph → Score → Learn → Better claims
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class KnowledgeNode:
    """A node in the knowledge graph."""
    id: str
    title: str
    content: str
    citations: list = field(default_factory=list)
    categories: list = field(default_factory=list)
    relationships: list = field(default_factory=list)  # [(node_id, relationship_type)]
    source: str = "grokipedia"
    confidence: float = 0.8
    last_updated: float = field(default_factory=time.time)


@dataclass
class ValidationResult:
    """Result of validating a claim against the knowledge graph."""
    claim: str
    is_valid: bool
    confidence: float
    supporting_evidence: list = field(default_factory=list)
    contradicting_evidence: list = field(default_factory=list)
    source: str = ""
    reasoning: str = ""


@dataclass
class ValidationPoint:
    """
    A validation point in the interaction between knowledge graph and predictions.
    
    This is WHERE knowledge meets prediction:
    - Knowledge graph provides facts
    - Predictions make claims about future
    - Validation points check claims against facts
    - Scores are updated based on validation
    """
    id: str
    claim: str
    knowledge_node_id: str
    validation_type: str  # "fact_check", "consistency", "source_verify"
    result: Optional[ValidationResult] = None
    created_at: float = field(default_factory=time.time)


class KnowledgeGraph:
    """
    Knowledge graph powered by Grokipedia + Wikidata + custom sources.
    
    Structure:
    - Nodes = entities, concepts, facts
    - Edges = relationships between nodes
    - Properties = attributes of nodes
    
    The graph is the GROUND TRUTH layer.
    """

    def __init__(self):
        self.nodes: dict[str, KnowledgeNode] = {}
        self.edges: list[dict] = []  # [{from, to, type, weight}]
        self.categories: dict[str, list[str]] = {}  # category -> [node_ids]

    def add_node(self, node: KnowledgeNode):
        """Add a node to the graph."""
        self.nodes[node.id] = node

        # Index by category
        for cat in node.categories:
            if cat not in self.categories:
                self.categories[cat] = []
            self.categories[cat].append(node.id)

    def add_edge(self, from_id: str, to_id: str, relationship: str, weight: float = 1.0):
        """Add a relationship between nodes."""
        self.edges.append({
            "from": from_id,
            "to": to_id,
            "type": relationship,
            "weight": weight,
        })

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def search(self, query: str, limit: int = 5) -> list[KnowledgeNode]:
        """Search nodes by content similarity (simple keyword match)."""
        query_lower = query.lower()
        scored = []

        for node in self.nodes.values():
            score = 0
            if query_lower in node.title.lower():
                score += 3
            if query_lower in node.content.lower():
                score += 1
            for word in query_lower.split():
                if word in node.content.lower():
                    score += 0.5

            if score > 0:
                scored.append((score, node))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [n for _, n in scored[:limit]]

    def get_relationships(self, node_id: str) -> list[dict]:
        """Get all relationships for a node."""
        return [e for e in self.edges if e["from"] == node_id or e["to"] == node_id]

    def get_category(self, category: str) -> list[KnowledgeNode]:
        """Get all nodes in a category."""
        node_ids = self.categories.get(category, [])
        return [self.nodes[nid] for nid in node_ids if nid in self.nodes]

    def get_stats(self) -> dict:
        """Graph statistics."""
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "categories": len(self.categories),
            "category_list": list(self.categories.keys()),
        }


class ValidationEngine:
    """
    Validates claims against the knowledge graph.
    
    This is the BRIDGE between knowledge and prediction.
    
    Types of validation:
    1. FACT CHECK — Is this claim supported by known facts?
    2. CONSISTENCY — Is this consistent with other claims?
    3. SOURCE VERIFY — Is the source credible?
    4. LOGICAL — Does this follow logically?
    5. TEMPORAL — Is this consistent with timeline?
    """

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self.validation_log: list[ValidationResult] = []

    def validate_claim(
        self,
        claim: str,
        validation_type: str = "fact_check",
    ) -> ValidationResult:
        """Validate a claim against the knowledge graph."""

        # Find relevant knowledge nodes
        relevant_nodes = self.graph.search(claim, limit=5)

        if not relevant_nodes:
            result = ValidationResult(
                claim=claim,
                is_valid=True,  # No contradicting evidence found
                confidence=0.3,  # Low confidence — no supporting evidence
                reasoning="No relevant knowledge found in graph",
            )
            self.validation_log.append(result)
            return result

        # Analyze claim against knowledge
        supporting = []
        contradicting = []

        for node in relevant_nodes:
            analysis = self._analyze_against_node(claim, node)
            if analysis["supports"]:
                supporting.append({
                    "node": node.id,
                    "title": node.title,
                    "evidence": analysis["evidence"],
                })
            if analysis["contradicts"]:
                contradicting.append({
                    "node": node.id,
                    "title": node.title,
                    "evidence": analysis["evidence"],
                })

        # Determine validity
        if contradicting and not supporting:
            is_valid = False
            confidence = 0.8
            reasoning = "Claim contradicts known knowledge"
        elif supporting and not contradicting:
            is_valid = True
            confidence = 0.7 + (len(supporting) * 0.1)
            reasoning = "Claim supported by knowledge graph"
        elif supporting and contradicting:
            is_valid = True  # Lean toward validity
            confidence = 0.5
            reasoning = "Mixed evidence — leaning valid"
        else:
            is_valid = True
            confidence = 0.4
            reasoning = "No clear support or contradiction"

        confidence = min(1.0, confidence)

        result = ValidationResult(
            claim=claim,
            is_valid=is_valid,
            confidence=confidence,
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            source="knowledge_graph",
            reasoning=reasoning,
        )

        self.validation_log.append(result)
        return result

    def validate_prediction(
        self,
        prediction: str,
        market_question: str,
    ) -> ValidationResult:
        """Validate a prediction against knowledge graph."""
        # Combine prediction and market question for context
        full_claim = f"{market_question} — Prediction: {prediction}"
        return self.validate_claim(full_claim, "fact_check")

    def _analyze_against_node(self, claim: str, node: KnowledgeNode) -> dict:
        """Analyze a claim against a knowledge node."""
        claim_lower = claim.lower()
        content_lower = node.content.lower()

        # Simple keyword overlap analysis
        claim_words = set(claim_lower.split())
        content_words = set(content_lower.split())
        overlap = claim_words & content_words

        # Check for contradictions (simplified)
        contradiction_signals = ["not", "never", "false", "incorrect", "wrong"]
        has_contradiction = any(
            signal in claim_lower and signal not in content_lower
            for signal in contradiction_signals
        )

        return {
            "supports": len(overlap) > 3,
            "contradicts": has_contradiction,
            "evidence": f"Overlap: {len(overlap)} words with '{node.title}'",
        }

    def get_validation_stats(self) -> dict:
        """Validation statistics."""
        if not self.validation_log:
            return {"total": 0, "valid": 0, "invalid": 0, "avg_confidence": 0}

        valid = sum(1 for v in self.validation_log if v.is_valid)
        invalid = len(self.validation_log) - valid
        avg_conf = sum(v.confidence for v in self.validation_log) / len(self.validation_log)

        return {
            "total": len(self.validation_log),
            "valid": valid,
            "invalid": invalid,
            "avg_confidence": round(avg_conf, 2),
        }


class GraphValidationBridge:
    """
    BRIDGE between Knowledge Graph and Prediction Markets.
    
    This is the INTERACTION layer:
    
    Knowledge Graph → Validation Engine → Prediction Markets
          ↓                  ↓                    ↓
       Facts             Validation            Scores
       Context           Confidence            Leaderboard
       Relationships     Evidence              Learning
    
    The feedback loop:
    1. Agent makes prediction
    2. Validation checks against knowledge graph
    3. Confidence score assigned
    4. Market prices adjust
    5. Outcome determines accuracy
    6. Agent learns from validation
    7. Knowledge graph updated with new insights
    """

    def __init__(self, graph: KnowledgeGraph, validation: ValidationEngine):
        self.graph = graph
        self.validation = validation
        self.validation_points: list[ValidationPoint] = []

    def create_validation_point(
        self,
        claim: str,
        knowledge_node_id: str = "",
        validation_type: str = "fact_check",
    ) -> ValidationPoint:
        """Create a validation point."""
        vp = ValidationPoint(
            id=f"vp-{len(self.validation_points) + 1}",
            claim=claim,
            knowledge_node_id=knowledge_node_id,
            validation_type=validation_type,
        )
        self.validation_points.append(vp)
        return vp

    def validate_and_score(self, claim: str) -> dict:
        """Validate a claim and return scored result."""
        # Create validation point
        vp = self.create_validation_point(claim)

        # Validate against knowledge graph
        result = self.validation.validate_claim(claim)

        # Attach result to validation point
        vp.result = result

        # Score based on validation
        score = self._calculate_score(result)

        return {
            "claim": claim,
            "validation": {
                "is_valid": result.is_valid,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "supporting": len(result.supporting_evidence),
                "contradicting": len(result.contradicting_evidence),
            },
            "score": score,
            "validation_point_id": vp.id,
        }

    def validate_market_creation(self, question: str) -> dict:
        """Validate whether a market question should be created."""
        # Check knowledge graph for relevant context
        relevant = self.graph.search(question, limit=3)

        if not relevant:
            return {
                "question": question,
                "should_create": True,  # Novel topic = good market
                "confidence": 0.5,
                "reasoning": "No existing knowledge — novel topic",
            }

        # Check if question is answerable from existing knowledge
        is_answerable = any(
            question.lower() in node.content.lower()
            for node in relevant
        )

        if is_answerable:
            return {
                "question": question,
                "should_create": False,  # Already known = boring market
                "confidence": 0.8,
                "reasoning": "Answer already in knowledge graph",
            }

        return {
            "question": question,
            "should_create": True,  # Open question = good market
            "confidence": 0.7,
            "reasoning": "Open question with some context available",
        }

    def _calculate_score(self, result: ValidationResult) -> float:
        """Calculate score from validation result."""
        base = 0.5

        if result.is_valid:
            base += 0.2
        else:
            base -= 0.3

        # Adjust by confidence
        base *= result.confidence

        # Bonus for supporting evidence
        base += len(result.supporting_evidence) * 0.05

        # Penalty for contradicting evidence
        base -= len(result.contradicting_evidence) * 0.1

        return round(max(0.0, min(1.0, base)), 4)

    def get_bridge_stats(self) -> dict:
        """Bridge statistics."""
        return {
            "validation_points": len(self.validation_points),
            "graph_stats": self.graph.get_stats(),
            "validation_stats": self.validation.get_validation_stats(),
        }


# ─── Grokipedia Loader ─────────────────────────────────────────

class GrokipediaLoader:
    """
    Load knowledge from Grokipedia into the graph.
    
    Sources:
    - Python API (grokipedia-api)
    - HuggingFace dump
    - Web scrape
    """

    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph

    def load_from_api(self, topics: list[str]):
        """Load articles from Grokipedia API."""
        try:
            from grokipedia_api import GrokipediaClient
            client = GrokipediaClient()

            for topic in topics:
                try:
                    page = client.get_page(topic, include_content=True)
                    if page and "page" in page:
                        p = page["page"]
                        node = KnowledgeNode(
                            id=f"grok-{topic.lower().replace(' ', '_')}",
                            title=p.get("title", topic),
                            content=p.get("content", "")[:2000],
                            citations=[c.get("title", "") for c in p.get("citations", [])],
                            categories=p.get("categories", []),
                            source="grokipedia",
                        )
                        self.graph.add_node(node)
                        print(f"  ✅ Loaded: {node.title}")
                except Exception as e:
                    print(f"  ❌ Failed: {topic} — {e}")

        except ImportError:
            print("  ❌ grokipedia-api not installed. Run: pip install grokipedia-api")

    def load_from_huggingface(self, dataset: str = "htriedman/grokipedia-v0.1-dump"):
        """Load from HuggingFace dump."""
        try:
            from datasets import load_dataset
            ds = load_dataset(dataset, split="train")

            for item in ds:
                node = KnowledgeNode(
                    id=f"grok-{item.get('title', '').lower().replace(' ', '_')}",
                    title=item.get("title", ""),
                    content=item.get("content", "")[:2000],
                    source="grokipedia",
                )
                self.graph.add_node(node)

            print(f"  ✅ Loaded {len(ds)} articles from HuggingFace")

        except ImportError:
            print("  ❌ datasets not installed. Run: pip install datasets")
        except Exception as e:
            print(f"  ❌ HuggingFace load failed: {e}")

    def load_sample(self):
        """Load sample knowledge for testing."""
        samples = [
            KnowledgeNode(
                id="quantum-computing",
                title="Quantum Computing",
                content="Quantum computing uses quantum-mechanical phenomena such as superposition and entanglement to perform computation. A quantum bit (qubit) can exist in multiple states simultaneously.",
                categories=["technology", "physics"],
                source="sample",
            ),
            KnowledgeNode(
                id="bitcoin",
                title="Bitcoin",
                content="Bitcoin is a decentralized digital currency created in 2009 by Satoshi Nakamoto. It uses blockchain technology and has a fixed supply of 21 million coins.",
                categories=["crypto", "finance"],
                source="sample",
            ),
            KnowledgeNode(
                id="prediction-markets",
                title="Prediction Markets",
                content="Prediction markets are exchange-traded markets created for the purpose of trading the outcome of events. The market prices can be used to gauge the probability of events.",
                categories=["finance", "technology"],
                source="sample",
            ),
            KnowledgeNode(
                id="consciousness",
                title="Consciousness",
                content="Consciousness is the state of being aware of and able to think about one's own existence, sensations, thoughts, and surroundings. The nature of consciousness is one of the hardest problems in science.",
                categories=["philosophy", "science"],
                source="sample",
            ),
            KnowledgeNode(
                id="ai-agents",
                title="AI Agents",
                content="AI agents are autonomous software programs that can perceive their environment, make decisions, and take actions to achieve goals. They can learn, adapt, and collaborate with other agents.",
                categories=["technology", "ai"],
                source="sample",
            ),
        ]

        for node in samples:
            self.graph.add_node(node)

        # Add relationships
        self.graph.add_edge("ai-agents", "prediction-markets", "enables")
        self.graph.add_edge("ai-agents", "consciousness", "relates_to")
        self.graph.add_edge("quantum-computing", "ai-agents", "enhances")
        self.graph.add_edge("bitcoin", "prediction-markets", "used_in")

        print(f"  ✅ Loaded {len(samples)} sample nodes + {len(self.graph.edges)} edges")


# ─── Demo ───────────────────────────────────────────────────────

def demo():
    """Demo the knowledge graph + validation engine."""

    print("=" * 60)
    print("🌅 KNOWLEDGE GRAPH + VALIDATION ENGINE")
    print("=" * 60)

    # Create knowledge graph
    graph = KnowledgeGraph()
    loader = GrokipediaLoader(graph)
    loader.load_sample()

    print(f"\n📊 Graph: {graph.get_stats()}")

    # Create validation engine
    validator = ValidationEngine(graph)

    # Create bridge
    bridge = GraphValidationBridge(graph, validator)

    # Test validation
    claims = [
        "AI agents will replace most jobs by 2030",
        "Bitcoin has a fixed supply of 21 million coins",
        "Quantum computing uses qubits that can be in multiple states",
        "Prediction markets are unreliable for forecasting",
    ]

    print(f"\n🔍 Validation Results:")
    for claim in claims:
        result = bridge.validate_and_score(claim)
        status = "✅" if result["validation"]["is_valid"] else "❌"
        print(f"\n  {status} \"{claim}\"")
        print(f"     Valid: {result['validation']['is_valid']}")
        print(f"     Confidence: {result['validation']['confidence']:.0%}")
        print(f"     Score: {result['score']:.2f}")
        print(f"     Reason: {result['validation']['reasoning']}")

    # Market creation validation
    print(f"\n📊 Market Creation Validation:")
    questions = [
        "Will AI agents achieve human-level reasoning by 2028?",
        "Is Bitcoin a digital currency?",
        "Will quantum computing break encryption?",
    ]

    for q in questions:
        result = bridge.validate_market_creation(q)
        create = "✅ CREATE" if result["should_create"] else "❌ SKIP"
        print(f"\n  {create}: \"{q}\"")
        print(f"     Reason: {result['reasoning']}")

    print(f"\n📊 Bridge Stats: {bridge.get_bridge_stats()}")
    print("=" * 60)


if __name__ == "__main__":
    demo()
