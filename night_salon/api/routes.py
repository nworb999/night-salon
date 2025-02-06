import asyncio
from fastapi import APIRouter, HTTPException
from typing import List

from night_salon.state import CoordinatorState
from utils.types import AgentStatus

router = APIRouter()
state: CoordinatorState = None

def init_routes(coordinator_state: CoordinatorState):
    global state
    state = coordinator_state

@router.post("/agents/{agent_id}")
async def create_agent(agent_id: str):
    success = await state.create_agent(agent_id)
    if not success:
        raise HTTPException(status_code=400, detail="Agent already exists")
    return {"status": "created"}


@router.post("/agents/{agent_id}")
async def create_agent(agent_id: str):
    success = await state.create_agent(agent_id)
    if not success:
        raise HTTPException(status_code=400, detail="Agent already exists")
    return {"status": "created"}

@router.get("/agents")
async def list_agents() -> List[str]:
    return list(state.agents.keys())

@router.get("/agents/{agent_id}")
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

@router.delete("/agents/{agent_id}")
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