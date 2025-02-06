import os
import argparse
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv




class Config:
    """Configuration management for the application"""

    def __init__(self):
        load_dotenv()

        self.coordinator_host = os.getenv("COORDINATOR_HOST", "0.0.0.0")
        self.coordinator_port = int(os.getenv("COORDINATOR_PORT", "8001"))

        # Unity HTTP endpoint
        self.unity_host = os.getenv('UNITY_HOST', '127.0.0.1')
        self.unity_http_port = int(os.getenv('UNITY_HTTP_PORT', '8080'))  
        self.unity_url = f"http://{self.unity_host}:{self.unity_http_port}"

        # Unity TCP/UDP ports for direct socket communication
        self.unity_tcp_port = int(os.getenv('UNITY_TCP_PORT', 8052))
        self.unity_udp_port = int(os.getenv('UNITY_UDP_PORT', 8053))

        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
