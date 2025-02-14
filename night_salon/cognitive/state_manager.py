from night_salon.models.agent import ACTION_MAPPING
from night_salon.models.environment import LOCATION_MAPPING

class StateManager:
    def process_event(self, agent, event):
        """
        Process an event and update agent's cognitive state.
        Returns the updated state to be sent back to Unity.
        """
        if event.type == "position_update":
            pos = event.data["position"]
            agent.update_position(pos["x"], pos["y"], pos["z"])
            updates = {}
            if "velocity" in event.data:
                updates["velocity"] = event.data["velocity"]
            if "speed" in event.data:
                updates["speed"] = event.data["speed"]
            agent.update_state(updates)
            
        elif event.type == "state_change":
            # Map the state string to an Action enum
            print(f"State: {event.data['state']}")
            print(f"Available actions: {ACTION_MAPPING}")
            
            # TODO make this generative
            state_mapping = {
                "Standing": ACTION_MAPPING["REST"],  # Example mapping
                "Walking": ACTION_MAPPING["WALK"],    # Example mapping
                # Add more mappings as needed
            }

            mapped_state = state_mapping.get(event.data["state"], ACTION_MAPPING["WALK"])
            print(f"Mapped state: {mapped_state}")

            updates = {
                "current_action": mapped_state.name
            }
            if "position" in event.data:
                pos = event.data["position"]
                agent.update_position(pos["x"], pos["y"], pos["z"])
            agent.update_state(updates)
            
        elif event.type == "destination_change":
            # Map the targetName string to a Location enum
            location_mapping = {
                "WaterCooler": LOCATION_MAPPING["WATER_COOLER"],  # Example mapping
                "SmokingArea": LOCATION_MAPPING["SMOKING_AREA"],    # Example mapping
                # Add more mappings as needed
            }
            location = location_mapping.get(event.data["targetName"], LOCATION_MAPPING["HALLWAY"])  # Default to HALLWAY if not found
            
            # Map the state string to an Action enum
            state_mapping = {
                "Walking": ACTION_MAPPING["WALK"],    # Example mapping
                # Add more mappings as needed
            }
            action = state_mapping.get(event.data["state"], ACTION_MAPPING["WALK"])  # Default to WALK if not found
            
            updates = {
                "current_action": action.name,
                "location": location
            }
            if "position" in event.data:
                pos = event.data["position"]
                agent.update_position(pos["x"], pos["y"], pos["z"])
            agent.update_state(updates)
        
        return self._get_cognitive_state(agent)
    
    def _process_nearby_objects(self, agent, nearby_objects):
        """Process nearby objects and update agent state accordingly"""
        # Simple example: if there's a health pickup nearby, mark it as target
        for obj in nearby_objects:
            if obj.get("type") == "health_pickup" and agent.state["health"] < 100:
                agent.state["target"] = obj["id"]
                agent.state["current_action"] = "move_to_pickup"
    
    def _get_cognitive_state(self, agent):
        """Return the current cognitive state to be sent to Unity"""
        state_copy = agent.state.copy()
        return state_copy