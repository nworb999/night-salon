import sys
import uvicorn
from fastapi import FastAPI

from utils.logger import logger
from utils.config import Config

from night_salon.state import CoordinatorState
from night_salon.api.routes import router, init_routes


def create_app(unity_url: str) -> FastAPI:
    app = FastAPI()
    config = Config()

    state = CoordinatorState(
        unity_url=unity_url,
        unity_host=config.unity_host,
        unity_bind_host=config.unity_bind_host,
        unity_tcp_port=config.unity_tcp_port,
        unity_udp_port=config.unity_udp_port,
    )

    # Initialize routes with state
    init_routes(state)

    # Include router
    app.include_router(router)

    return app


def main():
    try:
        config = Config()

    except Exception as e:
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    logger.info(
        f"Starting coordinator server on {config.coordinator_host}:{config.coordinator_port}"
    )
    logger.info(f"Unity connections:")
    logger.info(f"  - HTTP API: {config.unity_url}")
    logger.info(f"  - TCP Socket: {config.unity_host}:{config.unity_tcp_port}")
    logger.info(f"  - UDP Socket: {config.unity_host}:{config.unity_udp_port}")

    try:
        # Create FastAPI app with simulation server URL
        app = create_app(config.unity_host)

        uvicorn.run(
            app,
            host=config.coordinator_bind_host,
            port=config.coordinator_port,
            log_level=config.log_level.lower(),
        )

    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
