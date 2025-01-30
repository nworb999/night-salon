from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from night_salon.simulation.environment.office import (Action, Location,
                                                       OfficeEnvironment)

app = FastAPI()
office = OfficeEnvironment()


class AgentUpdate(BaseModel):
    location: Optional[Location] = None
    action: Optional[Action] = None
    objective: Optional[str] = None
    thought: Optional[str] = None


@app.post("/agents/{agent_id}")
async def create_agent(agent_id: str, location: Location):
    success = office.add_agent(agent_id, location)
    if not success:
        raise HTTPException(status_code=400, message="Location at capacity")
    return {"status": "success"}


@app.put("/agents/{agent_id}")
async def update_agent(agent_id: str, update: AgentUpdate):
    success = office.update_agent(
        agent_id, update.location, update.action, update.objective, update.thought
    )
    if not success:
        raise HTTPException(status_code=404, message="Agent not found")
    return {"status": "success"}
