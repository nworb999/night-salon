from dataclasses import dataclass
from typing import List, Optional
import random
import asyncio

@dataclass
class AgentAction:
    location: Optional[str] = None
    action: Optional[str] = None
    objective: Optional[str] = None
    thought: Optional[str] = None
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items() if v is not None}

class WorkerAgent:
    def __init__(self, agent_id: str, simulation_url: str):
        self.id = agent_id
        self.simulation_url = simulation_url
        self.current_location = "CUBICLES"
        self.current_action = "WORK"
        self.current_objective = "Starting work day"
        self.current_thought = "Let's be productive"
        
        # Define possible behaviors
        self.locations = ["CONFERENCE_ROOM", "WATER_COOLER", "SMOKING_AREA", "CUBICLES", "BATHROOM"]
        self.actions = ["WALK", "TALK", "WORK", "DRINK", "SMOKE", "REST"]
        
    async def decide_next_action(self) -> AgentAction:
        """Decide next action based on current state and goals"""
        # Simple random behavior for now
        new_location = random.choice(self.locations)
        new_action = random.choice(self.actions)
        
        # Update agent's state
        self.current_location = new_location
        self.current_action = new_action
        self.current_objective = f"Moving to {new_location}"
        self.current_thought = f"I should {new_action.lower()} here"
        
        return AgentAction(
            location=new_location,
            action=new_action,
            objective=self.current_objective,
            thought=self.current_thought
        )