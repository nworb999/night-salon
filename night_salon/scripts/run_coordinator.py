import sys
from pathlib import Path
import uvicorn
import argparse

from night_salon.utils.logger import setup_logger
from night_salon.utils.config import Config
from night_salon.coordinator.main import create_app

def parse_args():
    parser = argparse.ArgumentParser(description='Run the agent coordinator server')
    parser.add_argument('--config', type=Path, help='Path to config file')
    parser.add_argument('--log-file', type=Path, help='Path to log file')
    parser.add_argument('--simulation-url', help='URL of the simulation server')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup configuration
    try:
        config = Config(args.config)
    except Exception as e:
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Setup logging
    logger = setup_logger(
        "agent_coordinator",
        log_file=args.log_file or config.log_file
    )
    
    logger.info(f"Starting coordinator server on {config.coordinator_host}:{config.coordinator_port}")
    
    try:
        # Create FastAPI app with simulation server URL
        app = create_app(
            simulation_url=args.simulation_url or f"http://{config.simulation_host}:{config.simulation_port}"
        )
        
        uvicorn.run(
            app,
            host=config.coordinator_host,
            port=config.coordinator_port,
            log_level=config.log_level.lower()
        )
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()