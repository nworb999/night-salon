from datetime import datetime
from night_salon.models import LocationReachedEvent


class Memory:
    """Agent memory with location tracking"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.experiences = []
        self.locations_visited = {}  # {location_name: visit_count}

    async def retrieve_context(self, event) -> dict:
        """Retrieve context including location history"""
        return {
            "locations_visited": self.locations_visited,
            "recent_experiences": self.experiences[-3:],  # Last 3 experiences
        }

    async def store_experience(self, event, actions):
        """Store experience and update location visits"""
        if isinstance(event, LocationReachedEvent):
            loc = event.location_name
            self.locations_visited[loc] = self.locations_visited.get(loc, 0) + 1

        self.experiences.append(
            {
                "event": event.dict(),
                "actions": actions,
                "timestamp": datetime.now().isoformat(),
            }
        )
