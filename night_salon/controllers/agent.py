from typing import Any
from night_salon.cognitive.planner import Planner
from night_salon.cognitive.memory import Memory
from night_salon.models import AgentEvent, Agent
from night_salon.server.event_handler import EventHandler
import json

class AgentController:
    """Manages individual agent's cognitive processes"""
    
    def __init__(self, agent: Agent, env_controller):
        self.agent = agent
        self.env_controller = env_controller
        self.memory = Memory(agent.id)
        self.planner = Planner(self.memory)

    async def process_event(self, event: AgentEvent) -> dict[str, Any]:
        """Handle incoming events and return agent response"""
        # Parse event data
        event_data = event if isinstance(event, dict) else json.loads(event)
        
        # Handle system events directly
        if 'messageType' in event_data:
            await EventHandler.handle_event(
                event_data['messageType'],
                event_data,
                self.env_controller
            )
            return {"status": "event_processed"}
        
        # Existing cognitive processing
        context = await self.memory.retrieve_context(event)
        plan = self.planner.generate_plan(event, context)
        self.agent.update_state(plan["actions"])
        await self.memory.store_experience(event, plan["actions"])
        self.env_controller.add_agent(self.agent)
        
        return {
            "agent_id": self.agent.id,
            "state": self.agent.state,
            "actions": plan["actions"]
        } 