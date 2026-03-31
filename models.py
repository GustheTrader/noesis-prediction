"""
NOESIS Prediction Market — Data Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class MarketStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"


class MarketCategory(Enum):
    REALITY_OS = "reality_os"
    MACRO = "macro"
    PERSONAL = "personal"
    WRONG_ROOM = "wrong_room"


@dataclass
class Member:
    """A member of the Wrong Room Collective."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    joined: datetime = field(default_factory=datetime.utcnow)
    total_predictions: int = 0
    correct_predictions: int = 0
    reputation_score: float = 0.5  # 0.0 - 1.0
    domains: dict = field(default_factory=dict)  # domain -> accuracy


@dataclass
class Market:
    """A prediction market."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    description: str = ""
    category: MarketCategory = MarketCategory.REALITY_OS
    created_by: str = ""  # member id
    created_at: datetime = field(default_factory=datetime.utcnow)
    closes_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    status: MarketStatus = MarketStatus.OPEN
    outcome: Optional[bool] = None  # True = yes, False = no
    yes_price: float = 0.5  # Current implied probability
    no_price: float = 0.5
    total_volume: float = 0.0
    tags: list = field(default_factory=list)


@dataclass
class Prediction:
    """A member's prediction on a market."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    market_id: str = ""
    member_id: str = ""
    prediction: bool = True  # True = yes, False = no
    confidence: float = 0.5  # 0.0 - 1.0
    stake: float = 1.0  # Amount wagered (play-money default)
    created_at: datetime = field(default_factory=datetime.utcnow)
    reasoning: str = ""  # Why they believe this


@dataclass
class PredictionResult:
    """Outcome of a prediction."""
    prediction_id: str = ""
    market_id: str = ""
    member_id: str = ""
    predicted: bool = True
    actual: bool = True
    confidence: float = 0.5
    score: float = 0.0  # Accuracy score
    correct: bool = False


@dataclass
class Leaderboard:
    """Collective leaderboard."""
    period: str = "all_time"  # "daily", "weekly", "monthly", "all_time"
    top_predictors: list = field(default_factory=list)
    most_improved: list = field(default_factory=list)
    best_calibrated: list = field(default_factory=list)
    wrong_room_award: str = ""  # Best against-the-grain prediction
