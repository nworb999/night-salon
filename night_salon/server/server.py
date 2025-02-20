from typing import Dict
from uuid import uuid4
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from config import Config
from config.logger import logger
from night_salon.models import Agent, UnityEvent, Location, LocationData, WebsocketConnect, ClientWebsocketEvent
from night_salon.cognitive.state_manager import StateManager

config = Config()

# Remove the entire CORS middleware configuration block
app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_agents: Dict[str, dict] = {}  # Track agents per client
        self.allowed_origins = [
            "http://localhost",
            "https://localhost",
            "http://localhost:*",
            "https://localhost:*",
            "unity://*",
            "null",  # Allow null origin
            ""  # Allow empty origin
        ]

    async def connect(self, websocket: WebSocket):
        """Enhanced connection handler with detailed logging"""
        try:
            origin = websocket.headers.get('origin', '')
            logger.debug(f"WebSocket connection attempt from origin: {origin}")
            logger.debug("Incoming WebSocket connection headers:")
            for header, value in websocket.headers.items():
                logger.debug(f"{header}: {value}")

            # Simplified development mode handling
            if config.ENV == "development":
                await websocket.accept()
                client_id = str(uuid4())
                self.active_connections[client_id] = websocket
                self.client_agents[client_id] = {}
                logger.info(f"Dev mode connection accepted - Client ID: {client_id}")
                return client_id

            # Production origin checking
            if self._is_origin_allowed(origin):
                await websocket.accept()
                client_id = str(uuid4())
                self.active_connections[client_id] = websocket
                self.client_agents[client_id] = {}
                logger.info(f"Connection accepted - Client ID: {client_id}")
                return client_id
            else:
                logger.warning(f"Connection rejected - Invalid origin: {origin}")
                await websocket.close(code=1003, reason="Invalid origin")
                return None
                
        except Exception as e:
            logger.error(f"Error during WebSocket connection: {e}")
            raise

    def _is_origin_allowed(self, origin: str) -> bool:
        if not origin or origin == "null":
            return True
            
        return any(
            allowed.replace("*", "") in origin 
            for allowed in self.allowed_origins
        )

    def disconnect(self, client_id: str):
        del self.active_connections[client_id]
        del self.client_agents[client_id]

manager = ConnectionManager()

