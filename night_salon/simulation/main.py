import asyncio
import threading
from pathlib import Path

import uvicorn
from api.routes import app, office
from office_simulation.utils.config import Config
from office_simulation.utils.logger import setup_logger

# Setup logging with a log file
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
logger = setup_logger(__name__, log_file=log_dir / "simulation.log")

# Load configuration
config = Config()


async def run_simulation():
    """Run the office simulation loop"""
    logger.info("Starting simulation loop")
    while True:
        try:
            # Update simulation state
            logger.info("Simulation tick")
            # Example: Update environment, trigger random events, etc.
            await office.update_environment()

            # Wait before next tick
            await asyncio.sleep(5)  # Adjust tick rate as needed

        except Exception as e:
            logger.error(f"Error in simulation loop: {str(e)}")
            await asyncio.sleep(5)  # Wait before retrying


def start_server():
    """Start the FastAPI server with logging"""
    logger.info("=== Starting Office Simulation Server ===")
    logger.info(f"Host: {config.simulation_host}")
    logger.info(f"Port: {config.simulation_port}")

    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"][
        "fmt"
    ] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    try:
        uvicorn.run(
            app,
            host=config.simulation_host,
            port=config.simulation_port,
            log_config=log_config,
        )
    except Exception as e:
        logger.error(f"Server failed to start: {str(e)}")
        raise


async def main():
    """Start both the simulation and API server"""
    # Create tasks for both the simulation and API server
    simulation_task = asyncio.create_task(run_simulation())

    # Run the server in a separate thread since uvicorn.run is blocking
    server_thread = threading.Thread(target=start_server)
    server_thread.start()

    try:
        # Wait for the simulation task
        await simulation_task
    except asyncio.CancelledError:
        logger.info("Simulation stopped")
    finally:
        logger.info("Shutting down")


if __name__ == "__main__":
    asyncio.run(main())
