from pydantic import BaseModel
from dataclasses import dataclass, field
from enum import Enum, auto
    

class Location(str, Enum):
    HALLWAY = "HALLWAY"
    CONFERENCE_ROOM = "CONFERENCE_ROOM"
    WATER_COOLER = "WATER_COOLER"
    SMOKING_AREA = "SMOKING_AREA"
    CUBICLES = "CUBICLES"
    BATHROOM = "BATHROOM"


class Action(Enum):
    WALK = auto()
    CHAT = auto()
    WORK = auto()
    MEETING = auto()
    PRESENT = auto()
    LISTEN = auto()
    PHONE_CALL = auto()
    DRINK = auto()
    USE_BATHROOM = auto()
    SMOKE = auto()
    REST = auto()


@dataclass
class Agent:
    id: str
    location: Location = Location.HALLWAY
    current_action: Action = Action.WALK
    objective: str = "Exploring"
    thought: str = "Processing..."
    state: dict = field(default_factory=lambda: {
        "position": {"x": 0, "y": 0, "z": 0},
        "velocity": {"x": 0, "y": 0, "z": 0},
        "speed": 0,
    })

    def __post_init__(self):
        # Ensure state dictionary is consistent with instance attributes
        self.state.update({
            "agent_id": self.id,
            "location": self.location,
            "current_action": self.current_action,
            "objective": self.objective,
            "thought": self.thought
        })

    def update_position(self, x, y, z):
        self.state["position"] = {"x": x, "y": y, "z": z}
