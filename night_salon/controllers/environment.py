from night_salon.models.environment import EnvironmentState, LOCATION_MAPPING
from night_salon.models.agent import Agent

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
        """Update environment with agent's location data"""
        location_data = LOCATION_MAPPING.get(agent.location.name)
        if location_data:
            # Add agent to location tracking
            self.environment.locations[agent.location.name].sub_locations.append(agent.id)

    def get_environment_state(self):
        """Return current environment state"""
        return {
            "locations": self.environment.locations,
            "agents": {k: v.state for k, v in self.agents.items()},
            "cameras": self.environment.cameras,
            "items": self.environment.items
        } 