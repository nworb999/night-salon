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
        "%(asctime)s %(colored_level)s%(message)s"
    )

    # Add color formatter filter
    class ColoredLevelFormatter(logging.Filter):
        colors = {
            logging.DEBUG: "\033[36m",    # Cyan
            logging.INFO: "\033[32m",     # Green
            logging.WARNING: "\033[33m",  # Yellow
            logging.ERROR: "\033[31m",    # Red
            logging.CRITICAL: "\033[35m"  # Magenta
        }

        def filter(self, record):
            record.colored_level = f"{self.colors.get(record.levelno, '')}[{record.levelname}]\033[0m "
            return True

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(ColoredLevelFormatter())
    logger.addHandler(console_handler)

    # Optional file handler (without colors)
    if log_file:
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s\n")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

    # Setup logging


logger = setup_logger()
  
