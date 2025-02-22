from night_salon.models import EnvironmentState, Agent
from night_salon.utils.logger import logger

class EnvironmentController:
    """Manages environment state and agent interactions"""
    
    def __init__(self):
        self.environment = EnvironmentState()
        self.agents = {}  
        self.environment.cameras = []  # Initialize cameras list
        # TODO add cameras and locations

    def add_agent(self, agent: Agent):
        """Register a new agent in the environment"""
        self.agents[agent.id] = agent
        self._update_agent_location(agent)

    def remove_agent(self, agent_id: str):
        """Remove an agent from the environment"""
        if agent_id in self.agents:
            del self.agents[agent_id]

    def _update_agent_location(self, agent: Agent):
        """Update agent's location in the environment"""
        if agent.location:
            # Remove from previous location
            for loc_data in self.environment.locations.values():
                if agent.id in loc_data.sub_locations:
                    loc_data.sub_locations.remove(agent.id)
            
            # Add to new location
            if agent.location in self.environment.locations:
                self.environment.locations[agent.location].sub_locations.append(agent.id)
            else:
                logger.warning(f"Location {agent.location} not found in environment locations")

    def get_environment_state(self):
        """Return current environment state"""
        return {
            "locations": self.environment.locations,
            "agents": {k: v.state for k, v in self.agents.items()},
            "cameras": self.environment.cameras,
            "items": self.environment.items
        } 