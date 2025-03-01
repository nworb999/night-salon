from night_salon.controllers.environment import EnvironmentController
from night_salon.models import (
    Agent,
    SetupEvent,
    LocationReachedEvent,
    ProximityEvent,
    Area,
    LocationType,
    AreaData,
    LocationData,
    Location,
)
from night_salon.utils.logger import logger
import random
import asyncio


class EventHandler:
    """Handles different types of system events from clients"""

    @staticmethod
    async def handle_event(
        event_type: str, data: dict, env_controller: EnvironmentController
    ):
        logger.info(f"Received event type: {event_type}")
        logger.debug(f"Event data: {data}")
        try:
            event = EventHandler._create_event_object(event_type, data)
            if not event:
                logger.warning(f"Received unknown event type: {event_type}")
                return None
                
            logger.info(f"Processing {event_type} event")
            
            # Route event to appropriate handler
            if event_type == "setup":
                return await EventHandler._handle_setup(event, env_controller)
            elif event_type == "location_reached":
                return EventHandler._handle_location_reached(event, env_controller)
            elif event_type == "proximity_event":
                EventHandler._handle_proximity_event(event, env_controller)
                return None
                
        except Exception as e:
            logger.error(f"Error handling {event_type} event: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _create_event_object(event_type: str, data: dict):
        """Create the appropriate event object based on event type"""
        event_map = {
            "setup": lambda: SetupEvent(
                type="setup",
                agent_ids=data.get("agent_ids", []),
                areas=[
                    AreaData(
                        name=area.get("area_name"),
                        type=EventHandler._get_area_type(area.get("area_name")),
                        locations={
                            loc.get("location_name"): Location(
                                id=loc.get("location_name"),
                                name=loc.get("location_name"),
                                type=LocationType.STANDING_AREA.value,
                                coordinates=loc.get("coordinates")
                            )
                            for loc in area.get("locations", [])
                        }
                    )
                    for area in data.get("areas", [])
                ],
                cameras=data.get("cameras", []),
                items=data.get("items", []),
            ),
            "location_reached": lambda: LocationReachedEvent(
                type="location_reached",
                agent_id=data["agent_id"],
                location_name=data["location_name"],
                coordinates=data.get("coordinates"),
            ),
            "proximity_event": lambda: ProximityEvent(
                type="proximity_event",
                agent_id=data["agent_id"],
                target_id=data["target_id"],
                event_type=data["event_type"],
                distance=data["distance"],
            ),
        }
        
        return event_map[event_type]() if event_type in event_map else None

    @staticmethod
    def _get_area_type(area_name: str) -> Area:
        """Convert area name to Area enum type"""
        try:
            return Area[area_name.upper()]
        except (KeyError, ValueError, AttributeError):
            logger.warning(f"Unknown area type: {area_name}, defaulting to HALLWAY")
            return Area.HALLWAY

    @staticmethod
    async def _handle_setup(event: SetupEvent, env_controller: EnvironmentController):
        """Initialize environment with agents, areas and cameras"""
        logger.info(f"Initializing setup with {len(event.agent_ids)} agents")
        
        EventHandler._initialize_agents(event.agent_ids, env_controller)
        EventHandler._initialize_areas(event.areas, env_controller)
        EventHandler._initialize_cameras_and_items(event.cameras, event.items, env_controller)
        
        logger.info("Environment setup completed")
        
        # Generate initial move commands for all agents after setup
        move_commands = EventHandler._generate_initial_movement_commands(event.agent_ids, env_controller)
        
        logger.info(f"Generated {len(move_commands)} initial movement commands after setup")
        return move_commands

    @staticmethod
    def _initialize_agents(agent_ids, env_controller):
        """Create new agents and add them to the environment"""
        for agent_id in agent_ids:
            if agent_id not in env_controller.agents:
                logger.debug(f"Creating new agent: {agent_id}")
                env_controller.add_agent(Agent(id=agent_id))

    @staticmethod
    def _initialize_areas(areas, env_controller):
        """Process all areas and their locations"""
        logger.info(f"Setting up {len(areas)} areas")
        
        for area_data in areas:
            area_name = area_data.name
            locations = area_data.locations
            
            # Try to map to an Area enum if possible
            try:
                area_type = Area(area_name.upper())
            except (ValueError, AttributeError):
                # If area_name isn't in Area enum, use HALLWAY as default
                area_type = Area.HALLWAY
                logger.warning(f"Unknown area type: {area_name}, defaulting to HALLWAY")
            
            # Add the area with its locations
            env_controller.add_area(area_name, area_type)
            
            # Add each location to the area
            for location in locations:
                location_name = location.name if hasattr(location, 'name') else location
                coordinates = location.coordinates if hasattr(location, 'coordinates') else None
                
                env_controller.add_location_to_area(
                    area_name, 
                    location_name, 
                    location_name, 
                    LocationType.STANDING_AREA,
                    coordinates
                )

    @staticmethod
    def _initialize_cameras_and_items(cameras, items, env_controller):
        """Add cameras and items to the environment"""
        [env_controller.add_camera(cam) for cam in cameras]
        logger.debug(f"Added {len(cameras)} cameras")
        
        [env_controller.add_item(item) for item in items]
        logger.debug(f"Added {len(items)} items")

    @staticmethod
    def _generate_initial_movement_commands(agent_ids, env_controller):
        """Generate initial movement commands for all agents"""
        move_commands = []
        for agent_id in agent_ids:
            if agent_id in env_controller.agents:
                command = EventHandler.generate_random_movement_command(agent_id, env_controller)
                if command:
                    # Record the time for this initial move command
                    agent = env_controller.agents[agent_id]
                    agent.state["last_move_time"] = asyncio.get_event_loop().time()
                    move_commands.append(command)
                    logger.info(f"Generated initial move command for agent {agent_id} to {command['location_name']}")
        return move_commands

    @staticmethod
    def _handle_location_reached(event: LocationReachedEvent, env_controller: EnvironmentController):
        """Update agent location in environment"""
        logger.info(f"Agent {event.agent_id} reached {event.location_name}")
        agent = env_controller.agents.get(event.agent_id)
        
        if not agent:
            logger.warning(f"Agent {event.agent_id} not found")
            return None
            
        try:
            # Update agent location
            EventHandler._update_agent_position(event, agent, env_controller)
            
            # Generate next movement command
            return EventHandler.generate_random_movement_command(event.agent_id, env_controller)
        except Exception as e:
            logger.error(
                f"Error updating location for agent {event.agent_id}: {str(e)}",
                exc_info=True,
            )
            
        return None

    @staticmethod
    def _update_agent_position(event, agent, env_controller):
        """Update agent's position information in the environment"""
        area = EventHandler._find_area_for_location(event.location_name, env_controller)
        location_id = event.location_name if area else None
        
        env_controller._update_agent_location(agent, area, location_id)
        
        logger.debug(f"Updated area for {event.agent_id} to {area.name}")
        if location_id:
            logger.debug(f"Updated location for {event.agent_id} to {location_id}")
            
        if event.coordinates:
            agent.state["position"] = {
                "x": event.coordinates[0],
                "y": event.coordinates[1],
                "z": event.coordinates[2]
            }
            
        agent.state["last_move_time"] = asyncio.get_event_loop().time()
        agent.state["current_location"] = event.location_name

    @staticmethod
    def _find_area_for_location(location_id, env_controller):
        """Find which area contains the given location"""
        for area_name, area_data in env_controller.environment.areas.items():
            if location_id in area_data.locations:
                logger.debug(f"Location {location_id} belongs to {area_name}")
                return area_data.type
                
        logger.warning(f"Unknown location: {location_id}, defaulting to HALLWAY")
        return Area.HALLWAY

    @staticmethod
    def _handle_proximity_event(
        event: ProximityEvent, env_controller: EnvironmentController
    ):
        """Log proximity events between agents"""
        logger.info(
            f"Proximity event: {event.agent_id} {event.event_type} with {event.target_id} "
            f"at distance {event.distance:.2f}"
        )

    @staticmethod
    def generate_random_movement_command(
        agent_id: str, env_controller: EnvironmentController
    ):
        """Generate a command to move an agent to a random location"""
        agent = env_controller.agents.get(agent_id)
        if not agent:
            logger.warning(f"Agent {agent_id} not found")
            return None

        # Get current location of agent
        current_location = agent.state.get("current_location")
        
        # Find available locations
        available_locations = EventHandler._get_available_locations(current_location, env_controller)
        
        if not available_locations:
            logger.warning("No valid unoccupied locations available for random movement")
            return None

        # Select and reserve a random location
        return EventHandler._create_movement_command(agent_id, available_locations, env_controller)

    @staticmethod
    def _get_available_locations(current_location, env_controller):
        """Get all available locations the agent can move to"""
        available_locations = []
        
        for area_name, area_data in env_controller.environment.areas.items():
            if not area_data.valid:
                continue
            
            try:
                area_enum = Area[area_data.name.upper()]
            except (KeyError, ValueError):
                # Skip areas that don't map to our enum
                continue
                
            # Get truly available locations (neither occupied nor planned)
            area_locations = env_controller.get_available_locations(area_enum)
            
            for loc_id in area_locations:
                # Don't include current location as an option
                if loc_id != current_location:
                    available_locations.append((area_enum, loc_id))
                    
        return available_locations

    @staticmethod
    def _create_movement_command(agent_id, available_locations, env_controller):
        """Create and return a movement command for an agent"""
        # Select a random location
        random_area, random_location = random.choice(available_locations)
        
        # Try to reserve the location before sending command
        if env_controller.prepare_agent_move(agent_id, random_area, random_location):
            logger.info(f"Instructing agent {agent_id} to move to {random_location}")
            
            # Format the command as expected by Unity client
            return {
                "messageType": "move_to_location",
                "agent_id": agent_id,
                "location_name": random_location,
            }
        else:
            logger.warning(f"Failed to reserve location {random_location} for agent {agent_id}")
            return None
