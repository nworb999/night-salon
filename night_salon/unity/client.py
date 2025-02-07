import socket
import json
import asyncio
import threading
from typing import Dict, Callable
from utils.logger import logger


class UnityClient:
    def __init__(
        self,
        bind_host: str = "0.0.0.0",
        unity_host: str = "127.0.0.1",
        udp_receive_port: int = 8001,
        unity_tcp_port: int = 8052,
        unity_udp_port: int = 8053,
    ):
        """
        Initialize UnityClient with both sending and receiving capabilities

        Args:
            udp_receive_port: Port to receive UDP events from Unity
            unity_tcp_port: Unity's TCP port for requests
            unity_udp_port: Unity's UDP port for sending updates
        """
        # TCP Socket for making requests to Unity
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # UDP Socket for receiving events from Unity
        self.udp_receive_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_receive_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_receive_socket.bind((bind_host, udp_receive_port))

        # UDP Socket for sending updates to Unity
        self.udp_send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Unity server details
        self.unity_host = unity_host
        self.unity_tcp_port = unity_tcp_port
        self.unity_udp_port = unity_udp_port

        # Callback registry for different event types
        self.event_handlers: Dict[str, Callable] = {
            "state_change": self._default_state_handler,
            "position_update": self._default_position_handler,
            "destination_change": self._default_destination_handler,
        }

        self.loop = asyncio.new_event_loop()

        # Start UDP listener thread
        self._start_event_listener()

        logger.info(
            f"UnityClient initialized - TCP port: {unity_tcp_port}, UDP receive port: {udp_receive_port}, UDP send port: {unity_udp_port}"
        )

    def _default_state_handler(self, agent_id: str, state_data: dict):
        """Default handler for state change events"""
        # logger.info(f"State change for agent {agent_id}: {state_data}")

    def _default_position_handler(self, position_data: dict):
        """Default handler for position update events"""
        # logger.info(f"Position update: {position_data}")

    def _default_destination_handler(self, agent_id: str, destination_data: dict):
        """Default handler for destination change events"""
        # logger.info(f"Destination change for agent {agent_id}: {destination_data}")

    def send_request(self, request_type: str) -> dict:
        """Send TCP request to Unity and get response"""
        try:
            # Connect to Unity's TCP server
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
        """Start UDP listener thread"""
        threading.Thread(target=self._listen_for_events, daemon=True).start()
        logger.info("Started UDP event listener thread")

    async def _handle_event(self, event_type: str, agent_id: str = None, event_data: dict = None):
        """Handle event with proper async support"""
        if event_type in self.event_handlers:
            handler = self.event_handlers[event_type]
            if agent_id:
                await handler(agent_id, event_data)
            else:
                await handler(event_data)

    def _listen_for_events(self):
        """Listen for UDP events from Unity"""
        asyncio.set_event_loop(self.loop)
        
        logger.info("Started listening for Unity events...")
        while True:
            try:
                logger.debug("Waiting for UDP data...")
                data, addr = self.udp_receive_socket.recvfrom(1024)
                logger.debug(f"Raw data received from {addr}: {data}")

                decoded_data = data.decode()
                logger.debug(f"Decoded data: {decoded_data}")

                event = json.loads(decoded_data)
                logger.debug(f"Parsed event: {event}")

                # Extract event type and data
                event_type = event.get("type")
                agent_id = event.get("agent_id")
                event_data = event.get("data")

                logger.debug(
                    f"Extracted fields - type: {event_type}, agent_id: {agent_id}, data: {event_data}"
                )

                if event_type == "state_change":
                    if agent_id:
                        try:
                            new_state = (
                                json.loads(event_data)
                                if isinstance(event_data, str)
                                else event_data
                            )
                            # Run the handler in the event loop
                            self.loop.create_task(self._handle_event("state_change", agent_id, new_state))
                        except json.JSONDecodeError as je:
                            logger.error(
                                f"Failed to parse state data: {je}, raw data: {event_data}"
                            )
                    else:
                        logger.warning("Received state_change event without agent_id")

                elif event_type == "position_update":
                    try:
                        position_data = (
                            json.loads(event_data)
                            if isinstance(event_data, str)
                            else event_data
                        )
                        self.loop.create_task(self._handle_event("position_update", None, position_data))
                    except json.JSONDecodeError as je:
                        logger.error(
                            f"Failed to parse position data: {je}, raw data: {event_data}"
                        )

                elif event_type == "destination_change":
                    if agent_id:
                        try:
                            destination_data = (
                                json.loads(event_data)
                                if isinstance(event_data, str)
                                else event_data
                            )
                            self.loop.create_task(self._handle_event("destination_change", agent_id, destination_data))
                        except json.JSONDecodeError as je:
                            logger.error(
                                f"Failed to parse destination data: {je}, raw data: {event_data}"
                            )
                    else:
                        logger.warning("Received destination_change event without agent_id")

                elif event_type and event_type in self.event_handlers:
                    logger.info(f"Processing event type: {event_type}")
                    if event_type not in ["state_change", "position_update", "destination_change"]:
                        self.loop.create_task(self._handle_event(event_type, None, event_data))
                else:
                    logger.warning(f"Received unhandled Unity event type: {event_type}")

            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse Unity event: {e}, raw data: {data if 'data' in locals() else 'N/A'}"
                )
            except Exception as e:
                logger.error(f"Error receiving Unity event: {e}", exc_info=True)

    def register_handler(self, event_type: str, handler: Callable):
        """Register a callback function for a specific event type"""
        logger.info(f"Registering handler for event type: {event_type}")
        self.event_handlers[event_type] = handler

    def send_agent_update(self, agent_id: str, state_update: dict):
        """Send agent state updates to Unity via UDP"""
        try:
            message = {
                "type": "agent_update",
                "agent_id": agent_id,
                "data": state_update,
            }
            logger.debug(f"Sending agent update to Unity: {message}")
            data = json.dumps(message).encode()
            self.udp_send_socket.sendto(data, (self.unity_host, self.unity_udp_port))
            logger.info(f"Successfully sent update for agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to send agent update to Unity: {e}")

    def __del__(self):
        """Cleanup sockets on deletion"""
        try:
            self.tcp_socket.close()
            self.udp_receive_socket.close()
            self.udp_send_socket.close()
        except:
            pass
