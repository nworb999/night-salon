from typing import List, Optional
from pydantic import BaseModel

class AgentEvent(BaseModel):
    """Base class for all agent events"""
    type: str
    agent_id: str

class SetupEvent(AgentEvent):
    """Initialization event for environment setup"""
    agent_ids: List[str]
    locations: List[str]
    cameras: List[str]
    items: List[str]

class LocationReachedEvent(AgentEvent):
    """Event when an agent reaches a new location"""
    location_name: str
    coordinates: Optional[tuple] = None

class ProximityEvent(AgentEvent):
    """Event when agents come in proximity"""
    target_id: str
    distance: float
    event_type: str  # 'enter' or 'exit'
