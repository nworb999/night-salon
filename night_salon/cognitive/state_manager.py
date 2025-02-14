import random
from night_salon.models.agent import ACTION_MAPPING
from night_salon.models.environment import LOCATION_MAPPING

class StateManager:
    def process_event(self, agent, event):
        """
        Process an event and update agent's cognitive state.
        Returns only the destination if changed, otherwise None.
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
            return None
            
        elif event.type == "state_change":
            state_mapping = {
                "Standing": ACTION_MAPPING["REST"],
                "Walking": ACTION_MAPPING["WALK"],
            }

            mapped_state = state_mapping.get(event.data["state"], ACTION_MAPPING["WALK"])
            updates = {
                "current_action": mapped_state.name
            }

            # Check if the agent is now standing and was previously walking
            if event.data["state"] == "Standing" and agent.current_action == ACTION_MAPPING["WALK"]:
                # Get a new random destination excluding current one
                new_destination = self._get_new_destination(agent.destination)
                updates["destination"] = new_destination
                
                if "position" in event.data:
                    pos = event.data["position"]
                    agent.update_position(pos["x"], pos["y"], pos["z"])
                agent.update_state(updates)
                
                return new_destination
                
            agent.update_state(updates)
            return None
            
        return None
    
    def _process_nearby_objects(self, agent, nearby_objects):
        """Process nearby objects and update agent state accordingly"""
        # Simple example: if there's a health pickup nearby, mark it as target
        for obj in nearby_objects:
            if obj.get("type") == "health_pickup" and agent.state["health"] < 100:
                agent.state["target"] = obj["id"]
                agent.state["current_action"] = "move_to_pickup"
    
    def _get_new_destination(self, current_destination):
        """Choose a new random destination from all available sub-locations, excluding the current one."""
        # Collect all available sub-locations
        all_sub_locations = []
        for location_data in LOCATION_MAPPING.values():
            all_sub_locations.extend(location_data.sub_locations)
        
        # Remove current destination from options if it exists
        if current_destination in all_sub_locations:
            all_sub_locations.remove(current_destination)
        
        # Return random choice from remaining options
        # If no options left, return None
        return random.choice(all_sub_locations) if all_sub_locations else None
    
    def _get_cognitive_state(self, agent):
        """Return the current cognitive state to be sent to Unity"""
        state_copy = agent.state.copy()
        return state_copy