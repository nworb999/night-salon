from enum import Enum

class Location(str, Enum):
    HALLWAY = "HALLWAY"
    CONFERENCE_ROOM = "CONFERENCE_ROOM"
    WATER_COOLER = "WATER_COOLER"
    SMOKING_AREA = "SMOKING_AREA"
    CUBICLES = "CUBICLES"
    BATHROOM = "BATHROOM"

# Create a dictionary mapping location names to enum values
LOCATION_MAPPING = {location.name: location for location in Location}

