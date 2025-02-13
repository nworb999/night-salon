import signal
import sys
from config.logger import logger
from night_salon.server.server import Server

def signal_handler(sig, frame):
    logger.info("Ctrl+C detected. Shutting down...")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    server = Server()
    try:
        server.start()
    except Exception as e:
        logger.error(f"Server failed: {e}")
    finally:
        logger.info("Server stopped.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)