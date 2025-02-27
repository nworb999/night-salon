from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from night_salon.controllers.environment import EnvironmentController
from night_salon.server.event_handler import EventHandler
from night_salon.utils.logger import logger
import json
import asyncio
import random

# Define globals first
env_controller = EnvironmentController()  # Shared environment instance
connected_clients = set()  # Track connected clients


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
    await websocket.accept()
    connected_clients.add(websocket)
    logger.info("New client connected")
    try:
        while True:
            data = await websocket.receive_text()
            try:
                event = json.loads(data)
                event_type = event.get("messageType")
                event_data = {k: v for k, v in event.items() if k != "messageType"}
                logger.debug(f"Received event: {event_type}")
                
                # Process the event
                if event_type == "setup":
                    # Special handling for setup to return move commands
                    move_commands = await EventHandler.handle_event(event_type, event_data, env_controller)
                    
                    # First send success response
                    await websocket.send_json({"status": "success"})
                    
                    # Then send each move command with a small delay between them
                    logger.info(f"Sending {len(move_commands)} initial move commands to client")
                    for command in move_commands:
                        await asyncio.sleep(random.uniform(0.5, 1.5))  # Small delay between commands
                        await websocket.send_json(command)
                        logger.debug(f"Sent initial move command for agent {command['agent_id']} to {command['location_name']}")
                elif event_type == "location_reached":
                    # First update agent location and get next move command
                    next_move_command = await EventHandler.handle_event(event_type, event_data, env_controller)
                    
                    # Send success response
                    await websocket.send_json({"status": "success"})
                    
                    # Send next move command if one was generated
                    if next_move_command:
                        await asyncio.sleep(random.uniform(0.5, 1.5))  # Small delay before sending next move
                        await websocket.send_json(next_move_command)
                        logger.info(f"Sent next move command for agent {next_move_command['agent_id']} to {next_move_command['location_name']}")
                else:
                    # Normal handling for other event types
                    await EventHandler.handle_event(event_type, event_data, env_controller)
                    await websocket.send_json({"status": "success"})
                
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received")
                await websocket.send_json({"status": "error", "message": "Invalid JSON format"})
                
            except Exception as e:
                logger.error(f"Error processing event: {str(e)}", exc_info=True)
                await websocket.send_json({"status": "error", "message": str(e)})

    except WebSocketDisconnect:
        logger.info("Client disconnected")
        connected_clients.remove(websocket)
    except Exception as e:
        logger.error(f"Connection error: {str(e)}", exc_info=True)
        await websocket.close(code=1011)
        if websocket in connected_clients:
            connected_clients.remove(websocket)

@app.get("/send-random-move/{agent_id}")
async def send_random_move_command(agent_id: str):
    """API endpoint to trigger a random move command for an agent"""
    if not connected_clients:
        return {"status": "error", "message": "No connected clients"}
    
    if agent_id not in env_controller.agents:
        return {"status": "error", "message": f"Agent {agent_id} not found"}
        
    command = EventHandler.generate_random_movement_command(agent_id, env_controller)
    if not command:
        return {"status": "error", "message": "Failed to generate movement command"}
    
    # Send to all connected clients
    for client in connected_clients:
        try:
            await client.send_json(command)
        except Exception as e:
            logger.error(f"Error sending command to client: {str(e)}")
    
    return {"status": "success", "command": command}

@app.get("/send-random-move-all")
async def send_random_move_all():
    """API endpoint to trigger random moves for all agents"""
    if not connected_clients:
        return {"status": "error", "message": "No connected clients"}
    
    if not env_controller.agents:
        return {"status": "error", "message": "No agents registered"}
    
    results = []
    for agent_id in env_controller.agents:
        command = EventHandler.generate_random_movement_command(agent_id, env_controller)
        if command:
            # Send to all connected clients
            for client in connected_clients:
                try:
                    await client.send_json(command)
                except Exception as e:
                    logger.error(f"Error sending command to client: {str(e)}")
            results.append({"agent_id": agent_id, "command": command})
    
    return {"status": "success", "results": results}




