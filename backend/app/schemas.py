from typing import Dict, List, Optional

from pydantic import BaseModel


class TimeWindow(BaseModel):
    start: int
    end: int


class Objectives(BaseModel):
    maximize_completed: bool = True
    minimize_disruption: bool = True
    minimize_blocks: bool = True
    prioritize_critical: bool = True


class Conditions(BaseModel):
    block_window: TimeWindow
    crew_windows: Dict[str, TimeWindow]
    high_priority_trains: List[str]
    train_delays: Dict[str, int] = {}


class OptimizeRequest(BaseModel):
    objectives: Objectives = Objectives()
    conditions: Optional[Conditions] = None
