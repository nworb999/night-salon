from enum import Enum
from dataclasses import dataclass, field
from typing import List


@dataclass
class EnvironmentState:
    locations: dict = field(default_factory=dict)
    cameras: list = field(default_factory=list)
    items: list = field(default_factory=list)


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
    sub_locations: List[str] = field(default_factory=list)

LOCATION_MAPPING = {
    location.name: LocationData(location, []) 
    for location in Location
}