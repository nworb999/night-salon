from fastapi import WebSocket, WebSocketDisconnect
from night_salon.controllers.environment import EnvironmentController
from night_salon.server.event_handler import EventHandler
from night_salon.utils.logger import logger
import json
import asyncio
import random
from typing import Set, Dict, Any, Optional, List, Union

class WebSocketManager:
    """Manages WebSocket connections and event handling"""
    
    def __init__(self, env_controller: EnvironmentController):
        self.env_controller = env_controller
        self.connected_clients: Set[WebSocket] = set()
        self._active_connections = {}  # Track connection status
        
    async def connect(self, websocket: WebSocket) -> None:
        """Handle new client connection"""
        try:
            await websocket.accept()
            self.connected_clients.add(websocket)
            self._active_connections[id(websocket)] = True
            logger.info("New client connected")
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {str(e)}")
            # Don't add to connected_clients if accept fails
            
    def disconnect(self, websocket: WebSocket) -> None:
        """Handle client disconnection"""
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
        
        if id(websocket) in self._active_connections:
            self._active_connections.pop(id(websocket))
        
        logger.info("Client disconnected")
    
    def is_connected(self, websocket: WebSocket) -> bool:
        """Check if the websocket is still connected"""
        return id(websocket) in self._active_connections and websocket in self.connected_clients
        
    async def process_message(self, websocket: WebSocket, data: str) -> None:
        """Process an incoming message from the client"""
        try:
            event = json.loads(data)
            event_type = event.get("messageType")
            event_data = {k: v for k, v in event.items() if k != "messageType"}
            logger.debug(f"Received event: {event_type}")
            
            if event_type == "setup":
                await self._handle_setup_event(websocket, event_data)
            elif event_type == "location_reached":
                await self._handle_location_reached_event(websocket, event_data)
            else:
                await self._handle_generic_event(websocket, event_type, event_data)
                
        except json.JSONDecodeError:
            logger.warning("Invalid JSON received")
            await self._send_response(websocket, {"status": "error", "message": "Invalid JSON format"})
        except Exception as e:
            logger.error(f"Error processing event: {str(e)}", exc_info=True)
            await self._send_response(websocket, {"status": "error", "message": str(e)})
            
    async def _handle_setup_event(self, websocket: WebSocket, event_data: Dict[str, Any]) -> None:
        """Handle setup event and send initial move commands"""
        move_commands = await EventHandler.handle_event("setup", event_data, self.env_controller)
        
        # First send success response
        await self._send_response(websocket, {"status": "success"})
        
        # Then send move commands with delay
        logger.info(f"Sending {len(move_commands)} initial move commands to client")
        for command in move_commands:
            if not await self._send_delayed_command(websocket, command, 
                                                   f"agent {command['agent_id']} to {command['location_name']}"):
                break
                
    async def _handle_location_reached_event(self, websocket: WebSocket, event_data: Dict[str, Any]) -> None:
        """Handle location_reached event and send next move command"""
        next_move_command = await EventHandler.handle_event("location_reached", event_data, self.env_controller)
        
        # Send success response
        await self._send_response(websocket, {"status": "success"})
        
        # Send next move command if one was generated
        if next_move_command and websocket in self.connected_clients:
            await self._send_delayed_command(websocket, next_move_command, 
                                            f"agent {next_move_command['agent_id']} to {next_move_command['location_name']}")
                
    async def _handle_generic_event(self, websocket: WebSocket, event_type: str, event_data: Dict[str, Any]) -> None:
        """Handle other event types"""
        await EventHandler.handle_event(event_type, event_data, self.env_controller)
        await self._send_response(websocket, {"status": "success"})
        
    async def _send_response(self, websocket: WebSocket, response: Dict[str, Any]) -> bool:
        """Send a response to the client, return True if successful"""
        try:
            if self.is_connected(websocket):
                await websocket.send_json(response)
                return True
            else:
                logger.warning("Attempted to send response to disconnected client")
        except WebSocketDisconnect:
            logger.info("Client disconnected during response")
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error sending response: {str(e)}")
            self.disconnect(websocket)
        return False
        
    async def _send_delayed_command(self, websocket: WebSocket, command: Dict[str, Any], 
                                   log_message: str) -> bool:
        """Send a command with a random delay, return True if successful"""
        try:
            await asyncio.sleep(random.uniform(0.5, 1.5))  # Small delay
            
            # Check if client is still connected after delay
            if self.is_connected(websocket):
                await websocket.send_json(command)
                logger.info(f"Sent move command for {log_message}")
                return True
            else:
                logger.info("Client disconnected during delay, not sending command")
        except WebSocketDisconnect:
            logger.info(f"Client disconnected before sending command")
            self.disconnect(websocket)
        except Exception as e:
            logger.error(f"Error sending command: {str(e)}")
            self.disconnect(websocket)
        return False

    async def broadcast_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send a command to all connected clients"""
        failed_clients = []
        successful_sends = 0
        
        for client in list(self.connected_clients):
            try:
                await client.send_json(command)
                successful_sends += 1
            except Exception as e:
                logger.error(f"Error sending command to client: {str(e)}")
                failed_clients.append(client)
                self.disconnect(client)
        
        return {
            "status": "success" if successful_sends > 0 else "failure",
            "command": command,
            "sent_to": successful_sends,
            "failed": len(failed_clients)
        } 