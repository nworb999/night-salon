import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    return {
        "host": os.getenv("SERVER_HOST", "localhost"),
        "port": int(os.getenv("SERVER_PORT", "8765")),
        "debug": os.getenv("DEBUG", "False").lower() == "true",
    }