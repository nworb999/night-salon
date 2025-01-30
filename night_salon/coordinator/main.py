from fastapi import FastAPI, HTTPException
from typing import Dict, List, Optional
import asyncio
import random
from pydantic import BaseModel
import httpx

from night_salon.utils.logger import setup_logger
from night_salon.coordinator.agents.worker import WorkerAgent
from night_salon.utils.config import Config

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

    async def create_agent(self, agent_id: str) -> bool:
        """Create a new agent and start its behavior loop"""
        if agent_id in self.agents:
            return False
            
        # Create new agent
        agent = WorkerAgent(agent_id, self.simulation_url)
        self.agents[agent_id] = agent
        
        # Start agent behavior loop
        task = asyncio.create_task(self._agent_loop(agent))
        self.agent_tasks[agent_id] = task
        
        return True

    async def _agent_loop(self, agent: WorkerAgent):
        """Main loop for agent behavior"""
        try:
            while True:
                # Get next action from agent
                action = await agent.decide_next_action()
                
                # Execute action in simulation
                async with httpx.AsyncClient() as client:
                    response = await client.put(
                        f"{self.simulation_url}/agents/{agent.id}",
                        json=action.dict()
                    )
                    if response.status_code != 200:
                        logger.error(f"Failed to update agent {agent.id}: {response.text}")
                
                # Wait before next action
                await asyncio.sleep(random.uniform(1, 5))  # Random delay between actions
                
        except Exception as e:
            logger.error(f"Agent {agent.id} loop failed: {e}")
            # Remove failed agent
            self.agents.pop(agent.id, None)
            self.agent_tasks.pop(agent.id, None)

def create_app(simulation_url: str) -> FastAPI:
    app = FastAPI()
    state = CoordinatorState(simulation_url)

    @app.post("/agents/{agent_id}")
    async def create_agent(agent_id: str):
        """Create a new agent"""
        success = await state.create_agent(agent_id)
        if not success:
            raise HTTPException(status_code=400, detail="Agent already exists")
        return {"status": "created"}

    @app.get("/agents")
    async def list_agents() -> List[str]:
        """List all active agents"""
        return list(state.agents.keys())

    @app.get("/agents/{agent_id}")
    async def get_agent(agent_id: str) -> AgentStatus:
        """Get status of specific agent"""
        agent = state.agents.get(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return AgentStatus(
            agent_id=agent.id,
            location=agent.current_location,
            current_action=agent.current_action,
            objective=agent.current_objective,
            thought=agent.current_thought
        )

    @app.delete("/agents/{agent_id}")
    async def remove_agent(agent_id: str):
        """Remove an agent"""
        if agent_id not in state.agents:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        # Cancel agent task
        task = state.agent_tasks.pop(agent_id)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        # Remove agent
        state.agents.pop(agent_id)
        return {"status": "removed"}

    return app