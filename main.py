from config.logger import logger
from night_salon.server.server import Server
import sys

def main():
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
    except KeyboardInterrupt:
        logger.info("Main script interrupted.")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)