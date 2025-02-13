import httpx
from typing import Dict
import asyncio

from night_salon.unity.client import UnityClient
from night_salon.agents.worker import WorkerAgent
from night_salon.agents.base import BaseAgent
from utils.types import Location
from utils.logger import logger


class CoordinatorState:
    def __init__(
        self,
        unity_url: str,
        unity_host: str = "127.0.0.1",
        unity_tcp_port: int = 8052,
    ):
        self.unity_url = unity_url
        self.agents: Dict[str, WorkerAgent] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        self.unity_client = UnityClient(
            unity_host=unity_host,
            unity_tcp_port=unity_tcp_port,
        )

        self.unity_client.register_handler("state_change", self._handle_state_change)
        self.unity_client.register_handler("position_update", self._handle_position_update)
        self.unity_client.register_handler("destination_change", self._handle_destination_change)

    async def create_agent(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            return False

        agent = WorkerAgent(agent_id, self.unity_url)
        self.agents[agent_id] = agent

        return True
    
    def _handle_position_update(self, agent_id:str, position_data: dict):
        """Handle position updates from Unity"""
        # logger.info(f"Received position update for agent {agent_id}: {position_data}")
        if not agent_id in self.agents:
            asyncio.run(self.create_agent(agent_id=agent_id))
            if not agent_id in self.agents:
                logger.error(f"Failed to create agent {agent_id}")
                return
        agent = self.agents[agent_id]
        pass

    def _handle_destination_change(self, agent_id: str, destination_data: dict):
        """Handle destination changes from Unity"""
        logger.info(f"Received destination change for agent {agent_id}: {destination_data}")
        if not agent_id in self.agents:
            asyncio.run(self.create_agent(agent_id=agent_id))
            if not agent_id in self.agents:
                logger.error(f"Failed to create agent {agent_id}")
                return
        agent = self.agents[agent_id]
        # TODO: Update agent's destination information if needed
        pass

    def _handle_state_change(self, agent_id: str, new_state: dict):
        """Handle state changes from Unity"""
        logger.info(f"Received state change for agent {agent_id}: {new_state}")
        if not agent_id in self.agents:
            asyncio.run(self.create_agent(agent_id=agent_id))
            if not agent_id in self.agents:
                logger.error(f"Failed to create agent {agent_id}")
                return
        agent = self.agents[agent_id]

        if "state" in new_state:
            unity_state = new_state["state"]
            # Map Unity states to emotions
            state_to_emotion = {"walking": "active", "standing": "idle"}

            # Update cognitive state
            agent.cognitive_state.emotion = state_to_emotion.get(unity_state, "neutral")

            # Generate new objective and thought based on state
            if unity_state == "walking":
                agent.cognitive_state.objective = "Moving to new location"
                agent.cognitive_state.thought = agent._generate_movement_thought()
            elif unity_state == "standing":
                agent.cognitive_state.objective = "Taking a moment"
                agent.cognitive_state.thought = "Just another moment in the day"

            # Send updated state back to Unity
            state_update = {
                "objective": agent.cognitive_state.objective,
                "thought": agent.cognitive_state.thought,
                "emotion": agent.cognitive_state.emotion,
                "current_action": unity_state,
                "current_animation": unity_state  # You might want to map this differently
            }
            self.unity_client.send_agent_update(agent_id, state_update)

    async def _agent_loop(self, agent: BaseAgent):
        """Remove the automatic decision making - only react to Unity state changes"""
        try:
            while True:
                # Just keep the loop alive but don't make autonomous decisions
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in agent loop for {agent.id}: {e}")
