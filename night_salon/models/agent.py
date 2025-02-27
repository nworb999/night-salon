from dataclasses import dataclass, field
from enum import Enum, auto
import time

from night_salon.models.environment import Area, Location
    

class Action(Enum):
    WALK = auto()
    CHAT = auto()
    WORK = auto()
    MEETING = auto()
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
    area: Area = Area.HALLWAY
    current_action: Action = Action.WALK
    objective: str = "Exploring"
    thought: str = "Processing..."
    destination: str = None
    state: dict = field(default_factory=lambda: {
        "position": {"x": 0, "y": 0, "z": 0},
        "velocity": {"x": 0, "y": 0, "z": 0},
        "speed": 0,
        "last_updated": None,
        "location": None
    })
    memory: dict = field(default_factory=lambda: {})
    relationships: dict = field(default_factory=lambda: {})

    def __post_init__(self):
        self.state.update({
            "agent_id": self.id,
            "area": self.area.name,
            "current_action": self.current_action.name,
            "objective": self.objective,
            "thought": self.thought,
            "destination": self.destination,
            "memory": self.memory,
            "relationships": self.relationships,
            "location": self.state.get("location")
        })
    
    # TODO remove location from staet
    def update_state(self, new_state: dict):
        """Safely update agent state with validation"""
        self.state.update(new_state)
        self.state["last_updated"] = time.time()

        # Sync dataclass Fields with state
        if "location" in new_state:
            self.location = Location[new_state["location"]]
        if "current_action" in new_state:
            self.current_action = Action[new_state["current_action"]]

        self.objective = self.state.get("objective", self.objective)
        self.thought = self.state.get("thought", self.thought)

        if "memory" in new_state:
            self.memory = new_state["memory"]
        if "destination" in new_state:
            self.destination = new_state["destination"]
        if "relationships" in new_state:
            self.relationships = new_state["relationships"]

    def get_location(self):
        return self.state.get("location")
    
    def is_at_location(self, location_id: str):
        return self.get_location() == location_id
