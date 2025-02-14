from enum import Enum
from dataclasses import dataclass
from typing import List

@dataclass
class LocationData:
    type: 'Location'
    sub_locations: List[str]

class Location(str, Enum):
    HALLWAY = "HALLWAY"
    CONFERENCE_ROOM = "CONFERENCE_ROOM"
    WATER_COOLER = "WATER_COOLER"
    SMOKING_AREA = "SMOKING_AREA"
    CUBICLES = "CUBICLES"
    BATHROOM = "BATHROOM"

# Create mapping dynamically with empty sub-locations
LOCATION_MAPPING = {
    location.name: LocationData(location, []) 
    for location in Location
}

