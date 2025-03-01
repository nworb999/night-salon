from typing import Dict, List, Optional
from pydantic import BaseModel
from dataclasses import dataclass, field


class AgentEvent(BaseModel):
    """Base class for all agent events"""

    type: str
    agent_id: str


@dataclass
class LocationData:
    location_name: str
    coordinates: list = None


@dataclass
class AreaData:
    area_name: str
    locations: list = field(default_factory=list)


@dataclass
class SetupEvent:
    type: str = "setup"
    agent_ids: list = field(default_factory=list)
    areas: list[AreaData] = field(default_factory=list)
    cameras: list = field(default_factory=list)
    items: list = field(default_factory=list)


class LocationReachedEvent(AgentEvent):
    """Event when an agent reaches a new location"""

    agent_id: str = ""
    location_name: str = ""
    coordinates: List[float] = []
    sub_location: Optional[str] = None


class ProximityEvent(AgentEvent):
    """Event when agents come in proximity"""

    target_id: str = ""
    event_type: str = ""
    distance: float = 0.0