class Server:
    def __init__(self):
        self.state_manager = StateManager()
        self.agent_storage_file = "agent_states.json"
        self.environment_locations = {loc: LocationData(loc, []) for loc in Location}

    # Modified WebSocket handler with enhanced logging
    @app.websocket("/ws/py_client")
    async def websocket_endpoint(self, websocket: WebSocket):
        try:
            client_id = await manager.connect(websocket)
            if not client_id:
                return

            # Send immediate confirmation message
            await websocket.send_json({
                "event": "connect",
                "data": {
                    "status": "granted",
                    "client_id": client_id
                }
            })

            while True:
                message = await websocket.receive_text()
                logger.debug(f"Received message from client {client_id}: {message}")
                
                try:
                    response = await self.process_websocket_message(message, client_id)
                    await websocket.send_json(response)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send_json({
                        "event": "error",
                        "data": {"message": str(e)}
                    })

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
            manager.disconnect(client_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            try:
                await websocket.close(code=1011)  # Internal error
            except:
                pass
            manager.disconnect(client_id)

    async def process_websocket_message(self, message: str, client_id: str):
        try:
            # Validate message with Pydantic
            ws_message = ClientWebsocketEvent.parse_raw(message)
            
            if ws_message.event == "connect":
                return self.handle_connect(client_id)
                
            elif ws_message.event == "setup":
                return self.process_setup(ws_message.data, client_id)
                
            elif ws_message.event == "state_update":
                agent_id = ws_message.data.get("agent_id")
                state_data = ws_message.data.get("state")
                agent = self.get_or_create_agent(agent_id, client_id)
                event = UnityEvent(
                    type=ws_message.event,
                    agent_id=agent_id,
                    data=json.loads(state_data) if state_data else {}
                )
                new_destination = self.state_manager.process_event(agent, event)
                return self.format_response(agent_id, new_destination)
                
            else:
                return {"event": "error", "message": "Unknown event type"}

        except Exception as e:
            logger.error(f"Message processing error: {e}")
            return {"event": "error", "message": str(e)}

    def handle_connect(self, client_id: str):
        """Handle initial connection handshake"""
        return {
            "event": "connect",
            "data": {
                "status": "granted",
                "client_id": client_id
            }
        }

    def get_or_create_agent(self, agent_id: str, client_id: str):
        """Get or create agent scoped to specific client"""
        if agent_id not in manager.client_agents[client_id]:
            manager.client_agents[client_id][agent_id] = Agent(agent_id)
        return manager.client_agents[client_id][agent_id]

    def format_response(self, agent_id: str, destination: str):
        if destination:
            return {
                "event": "destination_update",
                "agent_id": agent_id,
                "destination": destination
            }
        return {
            "event": "no_update",
            "agent_id": agent_id
        }

    # Keep existing process_setup and _map_location methods but add client_id parameter
    def process_setup(self, setup_data: dict, client_id: str):
        try:
            agent_ids = setup_data.get("agent_ids", [])
            cameras = setup_data.get("cameras", [])
            manager.client_agents[client_id] = {
                agent_id: Agent(agent_id) for agent_id in agent_ids
            }
            
            locations_data = setup_data.get("locations", [])
            for location_name in locations_data:
                mapped_location = self._map_location(location_name)
                if mapped_location:
                    self.environment_locations[mapped_location].sub_locations.append(location_name)
            
            return {"event": "setup_complete", "client_id": client_id}
            
        except Exception as e:
            logger.error(f"Setup error: {e}")
            return {"event": "error", "message": str(e)}

    def _map_location(self, location_name):
        """
        Map incoming location names to defined Location enum values using simple pattern matching.
        """
        location_name = location_name.upper()
        
        # Direct mapping if exact match exists
        if location_name in Location.__members__:
            return Location[location_name]
        
        # Fuzzy mapping patterns
        mapping_patterns = {
            'CHAIR': Location.CUBICLES,
            'DESK': Location.CUBICLES,
            'OFFICE': Location.CUBICLES,
            'ARMCHAIR': Location.CONFERENCE_ROOM,
            'COUCH': Location.CONFERENCE_ROOM,
            'TABLE': Location.CONFERENCE_ROOM,
            'WATER': Location.WATER_COOLER,
            'COOLER': Location.WATER_COOLER,
            'BATHROOM': Location.BATHROOM,
            'RESTROOM': Location.BATHROOM,
            'TOILET': Location.BATHROOM,
            'SMOKING': Location.SMOKING_AREA,
            'HALL': Location.HALLWAY,
            'CORRIDOR': Location.HALLWAY
        }

        # Check if any pattern matches the location name
        for pattern, location in mapping_patterns.items():
            if pattern in location_name:
                return location

        return None

    def _save_agent_states(self):
        """Persist agent states to disk"""
        try:
            states = {
                agent_id: agent.state 
                for agent_id, agent in self.agents.items()
            }
            with open(self.agent_storage_file, 'w') as f:
                json.dump(states, f, default=str)  # Handle enum serialization
        except Exception as e:
            logger.error(f"Error saving agent states: {e}")

    def _load_agent_states(self):
        """Load persisted agent states from disk"""
        try:
            with open(self.agent_storage_file, 'r') as f:
                states = json.load(f)
                for agent_id, state in states.items():
                    agent = Agent(agent_id)
                    agent.state = state
                    self.agents[agent_id] = agent
        except FileNotFoundError:
            logger.info("No existing agent states found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading agent states: {e}")




