from pydantic import BaseModel
from dataclasses import dataclass
from enum import Enum, auto


class AgentStatus(BaseModel):
    agent_id: str
    location: str
    current_action: str
    objective: str
    thought: str


class Location(Enum):
    CONFERENCE_ROOM = auto()
    WATER_COOLER = auto()
    SMOKING_AREA = auto()
    CUBICLES = auto()
    BATHROOM = auto()


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
    location: Location
    current_action: Action
    objective: str
    thought: str
