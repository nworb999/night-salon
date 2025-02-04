from fastapi import FastAPI, HTTPException
from typing import Dict, List, Optional
import asyncio
import random
from pydantic import BaseModel
import httpx

from night_salon.utils.logger import setup_logger
from night_salon.utils.config import Config
from night_salon.coordinator.api.client import UnityClient
from night_salon.coordinator.agents.worker import WorkerAgent
from night_salon.coordinator.agents.base import BaseAgent


logger = setup_logger(__name__)

class AgentStatus(BaseModel):
    agent_id: str
    location: str
    current_action: str
    objective: str
    thought: str

class CoordinatorState:
    def __init__(self, simulation_url: str):
        self.simulation_url = simulation_url
        self.agents: Dict[str, WorkerAgent] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        self.unity_client = UnityClient()

        self.unity_client.register_handler("state_change", self._handle_unity_state_change)

    async def create_agent(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            return False
            
        agent = WorkerAgent(agent_id, self.simulation_url)
        self.agents[agent_id] = agent

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.simulation_url}/agents/{agent_id}",
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

def create_app(simulation_url: str) -> FastAPI:
    app = FastAPI()
    state = CoordinatorState(simulation_url)

    @app.post("/agents/{agent_id}")
    async def create_agent(agent_id: str):
        success = await state.create_agent(agent_id)
        if not success:
            raise HTTPException(status_code=400, detail="Agent already exists")
        return {"status": "created"}

    @app.get("/agents")
    async def list_agents() -> List[str]:
        return list(state.agents.keys())

    @app.get("/agents/{agent_id}")
    async def get_agent(agent_id: str) -> AgentStatus:
        agent = state.agents.get(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return AgentStatus(
            agent_id=agent.id,
            location=agent.functional_state.location.name,
            action=agent.functional_state.current_action.name,
            animation=agent.functional_state.current_animation,
            objective=agent.cognitive_state.objective,
            thought=agent.cognitive_state.thought,
            emotion=agent.cognitive_state.emotion
        )

    @app.delete("/agents/{agent_id}")
    async def remove_agent(agent_id: str):
        if agent_id not in state.agents:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        task = state.agent_tasks.pop(agent_id)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        state.agents.pop(agent_id)
        return {"status": "removed"}

    return app