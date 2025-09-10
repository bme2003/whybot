from pydantic import BaseModel, Field
from typing import List, Dict, Tuple, Optional

Coord = Tuple[int, int]

class Weights(BaseModel):
    time: float = 1.0
    risk: float = 1.0
    energy: float = 0.5
    uncertainty: float = 0.3
    memory: float = 1.0

class PlanRequest(BaseModel):
    width: int = 32
    height: int = 24
    start: Coord = (1, 1)
    goal: Coord = (30, 20)
    obstacles: List[Coord] = Field(default_factory=list)
    hazards: List[Coord] = Field(default_factory=list)  # prior bumps (hazard memory)
    weights: Weights = Weights()
    seed: Optional[int] = 7

class TermBreakdown(BaseModel):
    time: float
    risk: float
    energy: float
    uncertainty: float
    memory: float

class PlanResponse(BaseModel):
    path: List[Coord]
    found: bool
    total_cost: float
    steps: int
    breakdown: TermBreakdown
    percentages: Dict[str, float]
    explanation: str
