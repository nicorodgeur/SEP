"""
utils/logger.py — Configuration de loguru
"""

import sys

from loguru import logger

from config import LOG_DIR


def setup_logger():
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        colorize=True,
    )
    logger.add(
        LOG_DIR / "jobhunt_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="14 days",
        level="DEBUG",
        encoding="utf-8",
        enqueue=True,
    )
    return logger
