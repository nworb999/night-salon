from night_salon.controllers.environment import EnvironmentController
from night_salon.models import Agent, SetupEvent, LocationReachedEvent, ProximityEvent, LocationData
from night_salon.utils.logger import logger
from night_salon.models.environment import Location

class EventHandler:
    """Handles different types of system events from clients"""
    
    @staticmethod
    async def handle_event(event_type: str, data: dict, env_controller: EnvironmentController):
        print("\nevent_type",event_type)
        print("\ndata",data)
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
                    coordinates=data.get('coordinates')
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
                    EventHandler._handle_setup(event, env_controller)
                elif event_type == "location_reached":
                    EventHandler._handle_location_reached(event, env_controller)
                elif event_type == "proximity_event":
                    EventHandler._handle_proximity_event(event, env_controller)
            else:
                logger.warning(f"Received unknown event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling {event_type} event: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _handle_setup(event: SetupEvent, env_controller: EnvironmentController):
        """Initialize environment with agents, locations and cameras"""
        logger.info(f"Initializing setup with {len(event.agent_ids)} agents")
        for agent_id in event.agent_ids:
            if agent_id not in env_controller.agents:
                logger.debug(f"Creating new agent: {agent_id}")
                env_controller.add_agent(Agent(id=agent_id))
        
        logger.info(f"Setting up {len(event.locations)} locations")
        # Get all available location types
        location_types = list(Location)
        type_index = 0  # Counter for cycling through location types
        
        env_controller.environment.locations = {}
        for i, raw_loc in enumerate(event.locations):
            # Try to find matching enum value first
            try:
                loc_type = Location(raw_loc)
            except ValueError:
                # Assign type based on position cycling through available types
                loc_type = location_types[type_index % len(location_types)]
                type_index += 1
            
            env_controller.environment.locations[raw_loc] = LocationData(
                name=raw_loc,
                type=loc_type,
                sub_locations=[]
            )
        
        env_controller.environment.cameras = event.cameras
        env_controller.environment.items = event.items
        logger.debug("Environment setup completed")

    @staticmethod
    def _handle_location_reached(event: LocationReachedEvent, env_controller: EnvironmentController):
        """Update agent location in environment"""
        logger.info(f"Agent {event.agent_id} reached {event.location_name}")
        agent = env_controller.agents.get(event.agent_id)
        if agent:
            agent.location = event.location_name
            env_controller._update_agent_location(agent)
            logger.debug(f"Updated location for {event.agent_id}")
        else:
            logger.warning(f"Agent {event.agent_id} not found")

    @staticmethod
    def _handle_proximity_event(event: ProximityEvent, env_controller: EnvironmentController):
        """Log proximity events between agents"""
        logger.info(
            f"Proximity event: {event.agent_id} {event.event_type} with {event.target_id} "
            f"at distance {event.distance:.2f}"
        )
