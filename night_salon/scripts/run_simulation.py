import argparse
import sys
from pathlib import Path

import uvicorn

from night_salon.simulation.api.routes import app
from night_salon.utils.config import Config
from night_salon.utils.logger import setup_logger


def parse_args():
    parser = argparse.ArgumentParser(description="Run the simulation server")
    parser.add_argument("--config", type=Path, help="Path to config file")
    parser.add_argument("--log-file", type=Path, help="Path to log file")
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
    logger = setup_logger("simulation", log_file=args.log_file or config.log_file)

    logger.info(
        f"Starting simulation server on {config.simulation_host}:{config.simulation_port}"
    )

    try:
        uvicorn.run(
            app,
            host=config.simulation_host,
            port=config.simulation_port,
            log_level=config.log_level.lower(),
        )
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
