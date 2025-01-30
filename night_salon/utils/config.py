import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv


class Config:
    """Configuration management for the application"""

    def __init__(self, env_file: Optional[Path] = None):
        load_dotenv(env_file)

        self.simulation_host = os.getenv("SIMULATION_HOST", "0.0.0.0")
        self.simulation_port = int(os.getenv("SIMULATION_PORT", "8000"))
        self.coordinator_host = os.getenv("COORDINATOR_HOST", "0.0.0.0")
        self.coordinator_port = int(os.getenv("COORDINATOR_PORT", "8001"))

        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE")
