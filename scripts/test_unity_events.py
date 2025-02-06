import socket
import json
from datetime import datetime

def start_udp_listener(port=8001):
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Set socket options to allow address reuse
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to all interfaces instead of just localhost
    server_address = ('0.0.0.0', port)
    print(f"\nAttempting to bind to {server_address}")
    sock.bind(server_address)
    print(f"Successfully bound to {server_address}")
    print(f"WSL IP: 172.29.61.180")
    print("Waiting for messages...\n")
    
    buffer_size = 1024
    
    try:
        while True:
            print("Waiting for next message...")  # Debug line
            # Receive data
            data, addr = sock.recvfrom(buffer_size)
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
            
            print(f"\n[{timestamp}] Received {len(data)} bytes from {addr}")
            print(f"Raw data: {data}")
            
            try:
                # Try to decode as UTF-8
                decoded = data.decode('utf-8')
                print(f"Decoded (UTF-8): {decoded}")
                
                # Try to parse as JSON
                try:
                    json_data = json.loads(decoded)
                    print("\nParsed JSON:")
                    print(json.dumps(json_data, indent=2))
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    
            except UnicodeDecodeError as e:
                print(f"Unicode Decode Error: {e}")
            
            print("\n" + "-"*50)
            
    except KeyboardInterrupt:
        print("\nShutting down listener...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sock.close()
        print("Listener closed")

if __name__ == "__main__":
    try:
        start_udp_listener()
    except Exception as e:
        print(f"Failed to start listener: {e}")