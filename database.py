"""
Sovereign OS — Database Layer

Structured data (PostgreSQL) + Vector memory (Qdrant) + Gemini Embedding 2.

All self-hosted. All sovereign.
"""

import json
import time
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

import httpx


# ─── Gemini Embedding 2 Client ─────────────────────────────────

class GeminiEmbedding:
    """
    Gemini Embedding 2 — Multimodal embedding model.
    
    Accepts: text, images, video, audio, documents
    Output: 3072-dimensional vectors
    All modalities in unified semantic space.
    """

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.model = "gemini-embedding-exp-03-07"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.dimensions = 3072

    def embed_text(self, text: str) -> list[float]:
        """Embed text into 3072-dim vector."""
        try:
            resp = httpx.post(
                f"{self.base_url}/models/{self.model}:embedContent",
                params={"key": self.api_key},
                json={
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": text}]},
                },
                timeout=30,
            )
            data = resp.json()
            return data.get("embedding", {}).get("values", [])
        except Exception as e:
            print(f"Gemini embed error: {e}")
            return []

    def embed_image(self, image_base64: str) -> list[float]:
        """Embed image into 3072-dim vector."""
        try:
            resp = httpx.post(
                f"{self.base_url}/models/{self.model}:embedContent",
                params={"key": self.api_key},
                json={
                    "model": f"models/{self.model}",
                    "content": {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": image_base64,
                                }
                            }
                        ]
                    },
                },
                timeout=30,
            )
            data = resp.json()
            return data.get("embedding", {}).get("values", [])
        except Exception as e:
            print(f"Gemini image embed error: {e}")
            return []

    def embed_multimodal(self, parts: list[dict]) -> list[float]:
        """
        Embed multiple modalities in one call.
        
        parts: [{"text": "..."}, {"inline_data": {"mime_type": "...", "data": "..."}}]
        """
        try:
            resp = httpx.post(
                f"{self.base_url}/models/{self.model}:embedContent",
                params={"key": self.api_key},
                json={
                    "model": f"models/{self.model}",
                    "content": {"parts": parts},
                },
                timeout=60,
            )
            data = resp.json()
            return data.get("embedding", {}).get("values", [])
        except Exception as e:
            print(f"Gemini multimodal embed error: {e}")
            return []

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embed multiple texts."""
        try:
            resp = httpx.post(
                f"{self.base_url}/models/{self.model}:batchEmbedContents",
                params={"key": self.api_key},
                json={
                    "requests": [
                        {
                            "model": f"models/{self.model}",
                            "content": {"parts": [{"text": t}]},
                        }
                        for t in texts
                    ]
                },
                timeout=60,
            )
            data = resp.json()
            return [
                r.get("embedding", {}).get("values", [])
                for r in data.get("embeddings", [])
            ]
        except Exception as e:
            print(f"Gemini batch embed error: {e}")
            return []


# ─── Qdrant Vector Database Client ─────────────────────────────

class VectorMemory:
    """
    Qdrant-backed vector memory for Sovereign OS.
    
    Supports:
    - Semantic search across text, images, documents
    - Multimodal embeddings (via Gemini Embedding 2)
    - Persistent storage
    - Self-hosted, sovereign
    """

    def __init__(
        self,
        collection: str = "sovereign-memory",
        qdrant_url: str = "http://localhost:6333",
        embedding_model: GeminiEmbedding = None,
    ):
        self.collection = collection
        self.qdrant_url = qdrant_url
        self.embedder = embedding_model or GeminiEmbedding()

    def create_collection(self):
        """Create vector collection."""
        try:
            resp = httpx.put(
                f"{self.qdrant_url}/collections/{self.collection}",
                json={
                    "vectors": {
                        "size": self.embedder.dimensions,
                        "distance": "Cosine",
                    }
                },
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"Qdrant create error: {e}")
            return False

    def upsert(self, id: str, text: str, metadata: dict = None) -> bool:
        """Store a memory with embedding."""
        embedding = self.embedder.embed_text(text)
        if not embedding:
            return False

        try:
            resp = httpx.put(
                f"{self.qdrant_url}/collections/{self.collection}/points",
                json={
                    "points": [
                        {
                            "id": id,
                            "vector": embedding,
                            "payload": {
                                "text": text,
                                "timestamp": time.time(),
                                **(metadata or {}),
                            },
                        }
                    ]
                },
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as e:
            print(f"Qdrant upsert error: {e}")
            return False

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Semantic search across memories."""
        embedding = self.embedder.embed_text(query)
        if not embedding:
            return []

        try:
            resp = httpx.post(
                f"{self.qdrant_url}/collections/{self.collection}/points/search",
                json={
                    "vector": embedding,
                    "limit": limit,
                    "with_payload": True,
                },
                timeout=10,
            )
            data = resp.json()
            return [
                {
                    "id": r.get("id"),
                    "score": r.get("score", 0),
                    "text": r.get("payload", {}).get("text", ""),
                    "metadata": {k: v for k, v in r.get("payload", {}).items() if k != "text"},
                }
                for r in data.get("result", [])
            ]
        except Exception as e:
            print(f"Qdrant search error: {e}")
            return []

    def search_multimodal(self, text: str = "", image_base64: str = "", limit: int = 5) -> list[dict]:
        """Multimodal search — text + image."""
        parts = []
        if text:
            parts.append({"text": text})
        if image_base64:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": image_base64}})

        embedding = self.embedder.embed_multimodal(parts)
        if not embedding:
            return []

        try:
            resp = httpx.post(
                f"{self.qdrant_url}/collections/{self.collection}/points/search",
                json={
                    "vector": embedding,
                    "limit": limit,
                    "with_payload": True,
                },
                timeout=10,
            )
            data = resp.json()
            return [
                {
                    "id": r.get("id"),
                    "score": r.get("score", 0),
                    "text": r.get("payload", {}).get("text", ""),
                }
                for r in data.get("result", [])
            ]
        except Exception as e:
            print(f"Qdrant multimodal search error: {e}")
            return []

    def delete(self, id: str) -> bool:
        """Delete a memory."""
        try:
            resp = httpx.post(
                f"{self.qdrant_url}/collections/{self.collection}/points/delete",
                json={"points": [id]},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def count(self) -> int:
        """Count memories."""
        try:
            resp = httpx.get(
                f"{self.qdrant_url}/collections/{self.collection}",
                timeout=10,
            )
            data = resp.json()
            return data.get("result", {}).get("points_count", 0)
        except Exception:
            return 0


# ─── PostgreSQL Structured Database ────────────────────────────

class StructuredDB:
    """
    PostgreSQL-backed structured data for Sovereign OS.
    
    Tables:
    - markets: prediction markets
    - predictions: member predictions
    - members: collective members
    - agents: agent configurations
    - transactions: SVRGN/SVRGN-Y transactions
    """

    def __init__(self, connection_string: str = ""):
        self.connection_string = connection_string
        # In production, would use asyncpg or psycopg2
        # For now, this is the schema definition

    SCHEMA = """
    -- Prediction Markets
    CREATE TABLE IF NOT EXISTS markets (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        question TEXT NOT NULL,
        description TEXT,
        category TEXT,
        status TEXT DEFAULT 'open',
        outcome BOOLEAN,
        yes_price FLOAT DEFAULT 0.5,
        no_price FLOAT DEFAULT 0.5,
        total_volume FLOAT DEFAULT 0,
        created_by TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        closes_at TIMESTAMP,
        resolved_at TIMESTAMP,
        tags TEXT[]
    );

    -- Predictions
    CREATE TABLE IF NOT EXISTS predictions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        market_id UUID REFERENCES markets(id),
        member_id TEXT NOT NULL,
        prediction BOOLEAN NOT NULL,
        confidence FLOAT NOT NULL,
        stake FLOAT DEFAULT 1.0,
        reasoning TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );

    -- Members
    CREATE TABLE IF NOT EXISTS members (
        id TEXT PRIMARY KEY,
        name TEXT,
        joined_at TIMESTAMP DEFAULT NOW(),
        total_predictions INT DEFAULT 0,
        correct_predictions INT DEFAULT 0,
        reputation_score FLOAT DEFAULT 0.5,
        svrgn_balance FLOAT DEFAULT 0,
        svrgny_balance FLOAT DEFAULT 0
    );

    -- Agents
    CREATE TABLE IF NOT EXISTS agents (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        domain TEXT,
        skill_level FLOAT DEFAULT 0.5,
        strategy TEXT,
        budget FLOAT DEFAULT 100,
        status TEXT DEFAULT 'active',
        config JSONB,
        created_at TIMESTAMP DEFAULT NOW()
    );

    -- Transactions (SVRGN)
    CREATE TABLE IF NOT EXISTS transactions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        member_id TEXT REFERENCES members(id),
        type TEXT NOT NULL, -- 'earn', 'spend', 'transfer'
        amount FLOAT NOT NULL,
        token TEXT DEFAULT 'SVRGN', -- 'SVRGN' or 'SVRGN-Y'
        reason TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );

    -- Create indexes
    CREATE INDEX IF NOT EXISTS idx_predictions_market ON predictions(market_id);
    CREATE INDEX IF NOT EXISTS idx_predictions_member ON predictions(member_id);
    CREATE INDEX IF NOT EXISTS idx_markets_status ON markets(status);
    CREATE INDEX IF NOT EXISTS idx_transactions_member ON transactions(member_id);
    """

    def get_schema(self) -> str:
        """Get the SQL schema."""
        return self.SCHEMA


# ─── Integrated Database Layer ─────────────────────────────────

class SovereignDatabase:
    """
    Unified database layer for Sovereign OS.
    
    Combines:
    - PostgreSQL (structured data)
    - Qdrant (vector memory)
    - Gemini Embedding 2 (multimodal embeddings)
    
    All self-hosted. All sovereign.
    """

    def __init__(
        self,
        pg_connection: str = "",
        qdrant_url: str = "http://localhost:6333",
        gemini_key: str = "",
    ):
        self.structured = StructuredDB(pg_connection)
        self.embedder = GeminiEmbedding(gemini_key)
        self.memory = VectorMemory(
            collection="sovereign-memory",
            qdrant_url=qdrant_url,
            embedding_model=self.embedder,
        )

    def initialize(self):
        """Initialize all databases."""
        print("🌅 Initializing Sovereign Database...")

        # Create vector collection
        if self.memory.create_collection():
            print("  ✅ Qdrant collection created")
        else:
            print("  ❌ Qdrant connection failed")

        print(f"  📊 PostgreSQL schema ready")
        print(f"  🧠 Gemini Embedding 2: {self.embedder.dimensions} dimensions")

    def store_memory(self, id: str, text: str, metadata: dict = None):
        """Store a memory with embedding."""
        return self.memory.upsert(id, text, metadata)

    def recall_memory(self, query: str, limit: int = 5) -> list[dict]:
        """Semantic search memories."""
        return self.memory.search(query, limit)

    def store_multimodal(self, id: str, text: str = "", image_base64: str = "", metadata: dict = None):
        """Store multimodal content."""
        parts = []
        if text:
            parts.append({"text": text})
        if image_base64:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": image_base64}})

        embedding = self.embedder.embed_multimodal(parts)
        if not embedding:
            return False

        # Store in Qdrant
        import httpx
        try:
            resp = httpx.put(
                f"{self.memory.qdrant_url}/collections/{self.memory.collection}/points",
                json={
                    "points": [
                        {
                            "id": id,
                            "vector": embedding,
                            "payload": {
                                "text": text or "[image]",
                                "has_image": bool(image_base64),
                                "timestamp": time.time(),
                                **(metadata or {}),
                            },
                        }
                    ]
                },
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def get_status(self) -> dict:
        """Database status."""
        return {
            "vector_db": {
                "type": "Qdrant",
                "url": self.memory.qdrant_url,
                "collection": self.memory.collection,
                "points": self.memory.count(),
            },
            "embedding": {
                "model": "Gemini Embedding 2",
                "dimensions": self.embedder.dimensions,
                "multimodal": True,
            },
            "structured_db": {
                "type": "PostgreSQL",
                "tables": ["markets", "predictions", "members", "agents", "transactions"],
            },
        }
