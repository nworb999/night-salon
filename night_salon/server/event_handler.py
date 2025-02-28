from night_salon.controllers.environment import EnvironmentController
from night_salon.models import (
    Agent,
    SetupEvent,
    LocationReachedEvent,
    ProximityEvent,
    Area,
    LocationType,
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
            event_map = {
                "setup": lambda: SetupEvent(
                    type="setup",
                    agent_ids=data.get("agent_ids", []),
                    areas=data.get("areas", []),
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

            if event_type in event_map:
                event = event_map[event_type]()
                logger.info(f"Processing {event_type} event")

                if event_type == "setup":
                    response = await EventHandler._handle_setup(event, env_controller)
                    return response  # Return the setup response with move commands
                elif event_type == "location_reached":
                    return EventHandler._handle_location_reached(event, env_controller)
                elif event_type == "proximity_event":
                    EventHandler._handle_proximity_event(event, env_controller)
            else:
                logger.warning(f"Received unknown event type: {event_type}")

        except Exception as e:
            logger.error(f"Error handling {event_type} event: {str(e)}", exc_info=True)
            raise

    @staticmethod
    async def _handle_setup(event: SetupEvent, env_controller: EnvironmentController):
        """Initialize environment with agents, areas and cameras"""
        logger.info(f"Initializing setup with {len(event.agent_ids)} agents")
        for agent_id in event.agent_ids:
            if agent_id not in env_controller.agents:
                logger.debug(f"Creating new agent: {agent_id}")
                env_controller.add_agent(Agent(id=agent_id))

        logger.info(f"Setting up {len(event.areas)} areas")

        # Process all areas from the setup event
        for area_data in event.areas:
            area_name = area_data.area_name
            locations = area_data.locations

            # Try to map to an Area enum if possible, otherwise use the name as a string
            try:
                area_type = Area(area_name.upper())
            except (ValueError, AttributeError):
                # If area_name isn't in Area enum, use HALLWAY as default
                area_type = Area.HALLWAY
                logger.warning(f"Unknown area type: {area_name}, defaulting to HALLWAY")

            # Add the area with its locations
            env_controller.add_area(area_name, area_type)

            # Add each location to the area
            for location_name in locations:
                # Default to STANDING_AREA for all locations
                env_controller.add_location_to_area(
                    area_name, location_name, location_name, LocationType.STANDING_AREA
                )

        [env_controller.add_camera(cam) for cam in event.cameras]
        logger.debug(f"Added {len(event.cameras)} cameras")

        [env_controller.add_item(item) for item in event.items]
        logger.debug(f"Added {len(event.items)} items")

        logger.info("Environment setup completed")

        # Generate initial move commands for all agents after setup
        move_commands = []
        for agent_id in event.agent_ids:
            if agent_id in env_controller.agents:
                command = EventHandler.generate_random_movement_command(
                    agent_id, env_controller
                )
                if command:
                    # Record the time for this initial move command
                    agent = env_controller.agents[agent_id]
                    agent.state["last_move_time"] = asyncio.get_event_loop().time()
                    move_commands.append(command)
                    logger.info(
                        f"Generated initial move command for agent {agent_id} to {command['location_name']}"
                    )

        logger.info(
            f"Generated {len(move_commands)} initial movement commands after setup"
        )
        return move_commands  # Return the movement commands to be sent back to client

    @staticmethod
    def _handle_location_reached(
        event: LocationReachedEvent, env_controller: EnvironmentController
    ):
        """Update agent location in environment"""
        logger.info(f"Agent {event.agent_id} reached {event.location_name}")
        agent = env_controller.agents.get(event.agent_id)
        if agent:
            try:
                area = None
                location_id = event.location_name

                # Find which area contains this location
                for area_name, area_data in env_controller.environment.areas.items():
                    if location_id in area_data.locations:
                        area = area_data.type
                        logger.debug(f"Location {location_id} belongs to {area_name}")
                        break

                if not area:
                    logger.warning(
                        f"Unknown location: {location_id}, defaulting to HALLWAY"
                    )
                    area = Area.HALLWAY
                    location_id = None

                env_controller._update_agent_location(agent, area, location_id)

                logger.debug(f"Updated area for {event.agent_id} to {area.name}")
                if location_id:
                    logger.debug(
                        f"Updated location for {event.agent_id} to {location_id}"
                    )

                if event.coordinates:
                    agent.state["position"] = event.coordinates

                agent.state["last_move_time"] = asyncio.get_event_loop().time()
                agent.state["current_location"] = event.location_name

                return EventHandler.generate_random_movement_command(
                    event.agent_id, env_controller
                )

            except Exception as e:
                logger.error(
                    f"Error updating location for agent {event.agent_id}: {str(e)}",
                    exc_info=True,
                )
        else:
            logger.warning(f"Agent {event.agent_id} not found")

        return None  # Return None if no command was generated

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
        
        # Find all available locations across all areas using our availability checking
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

        if not available_locations:
            logger.warning(
                "No valid unoccupied locations available for random movement"
            )
            return None

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
