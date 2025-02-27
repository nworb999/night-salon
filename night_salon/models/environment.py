from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional




@dataclass
class SubLocation: 
    """Represents a specific area within a main loaction (e.g. a seat, standing place)"""
    id: str
    name: str
    type: str
    occupied_by: Optional[str] = None

class SubLocationType(str, Enum):
    SEAT = "SEAT"
    STANDING_AREA = "STANDING_AREA"
    DESK = "DESK"
    STALL = "STALL"

class Location(str, Enum):
    HALLWAY = "HALLWAY"
    CONFERENCE_ROOM = "CONFERENCE_ROOM"
    WATER_COOLER = "WATER_COOLER"
    SMOKING_AREA = "SMOKING_AREA"
    CUBICLES = "CUBICLES"
    BATHROOM = "BATHROOM"

@dataclass
class LocationData:
    name: str
    type: Location
    sub_locations: Dict[str, SubLocation] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)
    valid: bool = False  # Track whether this location exists in Unity

def create_location_mapping():
    mapping = {}
    for location in Location:
        mapping[location.value] = LocationData(
            name=location.name,
            type=location
        )

    mapping[Location.CONFERENCE_ROOM.value].sub_locations = {
        "CHAIR_1": SubLocation(id="CHAIR_1", name="Chair 1", type=SubLocationType.SEAT),
        "CHAIR_2": SubLocation(id="CHAIR_2", name="Chair 2", type=SubLocationType.SEAT),
        "PODIUM": SubLocation(id="PODIUM", name = "Speaker", type=SubLocationType.STANDING_AREA)
    }

    mapping[Location.WATER_COOLER.value].sub_locations = {
        "POSITION_1": SubLocation(id="POSITION_1", name="Position1", type=SubLocationType.STANDING_AREA),
        "POSITION_2": SubLocation(id="POSITION_2", name="Position2", type=SubLocationType.STANDING_AREA),
    }

    mapping[Location.CUBICLES.value].sub_locations = {
        "DESK_1": SubLocation(id="DESK_1", name="Desk 1", type=SubLocationType.DESK),
        "DESK_2": SubLocation(id="DESK_2", name="Desk 2", type=SubLocationType.DESK),
        "DESK_3": SubLocation(id="DESK_3", name="Desk 3", type=SubLocationType.DESK),
    }

    mapping[Location.BATHROOM.value].sub_locations = {
        "STALL_1": SubLocation(id="STALL_1", name="Stall 1", type=SubLocationType.STALL),
        "STALL_2": SubLocation(id="STALL_2", name="Stall 2", type=SubLocationType.STALL),
    }

    mapping[Location.SMOKING_AREA.value].sub_locations = {
        "CORNER_1":SubLocation(id="CORNER_1", name="Corner 1", type=SubLocationType.STANDING_AREA),
        "CORNER_2":SubLocation(id="CORNER_2", name="Corner 2", type=SubLocationType.STANDING_AREA),
    }

    mapping[Location.HALLWAY.value].sub_locations = {
        "NORTH_END": SubLocation(id="NORTH_END", name = "North End", type=SubLocationType.STANDING_AREA),
        "SOUTH_END": SubLocation(id="SOUTH_END", name = "South End", type=SubLocationType.STANDING_AREA),
        "MIDDLE": SubLocation(id="MIDDLE", name="Middle", type=SubLocationType.STANDING_AREA)
    }

    return mapping

LOCATION_MAPPING = create_location_mapping()

@dataclass
class EnvironmentState:
    locations: Dict[str, LocationData] = field(default_factory=dict)
    cameras: list = field(default_factory=list)
    items: list = field(default_factory=list)
