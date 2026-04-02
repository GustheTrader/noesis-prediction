"""
Sovereign OS — NOESIS API

FastAPI endpoints for the prediction market platform.
All endpoints encrypted. All user data sovereign.

Usage:
    uvicorn api:app --host 0.0.0.0 --port 8000
"""

import os
import time
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import our modules
from market_engine import MarketEngine
from models import MarketCategory, MarketStatus
from api_gateway import SovereignAPIGateway, SovereignAuth, SovereignEncryption
from smart_router import SmartRouter, QueryExecutor
from database import SovereignDatabase, GeminiEmbedding, VectorMemory


# ─── Configuration ──────────────────────────────────────────────

INSTANCE_ID = os.getenv("INSTANCE_ID", "noesis-api-1")
SECRET_KEY = os.getenv("SECRET_KEY", "sovereign-os-secret-key-change-me")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")


# ─── App Setup ──────────────────────────────────────────────────

app = FastAPI(
    title="Sovereign OS — NOESIS API",
    description="Encrypted prediction market platform for the Wrong Room Collective",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
engine = MarketEngine()
gateway = SovereignAPIGateway(INSTANCE_ID, SECRET_KEY)
auth = SovereignAuth(INSTANCE_ID, SECRET_KEY)
router = SmartRouter()


# ─── Pydantic Models ───────────────────────────────────────────

class MarketCreate(BaseModel):
    question: str
    description: str = ""
    category: str = "reality_os"
    closes_in_days: int = 30
    tags: list[str] = Field(default_factory=list)

class PredictionSubmit(BaseModel):
    market_id: str
    prediction: bool
    confidence: float = Field(ge=0.0, le=1.0)
    stake: float = 1.0
    reasoning: str = ""

class MarketResolve(BaseModel):
    market_id: str
    outcome: bool

class QueryRequest(BaseModel):
    query: str
    limit: int = 10

class AuthRequest(BaseModel):
    instance_id: str

class EncryptedRequest(BaseModel):
    ciphertext: str
    signature: str
    timestamp: float
    sender: str = ""


# ─── Auth Middleware ────────────────────────────────────────────

def verify_token(authorization: str = Header(None)) -> dict:
    """Verify sovereign auth token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="No auth token provided")

    token = authorization.replace("Bearer ", "")
    payload = auth.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return payload


# ─── Health Check ───────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "instance": INSTANCE_ID,
        "timestamp": time.time(),
        "encryption": "AES-128-CBC + HMAC",
    }


@app.get("/status")
async def status():
    """System status."""
    return {
        "instance": INSTANCE_ID,
        "markets": {
            "open": len(engine.get_open_markets()),
            "total": len(engine.markets),
        },
        "predictions": sum(len(p) for p in engine.predictions.values()),
        "leaderboard": len(engine.get_leaderboard()),
        "encryption": {
            "type": "Fernet (AES-128-CBC + HMAC)",
            "enabled": True,
        },
    }


# ─── Auth Endpoints ─────────────────────────────────────────────

@app.post("/auth/token")
async def create_token(req: AuthRequest):
    """Create sovereign auth token."""
    token = auth.create_token(expires_in=86400)  # 24 hours
    return {
        "token": token,
        "instance": INSTANCE_ID,
        "expires_in": 86400,
    }


# ─── Market Endpoints ───────────────────────────────────────────

@app.get("/markets")
async def list_markets(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
):
    """List markets with optional filters."""
    markets = list(engine.markets.values())

    if status:
        markets = [m for m in markets if m.status.value == status]
    if category:
        markets = [m for m in markets if m.category.value == category]

    return {
        "markets": [
            {
                "id": m.id,
                "question": m.question,
                "category": m.category.value,
                "status": m.status.value,
                "yes_price": m.yes_price,
                "no_price": m.no_price,
                "total_volume": m.total_volume,
                "closes_at": m.closes_at.isoformat() if m.closes_at else None,
            }
            for m in markets[:limit]
        ],
        "total": len(markets),
    }


@app.get("/markets/{market_id}")
async def get_market(market_id: str):
    """Get market details."""
    market = engine.markets.get(market_id)
    if not market:
        raise HTTPException(status_code=404, detail="Market not found")

    preds = engine.predictions.get(market_id, [])

    return {
        "id": market.id,
        "question": market.question,
        "description": market.description,
        "category": market.category.value,
        "status": market.status.value,
        "yes_price": market.yes_price,
        "no_price": market.no_price,
        "total_volume": market.total_volume,
        "predictions_count": len(preds),
        "closes_at": market.closes_at.isoformat() if market.closes_at else None,
        "created_at": market.created_at.isoformat(),
    }


@app.post("/markets")
async def create_market(
    req: MarketCreate,
    user: dict = Depends(verify_token),
):
    """Create a new market. Requires auth."""
    try:
        category = MarketCategory(req.category)
    except ValueError:
        category = MarketCategory.REALITY_OS

    market = engine.create_market(
        question=req.question,
        description=req.description,
        category=category,
        created_by=user.get("instance", "unknown"),
        closes_in_days=req.closes_in_days,
        tags=req.tags,
    )

    return {
        "id": market.id,
        "question": market.question,
        "status": "created",
    }


@app.post("/markets/{market_id}/resolve")
async def resolve_market(
    market_id: str,
    req: MarketResolve,
    user: dict = Depends(verify_token),
):
    """Resolve a market. Requires auth."""
    results = engine.resolve_market(market_id, req.outcome)

    return {
        "market_id": market_id,
        "outcome": req.outcome,
        "predictions_scored": len(results),
        "results": [
            {
                "member_id": r.member_id,
                "correct": r.correct,
                "score": r.score,
            }
            for r in results
        ],
    }


# ─── Prediction Endpoints ───────────────────────────────────────

@app.post("/predictions")
async def submit_prediction(
    req: PredictionSubmit,
    user: dict = Depends(verify_token),
):
    """Submit a prediction. Requires auth."""
    pred = engine.submit_prediction(
        market_id=req.market_id,
        member_id=user.get("instance", "unknown"),
        prediction=req.prediction,
        confidence=req.confidence,
        stake=req.stake,
        reasoning=req.reasoning,
    )

    if not pred:
        raise HTTPException(status_code=400, detail="Market not found or closed")

    market = engine.markets.get(req.market_id)

    return {
        "prediction_id": pred.id,
        "market_id": req.market_id,
        "prediction": "yes" if pred.prediction else "no",
        "confidence": pred.confidence,
        "market_prices": {
            "yes": market.yes_price if market else 0.5,
            "no": market.no_price if market else 0.5,
        },
    }


@app.get("/predictions/{member_id}")
async def get_member_predictions(member_id: str):
    """Get predictions by member."""
    accuracy = engine.get_member_accuracy(member_id)

    return {
        "member_id": member_id,
        "accuracy": accuracy,
    }


# ─── Leaderboard ────────────────────────────────────────────────

@app.get("/leaderboard")
async def get_leaderboard(limit: int = 20):
    """Get leaderboard."""
    board = engine.get_leaderboard(limit)

    return {
        "leaderboard": [
            {
                "rank": i + 1,
                "member_id": entry["member_id"],
                "accuracy": entry["accuracy"],
                "total": entry["total"],
                "correct": entry["correct"],
            }
            for i, entry in enumerate(board)
        ],
    }


# ─── Smart Router (Query) ───────────────────────────────────────

@app.post("/query")
async def smart_query(
    req: QueryRequest,
    user: dict = Depends(verify_token),
):
    """Smart query with automatic routing."""
    route = router.route(req.query)

    return {
        "query": req.query,
        "route": {
            "type": route.query_type.value,
            "backend": route.backend,
            "confidence": route.confidence,
            "reason": route.reason,
        },
        "message": "Connect to PostgreSQL and Qdrant for full results",
    }


# ─── Encrypted Communication ────────────────────────────────────

@app.post("/encrypt")
async def encrypt_message(
    message: str,
    user: dict = Depends(verify_token),
):
    """Encrypt a message for transmission."""
    payload = gateway.encryption.encrypt(message, sender_id=INSTANCE_ID)
    wire = gateway.encryption.to_wire(payload)

    return {
        "encrypted": True,
        "wire": wire,
        "size": len(wire),
    }


@app.post("/decrypt")
async def decrypt_message(
    req: EncryptedRequest,
    user: dict = Depends(verify_token),
):
    """Decrypt a received message."""
    payload = gateway.encryption.from_wire(req.ciphertext)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid encrypted payload")

    message = gateway.encryption.decrypt(payload)
    if not message:
        raise HTTPException(status_code=401, detail="Decryption failed or message tampered")

    return {
        "decrypted": True,
        "message": message,
    }


# ─── ATA Mesh Communication ─────────────────────────────────────

@app.post("/mesh/send")
async def mesh_send(
    recipient: str,
    message: str,
    user: dict = Depends(verify_token),
):
    """Send message to another instance in the mesh."""
    wire = gateway.send(message, recipient)

    if not wire:
        raise HTTPException(status_code=500, detail="Failed to encrypt message")

    return {
        "sent": True,
        "recipient": recipient,
        "wire_size": len(wire),
    }


@app.post("/mesh/broadcast")
async def mesh_broadcast(
    message: str,
    user: dict = Depends(verify_token),
):
    """Broadcast to all trusted instances."""
    results = gateway.broadcast(message)

    return {
        "broadcast": True,
        "recipients": list(results.keys()),
        "count": len(results),
    }


# ─── System Endpoints ───────────────────────────────────────────

@app.get("/encryption/status")
async def encryption_status():
    """Encryption status."""
    return {
        "enabled": True,
        "type": "Fernet (AES-128-CBC + HMAC)",
        "key_derivation": "PBKDF2HMAC-SHA256",
        "replay_protection": "5-minute timestamp window",
        "auth": "HMAC-SHA256 signature verification",
    }


@app.get("/docs/summary")
async def api_summary():
    """API summary."""
    return {
        "name": "Sovereign OS — NOESIS API",
        "version": "0.1.0",
        "endpoints": {
            "markets": "GET/POST /markets",
            "predictions": "POST /predictions",
            "leaderboard": "GET /leaderboard",
            "query": "POST /query (smart router)",
            "encrypt": "POST /encrypt",
            "decrypt": "POST /decrypt",
            "mesh_send": "POST /mesh/send",
            "mesh_broadcast": "POST /mesh/broadcast",
        },
        "auth": "Sovereign tokens (HMAC-SHA256)",
        "encryption": "Fernet (AES-128-CBC + HMAC)",
    }
