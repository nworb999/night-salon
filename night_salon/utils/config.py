import os

from dotenv import load_dotenv


class Config:
    """Configuration management for the application"""

    def __init__(self):
        load_dotenv()
        
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8001"))

