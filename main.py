import signal
import sys
import uvicorn
import os
from dotenv import load_dotenv
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WS Server")

load_dotenv()

def signal_handler(sig, frame):
    logger.info("Shutting down...")
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    uvicorn.run(
        "night_salon.server.server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "3000")),
        log_config=None,
        reload=os.getenv("ENV") == "development"
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)