import asyncio
import signal
from datetime import datetime

from night_salon.server import Server
from utils.utils import handle_shutdown, GracefulExit
from utils.logger import (
    setup_logging,
    log_server_start,
    log_shutdown_signal,
    log_fatal_error,
    log_shutdown_complete,
    log_shutdown_error,
)
from utils.config import load_config


async def main():
    # Load configuration
    config = load_config()
    
    # Setup logging
    logger = setup_logging(config["debug"])
    
    # Setup shutdown handler
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    game_server = Server()
    start_time = datetime.now()

    try:
        log_server_start(logger, config, start_time)
        await game_server.start(config["host"], config["port"])
        
    except GracefulExit:
        log_shutdown_signal(logger)
        
    except Exception as e:
        log_fatal_error(logger, e)
        
    finally:
        try:
            await game_server.stop()
            log_shutdown_complete(logger, start_time)
            
        except Exception as e:
            log_shutdown_error(logger, e)
            raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  