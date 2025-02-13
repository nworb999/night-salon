import socket
import json
import threading
from typing import Dict, Callable
from utils.logger import logger


class UnityClient:
    def __init__(
        self,
        unity_host: str = "127.0.0.1",
        unity_tcp_port: int = 8052,
    ):
        """
        Initialize UnityClient with TCP sending and receiving capabilities

        Args:
            unity_tcp_port: Unity's TCP port for requests
        """
        # TCP Socket for making requests to Unity
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.unity_host = unity_host
        self.unity_tcp_port = unity_tcp_port

        # Callback registry for different event types
        self.event_handlers: Dict[str, Callable] = {
            "state_change": self._default_state_handler,
            "position_update": self._default_position_handler,
            "destination_change": self._default_destination_handler,
        }

        # Start UDP listener thread
        try:
            self._start_event_listener()
        except Exception as e:
            logger.error(f"Error starting event listener: {e}", exc_info=True)

        logger.info(
            f"UnityClient initialized - TCP port: {unity_tcp_port}"
        )

    def _default_state_handler(self, agent_id: str, state_data: dict):
        """Default handler for state change events"""
        logger.info(f"State change for agent {agent_id}: {state_data}")

    def _default_position_handler(self, agent_id:str, position_data: dict):
        """Default handler for position update events"""
        logger.info(f"Position update: {agent_id} : {position_data}")

    def _default_destination_handler(self, agent_id: str, destination_data: dict):
        """Default handler for destination change events"""
        logger.info(f"Destination change for agent {agent_id}: {destination_data}")

    def send_request(self, request_type: str) -> dict:
        """Send TCP request to Unity and get response"""
        try:
            # Connect to Unity's TCP server
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.unity_host, self.unity_tcp_port))

            # Send request
            self.tcp_socket.send(request_type.encode())

            # Receive response
            response = self.tcp_socket.recv(1024).decode()
            return json.loads(response)
        except Exception as e:
            logger.error(f"Failed to send TCP request to Unity: {e}")
            return {"error": str(e)}
        finally:
            self.tcp_socket.close()

    def _start_event_listener(self):
        """Start TCP listener thread"""
        threading.Thread(target=self._listen_for_events, daemon=True).start()
        logger.info("Started TCP event listener thread")

    def _handle_event(self, event_type: str, agent_id: str = None, event_data: dict = None):
        """Handle event"""
        if event_type in self.event_handlers:
            handler = self.event_handlers[event_type]
            try:
                if agent_id:
                    handler(agent_id, event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.error(f"[HANDLE EVENT] Error in handler: {str(e)}", exc_info=True)
        else:
            logger.warning(f"[HANDLE EVENT] No handler found for event type: {event_type}")

    def _listen_for_events(self):
        """Listen for TCP events from Unity"""
        # Create a TCP socket to listen for incoming messages
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', self.unity_tcp_port))  # Listen on all interfaces
        server_socket.listen(5)  # Listen for incoming connections (adjust backlog as needed)

        while True:
            try:
                conn, addr = server_socket.accept()
                with conn:
                    logger.info(f"Connected by {addr}")
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        try:
                            message = json.loads(data.decode())
                            event_type = message.get("type")
                            agent_id = message.get("agent_id")
                            event_data = message.get("data")
                            self._handle_event(event_type, agent_id, event_data)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode message: {data}")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error in event listener: {e}", exc_info=True)

    def register_handler(self, event_type: str, handler: Callable):
        """Register a callback function for a specific event type"""
        logger.info(f"Registering handler for event type: {event_type}")
        self.event_handlers[event_type] = handler


    def send_agent_update(self, agent_id: str, state_update: dict):
        """Send agent state updates to Unity via TCP"""
        try:
            # Connect to Unity's TCP server
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            temp_socket.connect((self.unity_host, self.unity_tcp_port))

            message = {
                "type": "agent_update",
                "agent_id": agent_id,
                "data": state_update,
            }
            logger.debug(f"Sending agent update to Unity: {message}")
            data = json.dumps(message).encode()
            temp_socket.send(data)
            logger.info(f"Successfully sent update for agent {agent_id}")
            temp_socket.close()
        except Exception as e:
            logger.error(f"Failed to send agent update to Unity: {e}")

    def __del__(self):
        """Cleanup sockets on deletion"""
        try:
            self.tcp_socket.close()
        except:
            pass
