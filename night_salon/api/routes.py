from flask import Flask, jsonify, abort

from night_salon.state import CoordinatorState
from utils.types import AgentStatus

state: CoordinatorState = None


def init_routes(coordinator_state: CoordinatorState, app: Flask):
    global state
    state = coordinator_state

    @app.route("/")
    def read_root():
        return {"Hello": "World"}

    @app.route("/agents/<agent_id>", methods=['POST'])
    def create_agent(agent_id: str):
        success = state.create_agent(agent_id)
        if not success:
            abort(400, "Agent already exists")
        return jsonify({"status": "created"})

    @app.route("/agents", methods=['GET'])
    def list_agents():
        return jsonify(list(state.agents.keys()))

    @app.route("/agents/<agent_id>", methods=['GET'])
    def get_agent(agent_id: str):
        agent = state.agents.get(agent_id)
        if not agent:
            abort(404, "Agent not found")
        return jsonify(
            {
                "agent_id": agent.id,
                "location": agent.functional_state.location.name,
                "action": agent.functional_state.current_action.name,
                "animation": agent.functional_state.current_animation,
                "objective": agent.cognitive_state.objective,
                "thought": agent.cognitive_state.thought,
                "emotion": agent.cognitive_state.emotion,
            }
        )

    @app.route("/agents/<agent_id>", methods=['DELETE'])
    def remove_agent(agent_id: str):
        if agent_id not in state.agents:
            abort(404, "Agent not found")

        if agent_id in state.agent_tasks:
            task = state.agent_tasks.pop(agent_id)
            task.cancel()

        state.agents.pop(agent_id)
        return jsonify({"status": "removed"})
