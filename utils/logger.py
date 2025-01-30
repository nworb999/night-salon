import logging
from datetime import datetime

def setup_logging(debug=False):
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def create_separator(char='=', length=50):
    return f"\n{char * length}\n"

def log_server_start(logger, config, start_time):
    logger.info(create_separator())
    logger.info("Game Server Starting")
    logger.info(f"Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Host: {config['host']}")
    logger.info(f"Port: {config['port']}")
    logger.info(f"Debug Mode: {config['debug']}")
    print(create_separator())

def log_shutdown_signal(logger):
    logger.info(create_separator())
    logger.info("Received shutdown signal")
    print("Initiating graceful shutdown...")

def log_fatal_error(logger, error):
    logger.error(create_separator())
    logger.error(f"Fatal error occurred: {str(error)}")
    logger.exception("Stack trace:")

def log_shutdown_complete(logger, start_time):
    end_time = datetime.now()
    uptime = end_time - start_time
    
    logger.info(create_separator())
    logger.info("Server Shutdown Complete")
    logger.info(f"Server uptime: {uptime}")
    logger.info(f"Shutdown time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(create_separator())

def log_shutdown_error(logger, error):
    logger.error(f"Error during shutdown: {str(error)}")
