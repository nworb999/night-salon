from pydantic import BaseModel
from dataclasses import dataclass, field
from enum import Enum, auto
import time

from night_salon.models.environment import Location
    

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

# Create a dictionary mapping action names to enum values
ACTION_MAPPING = {action.name: action for action in Action}


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
        "last_updated": None,
    })

    def __post_init__(self):
        self.state.update({
            "agent_id": self.id,
            "location": self.location.name,
            "current_action": self.current_action.name,
            "objective": self.objective,
            "thought": self.thought
        })
        
    def update_state(self, new_state: dict):
        """Safely update agent state with validation"""
        self.state.update(new_state)
        self.state["last_updated"] = time.time()
        # Sync dataclass fields with state
        if "location" in new_state:
            self.location = Location[new_state["location"]]
        if "current_action" in new_state:
            self.current_action = Action[new_state["current_action"]]
        self.objective = self.state.get("objective", self.objective)
        self.thought = self.state.get("thought", self.thought)

    def update_position(self, x, y, z):
        self.state["position"] = {"x": x, "y": y, "z": z}
        self.state["last_updated"] = time.time()
