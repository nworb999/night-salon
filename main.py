import signal
import sys
from config.logger import logger
import uvicorn
import os

def signal_handler(sig, frame):
    logger.info("Ctrl+C detected. Shutting down...")
    sys.exit(0)

def main():
    # Remove signal handling (let the process manager handle it)
    uvicorn.run(
        "night_salon.server.server:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        log_level="info",
        reload=os.getenv("ENV") == "development",
        workers=int(os.getenv("WORKERS", "1")) if os.getenv("ENV") == "production" else 1
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)