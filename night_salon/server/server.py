from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from night_salon.controllers.environment import EnvironmentController
from night_salon.server.event_handler import EventHandler
from night_salon.server.websocket_manager import WebSocketManager
from night_salon.utils.logger import logger
import json

# Define globals first
env_controller = EnvironmentController()  # Shared environment instance
websocket_manager = WebSocketManager(env_controller)  # WebSocket manager

app = FastAPI()

# Middleware must be added right after creating the app instance, before it starts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    try:
        await websocket_manager.connect(websocket)
        
        # Main message receiving loop
        while websocket_manager.is_connected(websocket):
            try:
                data = await websocket.receive_text()
                await websocket_manager.process_message(websocket, data)
            except WebSocketDisconnect:
                logger.info("Client disconnected during message processing")
                websocket_manager.disconnect(websocket)
                break
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}", exc_info=True)
                # Try to send error response if possible
                try:
                    if websocket_manager.is_connected(websocket):
                        await websocket.send_json({"status": "error", "message": "Error processing message"})
                except Exception:
                    pass
                websocket_manager.disconnect(websocket)
                break
                
    except WebSocketDisconnect:
        logger.info("Client disconnected during connection setup")
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Connection error: {str(e)}", exc_info=True)
        websocket_manager.disconnect(websocket)
        try:
            await websocket.close(code=1011)
        except Exception:
            # We don't need to log this - it's likely the connection is already closed
            pass

@app.get("/send-random-move/{agent_id}")
async def send_random_move_command(agent_id: str):
    """API endpoint to trigger a random move command for an agent"""
    if not websocket_manager.connected_clients:
        return {"status": "error", "message": "No connected clients"}
    
    if agent_id not in env_controller.agents:
        return {"status": "error", "message": f"Agent {agent_id} not found"}
        
    command = EventHandler.generate_random_movement_command(agent_id, env_controller)
    if not command:
        return {"status": "error", "message": "Failed to generate movement command"}
    
    return await websocket_manager.broadcast_command(command)

@app.get("/send-random-move-all")
async def send_random_move_all():
    """API endpoint to trigger random moves for all agents"""
    if not websocket_manager.connected_clients:
        return {"status": "error", "message": "No connected clients"}
    
    if not env_controller.agents:
        return {"status": "error", "message": "No agents registered"}
    
    results = []
    failures = 0
    
    for agent_id in env_controller.agents:
        command = EventHandler.generate_random_movement_command(agent_id, env_controller)
        if command:
            result = await websocket_manager.broadcast_command(command)
            failures += result.get("failed", 0)
            results.append({
                "agent_id": agent_id, 
                "command": command,
                "sent_to": result.get("sent_to", 0)
            })
    
    return {
        "status": "success" if failures == 0 else "partial_success",
        "results": results,
        "failures": failures
    }




