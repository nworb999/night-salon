
import httpx
from typing import Dict
import asyncio

from night_salon.unity.client import UnityClient
from night_salon.agents.worker import WorkerAgent
from night_salon.agents.base import BaseAgent
from utils.types import Location
from utils.logger import logger

class CoordinatorState:
    def __init__(self, unity_url: str, unity_host: str = "127.0.0.1", unity_bind_host: str = "0.0.0.0", 
                 unity_tcp_port: int = 8052, unity_udp_port: int = 8053):
        self.unity_url = unity_url
        self.agents: Dict[str, WorkerAgent] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        self.unity_client = UnityClient(
            bind_host=unity_bind_host,
            unity_host=unity_host,
            unity_tcp_port=unity_tcp_port,
            unity_udp_port=unity_udp_port
        )

        self.unity_client.register_handler("state_change", self._handle_unity_state_change)

    async def create_agent(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            return False
            
        agent = WorkerAgent(agent_id, self.unity_url)
        self.agents[agent_id] = agent

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.unity_url}/agents/{agent_id}",
                json={"location": Location.CUBICLES.name}
            )
            if response.status_code != 200:
                logger.error(f"Failed to initialize agent {agent_id} in simulation: {response.text}")
                return False
        
        task = asyncio.create_task(self._agent_loop(agent))
        self.agent_tasks[agent_id] = task
        
        return True

    async def _handle_unity_state_change(self, agent_id: str, new_state: dict):
        """Handle state changes from Unity"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            
            # Update cognitive state based on Unity state
            if 'state' in new_state:
                unity_state = new_state['state']
                # Map Unity states to emotions
                state_to_emotion = {
                    'walking': 'active',
                    'standing': 'idle'
                }
                
                # Update cognitive state
                agent.cognitive_state.emotion = state_to_emotion.get(unity_state, 'neutral')
                
                # Send immediate update back to Unity
                state_update = agent.get_state_update()
                self.unity_client.send_agent_update(agent_id, state_update)

    async def _agent_loop(self, agent: BaseAgent):
        """Remove the automatic decision making - only react to Unity state changes"""
        try:
            while True:
                # Just keep the loop alive but don't make autonomous decisions
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in agent loop for {agent.id}: {e}")