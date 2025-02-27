from night_salon.controllers.environment import EnvironmentController
from night_salon.models import Agent, SetupEvent, LocationReachedEvent, ProximityEvent, LocationData
from night_salon.utils.logger import logger
from night_salon.models.environment import Location
import random
import asyncio

class EventHandler:
    """Handles different types of system events from clients"""
    
    @staticmethod
    async def handle_event(event_type: str, data: dict, env_controller: EnvironmentController):
        logger.info(f"Received event type: {event_type}")
        logger.debug(f"Event data: {data}")
        try:
            event_map = {
                "setup": lambda: SetupEvent(
                    type="setup",
                    agent_ids=data.get('agent_ids', []),
                    locations=data.get('locations', []),
                    cameras=data.get('cameras', []),
                    items=data.get('items', [])
                ),
                "location_reached": lambda: LocationReachedEvent(
                    type="location_reached",
                    agent_id=data['agent_id'],
                    location_name=data['location_name'],
                    coordinates=data.get('coordinates'),
                    sub_location=data.get('sub_location')
                ),
                "proximity_event": lambda: ProximityEvent(
                    type="proximity_event",
                    agent_id=data['agent_id'],
                    target_id=data['target_id'],
                    event_type=data['event_type'],
                    distance=data['distance']
                )
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
        """Initialize environment with agents, locations and cameras"""
        logger.info(f"Initializing setup with {len(event.agent_ids)} agents")
        for agent_id in event.agent_ids:
            if agent_id not in env_controller.agents:
                logger.debug(f"Creating new agent: {agent_id}")
                env_controller.add_agent(Agent(id=agent_id))
        
        logger.info(f"Setting up {len(event.locations)} locations: {', '.join(event.locations)}")
        
        # Get all available location types
        location_types = list(Location)
        type_index = 0  # Counter for cycling through location types
        
        # First, mark all locations as invalid
        for loc_data in env_controller.environment.locations.values():
            loc_data.valid = False
        
        for i, raw_loc in enumerate(event.locations):
            # Try to find matching enum value first
            try:
                loc_type = Location(raw_loc)
            except ValueError:
                # Assign type based on position cycling through available types
                loc_type = location_types[type_index % len(location_types)]
                type_index += 1
            
            env_controller.add_location(raw_loc, loc_type)
            # Mark this location as valid since it came from setup
            if raw_loc in env_controller.environment.locations:
                env_controller.environment.locations[raw_loc].valid = True
            logger.debug(f"Added location '{raw_loc}' with type {loc_type}")
        
        [env_controller.add_camera(cam) for cam in event.cameras]
        logger.debug(f"Added {len(event.cameras)} cameras")
        
        [env_controller.add_item(item) for item in event.items]
        logger.debug(f"Added {len(event.items)} items")
        
        logger.info("Environment setup completed")
        
        # Generate initial move commands for all agents after setup
        move_commands = []
        for agent_id in event.agent_ids:
            if agent_id in env_controller.agents:
                command = EventHandler.generate_random_movement_command(agent_id, env_controller)
                if command:
                    # Record the time for this initial move command
                    agent = env_controller.agents[agent_id]
                    agent.state["last_move_time"] = asyncio.get_event_loop().time()
                    move_commands.append(command)
                    logger.info(f"Generated initial move command for agent {agent_id} to {command['location_name']}")
        
        logger.info(f"Generated {len(move_commands)} initial movement commands after setup")
        return move_commands  # Return the movement commands to be sent back to client

    @staticmethod
    def _handle_location_reached(event: LocationReachedEvent, env_controller: EnvironmentController):
        """Update agent location in environment"""
        # TODDO add handling for incoming SUB locations
        logger.info(f"Agent {event.agent_id} reached {event.location_name}")
        agent = env_controller.agents.get(event.agent_id)
        if agent:
            try:
                location_enum = None
                try:
                    location_enum = Location(event.location_name)
                except ValueError:
                    try:
                        location_enum = Location[event.location_name]
                    except KeyError:
                        logger.warning(f"Unknown location: {event.location_name}, defaulting to HALLWAY")
                        location_enum = Location.HALLWAY

                env_controller._update_agent_location(
                    agent,
                    location_enum, 
                    event.sub_location
                )
            
                logger.debug(f"Updated location for {event.agent_id} to {location_enum.name}")

                if event.coordinates:
                    agent.state["position"] = event.coordinates
                    
                # Record the time agent reached this location
                agent.state["last_move_time"] = asyncio.get_event_loop().time()
                # Store current location to avoid immediately returning
                agent.state["current_location"] = event.location_name
                
                # Generate next random movement command and return it to be sent to the client
                return EventHandler.generate_random_movement_command(event.agent_id, env_controller)

            except Exception as e:
                logger.error(f"Error updating location for agent {event.agent_id}: {str(e)}", exc_info=True)
        else:
            logger.warning(f"Agent {event.agent_id} not found")
        
        return None  # Return None if no command was generated

    @staticmethod
    def _handle_proximity_event(event: ProximityEvent, env_controller: EnvironmentController):
        """Log proximity events between agents"""
        logger.info(
            f"Proximity event: {event.agent_id} {event.event_type} with {event.target_id} "
            f"at distance {event.distance:.2f}"
        )

    @staticmethod
    def generate_random_movement_command(agent_id: str, env_controller: EnvironmentController):
        """Generate a command to move an agent to a random location"""
        # Get only valid locations (those that exist in Unity)
        available_locations = [
            loc_key for loc_key, loc_data in env_controller.environment.locations.items()
            if loc_data.valid
        ]
        
        if not available_locations:
            logger.warning("No valid locations available for random movement")
            return None
        
        agent = env_controller.agents.get(agent_id)
        if not agent:
            logger.warning(f"Agent {agent_id} not found")
            return None
        
        # Get current location of agent to avoid selecting the same one
        current_location = agent.state.get("current_location")
        
        # Filter out current location from available destinations
        if current_location and current_location in available_locations:
            filtered_locations = [loc for loc in available_locations if loc != current_location]
            if filtered_locations:
                available_locations = filtered_locations
        
        # Select a random location
        random_location = random.choice(available_locations)
        
        logger.info(f"Instructing agent {agent_id} to move to {random_location}")
        
        # Format the command as expected by Unity client
        return {
            "messageType": "move_to_location",
            "agent_id": agent_id,
            "location_name": random_location
        }
