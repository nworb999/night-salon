from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Location:
    """Represents a specific position within an area (e.g. a seat, standing place)"""

    id: str
    name: str
    type: int
    occupied_by: str = None
    coordinates: list = None


class LocationType(str, Enum):
    SEAT = "SEAT"
    STANDING_AREA = "STANDING_AREA"
    DESK = "DESK"
    STALL = "STALL"


class Area(str, Enum):
    HALLWAY = "HALLWAY"
    CONFERENCE_ROOM = "CONFERENCE_ROOM"
    WATER_COOLER = "WATER_COOLER"
    SMOKING_AREA = "SMOKING_AREA"
    CUBICLES = "CUBICLES"
    BATHROOM = "BATHROOM"


@dataclass
class AreaData:
    name: str
    type: Area
    locations: Dict[str, Location] = field(default_factory=dict)
    agents: List[str] = field(default_factory=list)
    valid: bool = False  # Track whether this area exists in Unity


# Initialize empty area mapping (will be populated during setup)
LOCATION_MAPPING = {}


@dataclass
class EnvironmentState:
    areas: Dict[str, AreaData] = field(default_factory=dict)
    cameras: list = field(default_factory=list)
    items: list = field(default_factory=list)
