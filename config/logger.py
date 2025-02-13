import logging
from pathlib import Path
from typing import Optional
import sys


def setup_logger(
    level: int = logging.INFO, log_file: Optional[Path] = None
) -> logging.Logger:
    """Configure and return a logger instance with consistent formatting"""
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

    # Setup logging


logger = setup_logger()
  
