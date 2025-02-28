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
        # Track planned locations to prevent conflicts
        self.planned_locations = {}  # Maps area_key -> {location_id: agent_id}

        # Seed the environment with all areas from the Area enum
        self._initialize_areas()

    def _initialize_areas(self):
        """Initialize all areas from the Area enum with empty locations"""
        for area in Area:
            area_data = AreaData(
                name=area.name,
                type=area,
                locations={},
                valid=False,  # Mark as invalid until confirmed by Unity
            )
            self.environment.areas[area.value] = area_data
            # Initialize empty planned locations dictionary for this area
            self.planned_locations[area.value] = {}
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
                valid=True,  # Mark as valid since it's explicitly being added
            )
            self.environment.areas[area_name] = area_data
        logger.info(f"Added area: {area_name} with type: {area_type}")

    def add_location_to_area(
        self, area_name, location_id, location_name, location_type
    ):
        """Add a location to an existing area"""
        if area_name not in self.environment.areas:
            logger.warning(
                f"Area {area_name} not found, cannot add location {location_id}"
            )
            return

        area = self.environment.areas[area_name]
        location = Location(
            id=location_id, name=location_name, type=location_type.value
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
            # Release any planned locations
            self.release_planned_location(agent)
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

        # Try multiple possible area keys for more robust lookups
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
            # Look for area using multiple potential keys for reliable lookup
            area_key = self._get_area_key(area)

            if area_key and location_id in self.environment.areas[area_key].locations:
                location = self.environment.areas[area_key].locations[location_id]

                # First remove agent from their current location
                self._remove_agent_from_location(agent)

                # Check if the agent has this location planned
                is_planned = False
                if area_key in self.planned_locations and location_id in self.planned_locations[area_key]:
                    is_planned = self.planned_locations[area_key][location_id] == agent.id
                
                # Check if already occupied by another agent
                if location.occupied_by and location.occupied_by != agent.id:
                    logger.warning(
                        f"Location {location_id} in {area.name} is already occupied. "
                        f"Agent {agent.id} will be in the area but not in the specific location."
                    )
                elif not is_planned and area_key in self.planned_locations and location_id in self.planned_locations[area_key]:
                    # Location is planned by another agent
                    logger.warning(
                        f"Location {location_id} in {area.name} is planned by another agent. "
                        f"Agent {agent.id} will be in the area but not in the specific location."
                    )
                else:
                    # Occupy the location
                    location.occupied_by = agent.id
                    agent.state["location"] = location_id
                    
                    # If this was a planned location, release the plan
                    if is_planned:
                        del self.planned_locations[area_key][location_id]
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
        """Return only locations that are neither occupied nor planned"""
        area_key = self._get_area_key(area)
        if not area_key:
            return {}
            
        result = {}
        for loc_id, location in self.environment.areas[area_key].locations.items():
            # Skip if occupied
            if location.occupied_by:
                continue
                
            # Skip if planned
            if area_key in self.planned_locations and loc_id in self.planned_locations[area_key]:
                continue
                
            # Location is available
            result[loc_id] = location
            
        return result

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
                            "occupied_by": location.occupied_by,
                        }
                        for loc_id, location in area_data.locations.items()
                    },
                }
                for area_key, area_data in self.environment.areas.items()
            },
            "agents": {k: v.state for k, v in self.agents.items()},
            "cameras": self.environment.cameras,
            "items": self.environment.items,
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

    def is_location_available(self, area, location_id):
        """Check if a location is available (not occupied or planned)"""
        area_key = self._get_area_key(area)
        if not area_key:
            return False
            
        # Check if location exists
        if location_id not in self.environment.areas[area_key].locations:
            return False
            
        # Check if location is already occupied
        location = self.environment.areas[area_key].locations[location_id]
        if location.occupied_by:
            return False
            
        # Check if location is planned
        if area_key in self.planned_locations and location_id in self.planned_locations[area_key]:
            return False
            
        return True
        
    def plan_location(self, agent, area, location_id):
        """Reserve a location for an agent to move to later"""
        area_key = self._get_area_key(area)
        if not area_key:
            logger.warning(f"Area {area.name} not found, cannot plan location")
            return False
            
        if not self.is_location_available(area, location_id):
            logger.warning(f"Location {location_id} in {area.name} is not available for planning")
            return False
            
        # Reserve the location
        if area_key not in self.planned_locations:
            self.planned_locations[area_key] = {}
        self.planned_locations[area_key][location_id] = agent.id
        logger.info(f"Agent {agent.id} planned location {location_id} in {area.name}")
        return True
        
    def release_planned_location(self, agent, area=None, location_id=None):
        """Release a planned location if the agent changes plans"""
        # If area and location_id are specified, only release that specific plan
        if area and location_id:
            area_key = self._get_area_key(area)
            if area_key and area_key in self.planned_locations and location_id in self.planned_locations[area_key]:
                if self.planned_locations[area_key][location_id] == agent.id:
                    del self.planned_locations[area_key][location_id]
                    logger.info(f"Agent {agent.id} released planned location {location_id} in {area.name}")
            return
            
        # Otherwise, release all planned locations for this agent
        for area_key, locations in self.planned_locations.items():
            to_remove = []
            for loc_id, agent_id in locations.items():
                if agent_id == agent.id:
                    to_remove.append(loc_id)
            
            for loc_id in to_remove:
                del self.planned_locations[area_key][loc_id]
                logger.info(f"Agent {agent.id} released planned location {loc_id}")

    def _get_area_key(self, area):
        """Helper to get the correct area key from an Area object"""
        for possible_key in [normalize_name(area.name), area.name, area.value]:
            if possible_key in self.environment.areas:
                return possible_key
        return None

    def prepare_agent_move(self, agent_id, area, location_id):
        """Prepare an agent's move by checking and reserving the target location.
        Returns True if the location is available and was reserved, False otherwise."""
        agent = self.agents.get(agent_id)
        if not agent:
            logger.warning(f"Cannot prepare move for unknown agent {agent_id}")
            return False
            
        # Check if location is available
        if not self.is_location_available(area, location_id):
            logger.warning(f"Cannot move agent {agent_id} to {location_id} in {area.name}, location is not available")
            return False
            
        # Plan/reserve the location
        success = self.plan_location(agent, area, location_id)
        if success:
            logger.info(f"Reserved location {location_id} in {area.name} for agent {agent_id}")
        return success
