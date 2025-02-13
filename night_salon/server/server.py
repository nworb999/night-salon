import json
import socket
import time
import traceback
import sys
from config import Config
from night_salon.utils.types import Agent
from night_salon.models.events import UnityEvent
from night_salon.cognitive.state_manager import StateManager
from config.logger import logger

config = Config()

class Server:
    def __init__(self):
        self.state_manager = StateManager()
        self.agents = {}  # Store active agents
        self.client_socket = None
        self.server_socket = None  # Add server socket

    def receive_message(self):
        try:
            # Read message length (4 bytes, little endian)
            length_bytes = self.client_socket.recv(4)
            if not length_bytes:
                raise ConnectionError("Client disconnected (length)")
            message_length = int.from_bytes(length_bytes, byteorder='little')

            # Read exact message length
            remaining = message_length
            chunks = []
            while remaining > 0:
                chunk = self.client_socket.recv(remaining)
                if not chunk:
                    raise ConnectionError("Client disconnected (data)")
                chunks.append(chunk)
                remaining -= len(chunk)

            raw_message = b''.join(chunks)
            message = raw_message.decode('utf-8')
            return message
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            raise

    def send_message(self, message):
        try:
            message_bytes = message.encode('utf-8')
            # Send length prefix first (4 bytes, little endian)
            length_prefix = len(message_bytes).to_bytes(4, byteorder='little')
            self.client_socket.sendall(length_prefix)
            # Then send the actual message
            self.client_socket.sendall(message_bytes)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise

    def process_message(self, message):
        try:
            # Split message by pipe character
            parts = message.split('|')
            if len(parts) != 3:
                raise ValueError("Message format incorrect - expected 3 parts separated by '|'")

            event_type = parts[0]
            agent_id = parts[1]
            data = json.loads(parts[2])
            print(event_type + "\n")
            
            if event_type == "position_update":
                # Get or create agent
                agent = self.agents.get(agent_id)
                if not agent:
                    agent = Agent(agent_id)
                    self.agents[agent_id] = agent
                
                # Create a UnityEvent object instead of a dictionary
                event = UnityEvent(
                    type=event_type,
                    agent_id=agent_id,
                    position=data.get('position'),
                    velocity=data.get('velocity'),
                    speed=data.get('speed')
                )
                updated_state = self.state_manager.process_event(agent, event)
                return {
                    "type": "cognitive_update",
                    "agent_id": agent_id,
                    "state": updated_state
                }

            return {"type": "error", "message": "Unknown event type"}

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {message}")
            return {"type": "error", "message": f"Invalid JSON: {str(e)}"}
        except Exception as e:
            exc_info = sys.exc_info()
            stack = traceback.extract_tb(exc_info[2])
            line_number = stack[-1].lineno if stack else 'unknown'
            logger.error(f"Error in {__name__} line {line_number}: {str(e)}")
            logger.debug(f"Full traceback:\n{''.join(traceback.format_exception(*exc_info))}")
            return {"type": "error", "message": f"{e.__class__.__name__} at {__name__}:{line_number}: {str(e)}"}

    def start(self):
        client_address = (config.unity_host, config.unity_port)  # Unity server address

        while True:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                logger.info("Attempting to connect to Unity server...")
                self.client_socket.connect(client_address)  # Connect to Unity's server
                logger.info(f"Connected to Unity server at {client_address}")
                break
            except ConnectionRefusedError:
                logger.warning("Connection failed. Retrying in 2 seconds...")
                self.client_socket.close()  # Make sure to close the socket before retrying
                time.sleep(2)
            except KeyboardInterrupt:
                logger.info("\nConnection attempts cancelled by user.")
                return
            except Exception as e:
                logger.error(f"Connection error: {e}")
                self.client_socket.close()  # Make sure to close the socket before retrying
                time.sleep(2)

        try:
            while True:
                try:
                    # Receive update from Unity
                    message = self.receive_message()
                    if message:
                        logger.info(f"Received: {message}")

                        # Process message and prepare response
                        response = self.process_message(message)
                        response_json = json.dumps(response)

                        # Send response back to Unity
                        self.send_message(response_json)
                        logger.info(f"Sent response: {response_json}")

                    time.sleep(0.01)  # Small delay to prevent busy-waiting

                except (ConnectionAbortedError, ConnectionResetError) as e:
                    logger.error(f"\nConnection lost: {e}")
                    self.client_socket.close()
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    self.client_socket.close()
                    break

        except KeyboardInterrupt:
            logger.info("\nClosing connection...")
            if self.client_socket:
                self.client_socket.close()



