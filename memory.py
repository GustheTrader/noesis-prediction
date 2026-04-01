"""
Persistent Semantic Memory — Experience distillation and transfer.

Reality OS Principle: Emotional memory runs the show.
The agent remembers what matters and distills lessons over time.
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class Memory:
    """A single memory entry."""
    content: str
    memory_type: str  # "episodic" | "semantic" | "procedural"
    importance: float = 0.5  # 0.0 - 1.0
    timestamp: float = field(default_factory=time.time)
    tags: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class PersistentMemory:
    """
    Memory system that persists across sessions and distills over time.
    
    Three types:
    - Episodic: "what happened" (specific experiences)
    - Semantic: "what I know" (distilled knowledge)
    - Procedural: "how to do" (learned skills)
    """

    def __init__(self, storage_path: str = "memory.json"):
        self.storage_path = Path(storage_path)
        self.episodic: list[Memory] = []
        self.semantic: list[Memory] = []
        self.procedural: list[Memory] = []
        self._load()

    def _load(self):
        """Load memories from disk."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                self.episodic = [Memory(**m) for m in data.get("episodic", [])]
                self.semantic = [Memory(**m) for m in data.get("semantic", [])]
                self.procedural = [Memory(**m) for m in data.get("procedural", [])]
            except Exception:
                pass  # Start fresh if corrupted

    def save(self):
        """Persist memories to disk."""
        data = {
            "episodic": [vars(m) for m in self.episodic[-500:]],  # Keep last 500
            "semantic": [vars(m) for m in self.semantic],
            "procedural": [vars(m) for m in self.procedural],
        }
        self.storage_path.write_text(json.dumps(data, indent=2))

    def remember(self, content: str, memory_type: str = "episodic",
                 importance: float = 0.5, tags: list = None):
        """Store a new memory."""
        mem = Memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
        )
        if memory_type == "episodic":
            self.episodic.append(mem)
        elif memory_type == "semantic":
            self.semantic.append(mem)
        elif memory_type == "procedural":
            self.procedural.append(mem)

    def recall(self, query: str, memory_type: str = None, limit: int = 5) -> list[Memory]:
        """Retrieve relevant memories (simple keyword matching for now)."""
        all_memories = []
        if memory_type is None or memory_type == "episodic":
            all_memories.extend(self.episodic)
        if memory_type is None or memory_type == "semantic":
            all_memories.extend(self.semantic)
        if memory_type is None or memory_type == "procedural":
            all_memories.extend(self.procedural)

        # Score by relevance (keyword overlap) and importance
        query_words = set(query.lower().split())
        scored = []
        for mem in all_memories:
            mem_words = set(mem.content.lower().split())
            overlap = len(query_words & mem_words)
            score = overlap * mem.importance
            if score > 0:
                scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]

    def distill(self):
        """
        The Memory Maintenance process.
        
        Review recent episodic memories → extract patterns → store as semantic knowledge.
        This is the accountability loop applied to memory.
        """
        if len(self.episodic) < 10:
            return

        # Find patterns in recent memories
        recent = self.episodic[-50:]
        patterns = {}

        for mem in recent:
            for tag in mem.tags:
                if tag not in patterns:
                    patterns[tag] = []
                patterns[tag].append(mem.content)

        # Create semantic memories from patterns
        for tag, contents in patterns.items():
            if len(contents) >= 3:
                summary = f"Pattern observed: '{tag}' appears in {len(contents)} experiences. Examples: {'; '.join(contents[:3])}"
                existing = [m for m in self.semantic if tag in m.tags]
                if not existing:
                    self.remember(summary, memory_type="semantic", importance=0.7, tags=[tag])

    def get_status(self) -> dict:
        """Memory system status."""
        return {
            "episodic_count": len(self.episodic),
            "semantic_count": len(self.semantic),
            "procedural_count": len(self.procedural),
            "total": len(self.episodic) + len(self.semantic) + len(self.procedural),
        }
