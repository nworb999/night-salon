from night_salon.models import LocationReachedEvent


class Planner:
    """Planning system with location awareness"""
    
    def __init__(self, memory):
        self.memory = memory
    
    def generate_plan(self, event, context) -> dict:
        """Generate plan considering location history"""
        base_plan = {
            "reasoning": "Basic behavioral pattern",
            "actions": []
        }
        
        if isinstance(event, LocationReachedEvent):
            visit_count = context["locations_visited"].get(event.location_name, 0)
            if visit_count == 1:
                base_plan["actions"].append({"action": "explore", "location": event.location_name})
            else:
                base_plan["actions"].append({"action": "check_familiar", "location": event.location_name})
        
        return base_plan
