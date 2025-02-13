import os

from dotenv import load_dotenv


class Config:
    """Configuration management for the application"""

    def __init__(self):
        load_dotenv()

        self.bind_host = "0.0.0.0"  # Always bind to all interfaces
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8001"))

        # Unity HTTP endpoint
        self.unity_bind_host = "0.0.0.0"  # For receiving connections
        self.unity_host = os.getenv("UNITY_HOST", "127.0.0.1")
        self.unity_port = int(os.getenv("UNITY_PORT", 5000)) #This is the port for TCP

        self.unity_url = f"http://{self.unity_host}:{self.unity_port}" #was unity_http_port, but that variable does not exist

        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
