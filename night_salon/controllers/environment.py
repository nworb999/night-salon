from night_salon.models.environment import Area, Location, LocationType
from night_salon.models import EnvironmentState, Agent, AreaData
from night_salon.utils.logger import logger
from night_salon.utils.string_utils import normalize_name

class EnvironmentController:
    """Manages environment state and agent interactions"""
    
    def __init__(self):
        self.environment = EnvironmentState()
        self.environment.areas = {}  # Start with empty areas
        self.agents = {} 
        
        # Seed the environment with all areas from the Area enum
        self._initialize_areas()

    def _initialize_areas(self):
        """Initialize all areas from the Area enum with empty locations"""
        for area in Area:
            area_data = AreaData(
                name=area.name,
                type=area,
                locations={},
                valid=False  # Mark as invalid until confirmed by Unity
            )
            self.environment.areas[area.value] = area_data
            logger.info(f"Initialized area: {area.name}")

    def add_camera(self, camera):
        self.environment.cameras.append(camera)

    def add_area(self, area_name, area_type):
        # Check if area already exists
        if area_name in self.environment.areas:
            # Update existing area
            self.environment.areas[area_name].type = area_type
            self.environment.areas[area_name].valid = True
        else:
            # Create new area
            area_data = AreaData(
                    name=area_name,
                    type=area_type,
                    locations={},
                    valid=True  # Mark as valid since it's explicitly being added
                )
            self.environment.areas[area_name] = area_data
        logger.info(f"Added area: {area_name} with type: {area_type}")

    def add_location_to_area(self, area_name, location_id, location_name, location_type):
        """Add a location to an existing area"""
        if area_name not in self.environment.areas:
            logger.warning(f"Area {area_name} not found, cannot add location {location_id}")
            return
            
        area = self.environment.areas[area_name]
        location = Location(
            id=location_id,
            name=location_name,
            type=location_type.value
        )
        area.locations[location_id] = location
        logger.info(f"Added location {location_id} to area {area_name}")

    def add_item(self, item):
        self.environment.items.append(item)
    
    def add_agent(self, agent: Agent):
        """Register a new agent in the environment"""
        logger.info(f"Added agent: {agent.id}")
        self.agents[agent.id] = agent
        self._update_agent_area(agent)

    def remove_agent(self, agent_id: str):
        """Remove an agent from the environment"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            self._remove_agent_from_area(agent)
            self._remove_agent_from_location(agent)

            del self.agents[agent_id]

    def _update_agent_area(self, agent: Agent):
        """Update agent's area in the environment state"""
        for area_data in self.environment.areas.values():
            if agent.id in area_data.agents:
                area_data.agents.remove(agent.id)

        # Add agent to their current area
        area_key = agent.area.value
        if area_key in self.environment.areas:
            self.environment.areas[area_key].agents.append(agent.id)
        else:
            logger.warning(f"Area {area_key} not found in environment areas")

    def _remove_agent_from_area(self, agent: Agent):
        """Remove agent from their current area"""
        area_key = agent.area.value
        if area_key in self.environment.areas:
            if agent.id in self.environment.areas[area_key].agents:
                self.environment.areas[area_key].agents.remove(agent.id)

    def _remove_agent_from_location(self, agent: Agent):
        """Remove agent from their current location"""
        area = agent.area
        location_id = agent.state.get("location")
        
        if not location_id:
            return
        
        # Look for the area using multiple keys
        found_area = False
        area_key = None
        
        for possible_key in [normalize_name(area.name), area.name, area.value]:
            if possible_key in self.environment.areas:
                area_key = possible_key
                found_area = True
                break
        
        if found_area and location_id in self.environment.areas[area_key].locations:
            location = self.environment.areas[area_key].locations[location_id]
            if location.occupied_by == agent.id:
                location.occupied_by = None

    def _update_agent_location(self, agent: Agent, area: Area, location_id: str = None):
        """Update both the area and specific location for an agent"""
        old_area = agent.area
        
        # Update agent's area
        agent.area = area
        agent.state["area"] = area.name
        
        # Update state with location ID if provided
        if location_id:
            # Get the proper area key - this is the critical fix
            # Either use the normalized name from the enum or look it up directly
            area_key = area.value  # This is the problem - area.value is uppercase "CUBICLES"
            
            # NEW APPROACH: First try to find the area by its normalized name
            normalized_area_name = normalize_name(area.name)
            found_area = False
            
            # Look for area using multiple potential keys
            for possible_key in [normalized_area_name, area.name, area.value]:
                if possible_key in self.environment.areas:
                    area_key = possible_key
                    found_area = True
                    break
            
            if found_area and location_id in self.environment.areas[area_key].locations:
                location = self.environment.areas[area_key].locations[location_id]
                
                # First remove agent from their current location
                self._remove_agent_from_location(agent)
                
                # Check if already occupied by another agent
                if location.occupied_by and location.occupied_by != agent.id:
                    logger.warning(f"Location {location_id} in {area.name} is already occupied. "
                                  f"Agent {agent.id} will be in the area but not in the specific location.")
                else:
                    location.occupied_by = agent.id
                    agent.state["location"] = location_id
            else:
                logger.warning(f"Location {location_id} not found in {area.name}")
                agent.state["location"] = None
        else:
            # If no specific location, just remove them from any current location
            self._remove_agent_from_location(agent)
            agent.state["location"] = None
        
        # If the area changed, update the area assignments
        if old_area != area:
            self._update_agent_area(agent)

    def get_available_locations(self, area: Area):
        area_key = area.value
        if area_key in self.environment.areas:
            return {
                loc_id: location
                for loc_id, location in self.environment.areas[area_key].locations.items()
                if not location.occupied_by
            }
        return {}

    def get_environment_state(self):
        """Return current environment state"""
        return {
            "areas": {
                area_key: {
                    "name": area_data.name,
                    "type": area_data.type.value,
                    "agents": list(area_data.agents),
                    "locations": {
                        loc_id: {
                            "name": location.name,
                            "type": location.type.value,
                            "occupied_by": location.occupied_by
                        }
                        for loc_id, location in area_data.locations.items()
                    }
                }
                for area_key, area_data in self.environment.areas.items()
            },
            "agents": {k: v.state for k, v in self.agents.items()},
            "cameras": self.environment.cameras,
            "items": self.environment.items
        } 

    def get_locations_for_area(self, area_name):
        """Get all locations for a specific area with normalized name lookup"""
        normalized_name = normalize_name(area_name)
        
        # Try with normalized name
        if normalized_name in self.environment.areas:
            return self.environment.areas[normalized_name].locations
        
        # Try with original name as fallback
        if area_name in self.environment.areas:
            return self.environment.areas[area_name].locations
        
        logger.warning(f"Area {area_name} not found")
        return [] 