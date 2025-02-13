import socket
import time
import json

def receive_message(socket):
    # Read message length (4 bytes, little endian as BitConverter uses little endian by default)
    length_bytes = socket.recv(4)
    message_length = int.from_bytes(length_bytes, byteorder='little')
    
    # Read exact message length
    remaining = message_length
    chunks = []
    while remaining > 0:
        chunk = socket.recv(remaining)
        if not chunk:
            raise ConnectionError("Connection closed while receiving message")
        chunks.append(chunk)
        remaining -= len(chunk)
    
    raw_message = b''.join(chunks)
    # Use UTF-8 encoding instead of ASCII
    message = raw_message.decode('utf-8')
    return message

def start_python_server():
    # Connect to Unity server
    server_address = ('127.0.0.1', 5000)
    
    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print("Connecting to Unity server...")
            client_socket.connect(server_address)
            print("Connected to Unity server!")
            break
        except ConnectionRefusedError:
            print("Connection failed. Retrying in 2 seconds...")
            time.sleep(2)
        except KeyboardInterrupt:
            print("\nConnection attempts cancelled by user.")
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
                print(f"Sent to Unity: {message}")

                # Receive update from Unity
                message = receive_message(client_socket)
                if message:
                    print(f"Received complete message: {message}")

                time.sleep(1)  # Wait for 1 second before next request

            except (ConnectionAbortedError, ConnectionResetError) as e:
                print(f"\nConnection lost: {e}")
                client_socket.close()
                break

    except KeyboardInterrupt:
        print("\nClosing connection...")
        client_socket.close()

if __name__ == "__main__":
    start_python_server()