import signal
import sys
import uvicorn
import os
from night_salon.utils.config import Config
from utils.logger import logger

def signal_handler(sig, frame):
    logger.info("Shutting down...")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    config = Config()
    
    uvicorn.run(
        "night_salon.server.server:app",
        host=config.host,
        port=config.port,
        log_config=None,
        reload=os.getenv("ENV") == "development"
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)