from night_salon.models.environment import Location
from night_salon.models import EnvironmentState, Agent, LocationData, LOCATION_MAPPING
from night_salon.utils.logger import logger

class EnvironmentController:
    """Manages environment state and agent interactions"""
    
    def __init__(self):
        self.environment = EnvironmentState()
        self.environment.locations = LOCATION_MAPPING.copy()
        self.agents = {} 

    def add_camera(self, camera):
        self.environment.cameras.append(camera)

    def add_location(self, location_name, location_type):
        # Check if location already exists
        if location_name in self.environment.locations:
            # Update existing location
            self.environment.locations[location_name].type = location_type
            self.environment.locations[location_name].valid = True
        else:
            # Create new location
            location_data = LocationData(
                    name=location_name,
                    type=location_type,
                    sub_locations=[],
                    valid=True  # Mark as valid since it's explicitly being added
                )
            self.environment.locations[location_name] = location_data
        logger.info(f"Added location: {location_name} with type: {location_type}")

    def add_item(self, item):
        self.environment.items.append(item)
    
    def add_agent(self, agent: Agent):
        """Register a new agent in the environment"""
        logger.info(f"Added agent: {agent.id}")
        self.agents[agent.id] = agent
        self._update_agent_main_location(agent)

    def remove_agent(self, agent_id: str):
        """Remove an agent from the environment"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            self._remove_agent_from_main_location(agent)
            self._remove_agent_from_sub_location(agent)

            del self.agents[agent_id]

    def _update_agent_main_location(self, agent: Agent):
        """Update agent's main location in the environment state"""
        for loc_data in self.environment.locations.values():
            if agent.id in loc_data.agents:
                loc_data.agents.remove(agent.id)

        # TODO refactor this and add functions instead of these chains
        location_key = agent.location.value
        if location_key in self.environment.locations:
            self.environment.locations[location_key].agents.append(agent.id)
        else:
            logger.warning(f"Location {location_key} not found in environment locations")

    def _remove_agent_from_main_location(self, agent: Agent):
        """Remove agent from their current main location"""
        location_key = agent.location.value
        if location_key in self.environment.locations:
            if agent.id in self.environment.locations[location_key].agents:
                self.environment.locations[location_key].agents.remove(agent.id)

    def _remove_agent_from_sub_location(self, agent: Agent):
        """Remove agent from their current sub-location"""
        location_key = agent.location.value
        sub_loc_id = agent.state.get("sub_location")

        if (location_key in self.environment.locations and sub_loc_id and sub_loc_id in self.environment.locations[location_key].sub_locations):
            sub_location = self.environment.locations[location_key].sub_locations[sub_loc_id]
            if sub_location.occupied_by == agent.id:
                sub_location.occupied_by = None

    def _update_agent_location(self, agent: Agent, location: Location, sub_location_id:str = None):
        """Update agent's location in the environment"""
        old_location = agent.location
        agent.location = location

        new_state = {
            "location": location.name
        }

        if sub_location_id:
            location_key = location.value

            if (location_key in self.environment.locations and sub_location_id in self.environment.locations[location_key].sub_locations):
                sub_loc = self.environment.locations[location_key].sub_locations[sub_location_id]

                # check if already occupied by another agent
                if sub_loc.occupied_by and sub_loc.occupied_by != agent.id:
                    logger.warning(f"Sub-location {sub_location_id} in {location.name} is already occupied. "
                                   f"Agent {agent.id} will be in the location but not in the specific sub-location.")
                else:
                    self._remove_agent_from_sub_location(agent)

                    sub_loc.occupied_by = agent.id
                    new_state["sub_location"] = sub_location_id

            else:
                logger.warning(f"Sub-location {sub_location_id} not found in {location.name}")
        
        else:
            self._remove_agent_from_sub_location(agent)
            new_state["sub_location"] = None

        agent.update_state(new_state)

        if old_location != location:
            self._update_agent_main_location(agent)

    def get_available_sub_locations(self, location:Location):
        location_key = location.value
        if location_key in self.environment.locations:
            return {
                sub_id: sub_loc
                for sub_id, sub_loc in self.environment.locations[location_key].sub_locations.items()
                if not sub_loc.occupied_by
            }
        return {}

    def get_environment_state(self):
        """Return current environment state"""
        return {
            "locations": {
                loc_key: {
                    "name": loc_data.name,
                    "type": loc_data.type.value,
                    "agents": list(loc_data.agents),
                    "sub_locations": {
                        sub_id: {
                            "name": sub_loc.name,
                            "type": sub_loc.type.value,
                            "occupied_by": sub_loc.occupied_by
                        }
                        for sub_id, sub_loc in loc_data.sub_locations.items()
                    }
                }
                for loc_key, loc_data in self.environment.locations.items()
            },
            "agents": {k: v.state for k, v in self.agents.items()},
            "cameras": self.environment.cameras,
            "items": self.environment.items
        } 