from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from utils.types import Location, Action

@dataclass
class CognitiveState:
    """Represents the agent's internal mental state"""
    emotion: str  # e.g., "happy", "stressed", "neutral"
    energy_level: float  # 0.0 to 1.0
    stress_level: float  # 0.0 to 1.0
    thought: str
    objective: str
    social_need: float  # 0.0 to 1.0
    
@dataclass
class FunctionalState:
    """Represents the agent's physical/observable state"""
    location: Location
    current_action: Action
    current_animation: str  # e.g., "walking", "sitting", "typing"
    interaction_target: Optional[str] = None  # ID of agent being interacted with
    
class BaseAgent(ABC):
    def __init__(self, agent_id: str, simulation_url: str):
        self.id = agent_id
        self.simulation_url = simulation_url
        self.cognitive_state = CognitiveState(
            emotion="neutral",
            energy_level=1.0,
            stress_level=0.0,
            thought="Starting my day",
            objective="Beginning work",
            social_need=0.5
        )
        self.functional_state = FunctionalState(
            location=Location.CUBICLES,
            current_action=Action.WALK,
            current_animation="walking"
        )

    @abstractmethod
    async def decide_next_action(self) -> dict:
        """Decide the next action based on current states"""
        pass

    @abstractmethod
    async def update_cognitive_state(self):
        """Update the agent's cognitive state based on current conditions"""
        pass

    def get_state_update(self) -> dict:
        """Convert current states to API-compatible format"""
        return {
            "location": self.functional_state.location.name,
            "action": self.functional_state.current_action.name,
            "objective": self.cognitive_state.objective,
            "thought": self.cognitive_state.thought
        }