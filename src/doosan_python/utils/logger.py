"""Standard logging configuration for the doosan_python package."""

import logging
import sys
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Custom formatter adding basic ANSI colors for terminal output."""

    GREY = "\x1b[38;20m"
    GREEN = "\x1b[32;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: GREY + "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s" + RESET,
        logging.INFO: GREEN + "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s" + RESET,
        logging.WARNING: YELLOW + "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s" + RESET,
        logging.ERROR: RED + "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s" + RESET,
        logging.CRITICAL: BOLD_RED + "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s" + RESET,
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logger(
    name: str = "doosan_python",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Configure and return a standard logger.

    Args:
        name: Logger hierarchy name.
        level: Minimum log level (e.g. logging.INFO, logging.DEBUG).
        log_file: Optional path to output log file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Retrieve an existing child logger under doosan_python namespace."""
    if not name.startswith("doosan_python"):
        name = f"doosan_python.{name}"
    return logging.getLogger(name)
