import json
import socket
import time
import traceback
import sys
from config import Config
from night_salon.models.agent import Agent
from night_salon.models.events import UnityEvent
from night_salon.cognitive.state_manager import StateManager
from config.logger import logger
from night_salon.models.environment import Location

config = Config()

class Server:
    def __init__(self):
        self.state_manager = StateManager()
        self.agents = {}  # Store active agents
        self.client_socket = None
        self.server_socket = None  # Add server socket
         # Add agent persistence file
        self.agent_storage_file = "agent_states.json"
        self.environment_locations = {} # Store environment locations

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

            if event_type == "setup":
                return self.process_setup(data)
            
            # Get or create agent (moved outside of position_update check)
            agent = self.agents.get(agent_id)
            if not agent:
                agent = Agent(agent_id)
                self.agents[agent_id] = agent
            
            # Create a UnityEvent object with all available data
            event = UnityEvent(
                type=event_type,
                agent_id=agent_id,
                data=data  # Pass raw data dictionary to be handled in state manager
            )
            
            # Process all event types through state manager
            updated_state = self.state_manager.process_event(agent, event)
            return {
                "type": "cognitive_update",
                "agent_id": agent_id,
                "state": updated_state
            }

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

    def process_setup(self, setup_data):
        """
        Process the initial setup data from Unity.
        This includes agent IDs and environment locations.
        """
        try:
            # Extract agent IDs
            agent_ids = setup_data.get("agent_ids", [])
            for agent_id in agent_ids:
                if agent_id not in self.agents:
                    self.agents[agent_id] = Agent(agent_id)
                    logger.info(f"Added agent {agent_id} from setup data.")

            # Extract environment locations
            locations_data = setup_data.get("locations", [])
            for location_name in locations_data:
                try:
                    location = Location[location_name.upper()]
                    self.environment_locations[location_name] = location
                    logger.info(f"Added location {location_name} from setup data.")
                except KeyError:
                    logger.warning(f"Invalid location name '{location_name}' in setup data.")
            print(self.environment_locations)
            print(self.agents)
            return {"type": "setup_complete", "message": "Setup processed successfully."}

        except Exception as e:
            logger.error(f"Error processing setup data: {e}")
            return {"type": "error", "message": f"Error processing setup: {str(e)}"}

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
                        # logger.info(f"Received: {message}")

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



