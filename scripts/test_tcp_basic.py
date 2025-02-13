import socket
import time
import json
from config import Config
from config.logger import logger

config = Config()

def receive_message(socket):
    # Read message length (4 bytes, little endian as BitConverter uses little endian by default)
    length_bytes = socket.recv(4)
    if not length_bytes:
        return None  # Indicate disconnection
    message_length = int.from_bytes(length_bytes, byteorder='little')
    
    # Read exact message length
    remaining = message_length
    chunks = []
    while remaining > 0:
        chunk = socket.recv(remaining)
        if not chunk:
            return None  # Indicate disconnection
        chunks.append(chunk)
        remaining -= len(chunk)
    
    raw_message = b''.join(chunks)
    # Use UTF-8 encoding instead of ASCII
    message = raw_message.decode('utf-8')
    return message

def start_python_server():
    # Connect to Unity server
    server_address = (config.host, config.port)
    
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logger.info("Connecting to Unity server...")
            client_socket.connect(server_address)
            logger.info("Connected to Unity server!")
            break
        except ConnectionRefusedError:
            logger.warning("Connection failed. Retrying in 2 seconds...")
            time.sleep(2)
        except KeyboardInterrupt:
            logger.info("\nConnection attempts cancelled by user.")
            return

    try:
        while True:
            try:
                # Send request to Unity
                message = "Python request"
                message_bytes = message.encode('utf-8')  # Changed to UTF-8
                # Send length prefix first (4 bytes, little endian)
                length_prefix = len(message_bytes).to_bytes(4, byteorder='little')
                client_socket.send(length_prefix)
                # Then send the actual message
                client_socket.send(message_bytes)
                logger.info(f"Sent to Unity: {message}")

                # Receive update from Unity
                response = receive_message(client_socket)
                if response:
                    logger.info(f"Received complete message: {response}")
                else:
                    logger.info("Connection closed by server.")
                    break

                time.sleep(1)  # Wait for 1 second before next request

            except (ConnectionAbortedError, ConnectionResetError) as e:
                logger.error(f"\nConnection lost: {e}")
                client_socket.close()
                break
            except Exception as e:
                logger.error(f"An error occurred: {e}")
                break

    except KeyboardInterrupt:
        logger.info("\nClosing connection...")
        if client_socket:
            client_socket.close()

if __name__ == "__main__":
    start_python_server()