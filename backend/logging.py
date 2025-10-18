"""
Centralized Logging Configuration using Loguru

This module configures loguru for the entire application with:
- Colored console output
- File rotation
- Different log levels per environment
- Structured logging format
- Exception tracking
"""
import sys
from pathlib import Path
from loguru import logger
from core.config import settings

# Remove default handler
logger.remove()

# Console handler with colors
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# File handler with rotation
if settings.LOG_FILE:
    log_path = Path(settings.LOG_FILE)
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="10 MB",  # Rotate when file reaches 10MB
        retention="1 week",  # Keep logs for 1 week
        compression="zip",  # Compress rotated logs
        backtrace=True,
        diagnose=True,
    )

# Add custom log levels if needed
# logger.level("CUSTOM", no=38, color="<yellow>", icon="🔧")

def get_logger(name: str = None):
    """
    Get a logger instance with optional name binding

    Args:
        name: Optional name to bind to the logger (e.g., module name)

    Returns:
        Configured logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger


# Export logger for convenience
__all__ = ["logger", "get_logger"]

