from typing import Dict, List, Optional
from pydantic import BaseModel
from dataclasses import field


class AgentEvent(BaseModel):
    """Base class for all agent events"""

    type: str
    agent_id: str


class AreaData(BaseModel):
    """Represents area data with a name and list of locations"""

    area_name: str
    locations: List[str] = []


class SetupEvent(BaseModel):
    """Event for initial setup of the environment"""

    type: str = "setup"
    agent_ids: List[str] = []
    areas: List[AreaData] = []
    cameras: List[str] = []
    items: List[str] = []


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
