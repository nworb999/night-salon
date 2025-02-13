from night_salon.utils.types import AgentStatus, Location, Action

class StateManager:
    def process_event(self, agent, event):
        """
        Process an event and update agent's cognitive state.
        Returns the updated state to be sent back to Unity.
        """
        if event.type == "position_update":
            pos = event.data["position"]
            agent.update_position(pos["x"], pos["y"], pos["z"])
            if "velocity" in event.data:
                agent.state["velocity"] = event.data["velocity"]
            if "speed" in event.data:
                agent.state["speed"] = event.data["speed"]
            
        elif event.type == "state_change":
            # Convert string to Action enum
            agent.state["current_action"] = Action[event.data["state"].upper()]
            if "position" in event.data:
                pos = event.data["position"]
                agent.update_position(pos["x"], pos["y"], pos["z"])
            
        elif event.type == "destination_change":
            # Convert string to Action enum for movement state
            agent.state["current_action"] = Action[event.data["state"].upper()]
            # Convert string to Location enum for target
            agent.state["location"] = Location[event.data["targetName"].upper()]
            if "position" in event.data:
                pos = event.data["position"]
                agent.update_position(pos["x"], pos["y"], pos["z"])
        
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
        return AgentStatus(
            agent_id=agent.id,
            location=agent.state["location"].name,
            current_action=agent.state["current_action"].name,
            objective=agent.state["objective"],
            thought=agent.state["thought"]
        ).dict()