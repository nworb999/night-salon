import json
import socket
import time
from config import Config
from night_salon.models.agent import Agent
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
            data = json.loads(message)
            event_type = data.get('type')
            agent_id = data.get('agent_id')

            if event_type == "agent_spawn":
                if agent_id not in self.agents:
                    self.agents[agent_id] = Agent(agent_id)
                    logger.info(f"Spawned agent {agent_id}")
                    return {"type": "spawn_confirmation", "agent_id": agent_id}

            elif event_type == "agent_update":
                agent = self.agents.get(agent_id)
                if agent:
                    updated_state = self.state_manager.process_event(agent, data)
                    return {
                        "type": "cognitive_update",
                        "agent_id": agent_id,
                        "state": updated_state
                    }

            return {"type": "error", "message": "Unknown event type"}

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message}")
            return {"type": "error", "message": "Invalid JSON"}
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {"type": "error", "message": str(e)}

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



