import socket
import json
import threading
from typing import Dict, Optional, Callable
from night_salon.utils.logger import setup_logger

logger = setup_logger(__name__)

class UnityClient:
    def __init__(self, udp_port: int = 8054):
        # UDP Server for receiving events from Unity
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(('127.0.0.1', udp_port))
        
        # Callback registry for different event types
        self.event_handlers: Dict[str, Callable] = {}
        
        # Start UDP listener thread
        self._start_event_listener()

    def _start_event_listener(self):
        threading.Thread(target=self._listen_for_events, daemon=True).start()

    def _listen_for_events(self):
        logger.info("Started listening for Unity events...")
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                event = json.loads(data.decode())
                
                # Extract event type and data
                event_type = event.get('type')
                if event_type == 'state_change':
                    agent_id = event.get('agent_id')
                    new_state = event.get('data', {})
                    if agent_id and 'state' in new_state:
                        # Call handler with agent_id and new state
                        self.event_handlers.get('state_change', lambda *args: None)(agent_id, new_state)
                
                if event_type and event_type in self.event_handlers:
                    self.event_handlers[event_type](event_data)
                else:
                    logger.debug(f"Received unhandled Unity event: {event}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Unity event: {e}")
            except Exception as e:
                logger.error(f"Error receiving Unity event: {e}")

    def register_handler(self, event_type: str, handler: Callable):
        """Register a callback function for a specific event type"""
        self.event_handlers[event_type] = handler

    
def send_agent_update(self, agent_id: str, state_update: dict):
    """Send agent state updates to Unity via UDP"""
    try:
        message = {
            "type": "agent_update",
            "agent_id": agent_id,
            "data": state_update
        }
        data = json.dumps(message).encode()
        self.udp_socket.sendto(data, ('127.0.0.1', 8055))  # Assuming Unity listens on port 8055
    except Exception as e:
        logger.error(f"Failed to send agent update to Unity: {e}")