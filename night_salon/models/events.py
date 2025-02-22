from typing import List, Optional
from pydantic import BaseModel, Field

class AgentEvent(BaseModel):
    """Base class for all agent events"""
    type: str
    agent_id: str

class SetupEvent(BaseModel):
    agent_ids: List[str]  # Matches C# 'agent_ids' field
    locations: List[str]
    cameras: List[str]
    items: List[str] = Field(default_factory=list)  # Make optional with empty list default 

class LocationReachedEvent(AgentEvent):
    """Event when an agent reaches a new location"""
    location_name: str
    coordinates: Optional[tuple] = None

class ProximityEvent(AgentEvent):
    """Event when agents come in proximity"""
    target_id: str
    distance: float
    event_type: str  # 'enter' or 'exit'
