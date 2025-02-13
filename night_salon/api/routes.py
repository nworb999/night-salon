from flask import Flask, jsonify, abort, request

from night_salon.state import CoordinatorState
from utils.types import AgentStatus
from utils.logger import logger

state: CoordinatorState = None


def init_routes(coordinator_state: CoordinatorState, app: Flask):
    global state
    state = coordinator_state

    @app.route("/")
    def read_root():
        return {"Hello": "World"}

    @app.route("/agents/<agent_id>", methods=['POST'])
    def create_agent(agent_id: str):
        """Create a new agent."""
        if state.create_agent(agent_id):
            return jsonify({"message": f"Agent {agent_id} created."}), 201
        else:
            return jsonify({"message": f"Agent {agent_id} already exists."}), 409

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

    @app.route("/agents/<agent_id>/state", methods=["POST"])
    def update_agent_state(agent_id: str):
        """Update an agent's state."""
        try:
            # Check if the content type is application/json
            if request.content_type != 'application/json':
                return jsonify({"error": "Content type must be application/json"}), 400

            # Parse JSON data from the request body
            try:
                data = request.get_json()
            except Exception as e:
                return jsonify({"error": f"Failed to parse JSON: {str(e)}"}), 400

            if not data:
                return jsonify({"error": "Request body must be JSON"}), 400

            objective = data.get("objective")
            thought = data.get("thought")
            emotion = data.get("emotion")

            if objective is None or thought is None or emotion is None:
                return jsonify({"error": "Missing required fields"}), 400

            # Log the received data
            logger.info(f"Received state update for agent {agent_id}: {data}")

            # Send agent state updates to Unity via TCP
            state.unity_client.send_agent_update(agent_id, data)

            return jsonify({"message": f"Agent {agent_id} state updated."}), 200
        except Exception as e:
            logger.error(f"Error updating agent state: {e}")
            return jsonify({"error": str(e)}), 500
