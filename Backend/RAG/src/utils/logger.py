"""
Maritime-RAG Logging Module
============================
Configures structured logging with loguru.
Provides a pre-configured logger instance used across the project.
"""

import sys
from pathlib import Path

from loguru import logger

from src.utils.config import get_settings


def setup_logger() -> "logger":
    """
    Configure and return the application-wide loguru logger.

    Outputs:
        - Console: colourised, human-readable.
        - File   : JSON-structured, rotated at 10 MB, retained 7 days.

    Returns:
        Configured loguru logger instance.
    """
    settings = get_settings()

    # Remove default handler to avoid duplicate logs
    logger.remove()

    # ── Console handler ────────────────────────────────────────────────────
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # ── File handler ───────────────────────────────────────────────────────
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        str(log_path),
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        serialize=False,
    )

    logger.info("Logger initialised – level={}", settings.log_level)
    return logger


# ---------------------------------------------------------------------------
# Module-level logger ready for import:  `from src.utils.logger import log`
# ---------------------------------------------------------------------------
log = setup_logger()
