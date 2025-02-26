from typing import Dict, List, Optional
from pydantic import BaseModel
from dataclasses import field

class AgentEvent(BaseModel):
    """Base class for all agent events"""
    type: str
    agent_id: str

class SetupEvent(BaseModel):
    agent_ids: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    cameras: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)  

class LocationReachedEvent(AgentEvent):
    """Event when an agent reaches a new location"""
    agent_id: str = ""
    location_name: str = ""
    coordinates: List[float] = field(default_factory=list)
    sub_location: Optional[str] = None

class ProximityEvent(AgentEvent):
    """Event when agents come in proximity"""
    target_id: str = ""
    distance: float = ""
    event_type: str = ""
    distance: float = 0.0
