from night_salon.controllers.environment import EnvironmentController
from night_salon.models import Agent, SetupEvent, LocationReachedEvent, ProximityEvent
from night_salon.utils.logger import logger

class EventHandler:
    """Handles different types of system events from clients"""
    
    @staticmethod
    async def handle_event(event_type: str, data: dict, env_controller: EnvironmentController):
        try:
            event_map = {
                "setup": SetupEvent(**data),
                "location_reached": LocationReachedEvent(**data),
                "proximity_event": ProximityEvent(**data)
            }
            
            if event_type in event_map:
                event = event_map[event_type]
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
        env_controller.environment.locations = {loc: {} for loc in event.locations}
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
