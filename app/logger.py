"""
Initialize application logging using loguru.
"""
import os
import sys
from loguru import logger
from app.config import settings

def init_logger():
    """
    Configure loguru logger: stdout and file (if enabled).
    """
    # Remove default handler
    logger.remove()

    # Console sink
    logger.add(sys.stdout, level="DEBUG" if settings.debug else "INFO", backtrace=settings.debug, diagnose=settings.debug)

    # File sink
    if settings.log_dir:
        os.makedirs(settings.log_dir, exist_ok=True)
        log_file = os.path.join(settings.log_dir, "suno_api.log")
        rotation = "10 MB" if settings.rotate_logs else None
        logger.add(log_file, rotation=rotation, retention="10 days", level="DEBUG")