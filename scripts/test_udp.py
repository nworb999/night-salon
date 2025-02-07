import socket
import json
import time

def test_udp_send():
    # Create a UDP socket for sending
    send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Unity server details (Windows)
    unity_ip = "127.0.0.1"  # Try with localhost first
    unity_port = 8053
    
    # Test message
    test_message = {
        "type": "agent_update",
        "agent_id": "test_agent",
        "data": json.dumps({
            "objective": "test",
            "thought": "testing connection",
            "emotion": "neutral",
            "current_action": "testing",
            "current_animation": "idle"
        })
    }
    
    try:
        # Convert message to JSON and encode
        message_bytes = json.dumps(test_message).encode('utf-8')
        print(f"Sending message: {json.dumps(test_message, indent=2)}")
        print(f"Message size: {len(message_bytes)} bytes")
        
        # Send message
        send_socket.sendto(message_bytes, (unity_ip, unity_port))
        print(f"Message sent to {unity_ip}:{unity_port}")
        
        # Wait a bit and send another message
        time.sleep(2)
        send_socket.sendto(message_bytes, (unity_ip, unity_port))
        print("Second message sent")
        
    except Exception as e:
        print(f"Error sending message: {e}")
    finally:
        send_socket.close()

if __name__ == "__main__":
    print("Starting UDP test...")
    test_udp_send()
    print("Test complete. Check Unity console for received messages.")