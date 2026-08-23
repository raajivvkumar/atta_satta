"""Logging configuration for Atta Satta."""

from __future__ import annotations

import logging


LOGGER_NAME = "atta_satta"


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return the application logger.

    Configuration is intentionally conservative so importing the package never
    changes the host application's global logging configuration.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
        )
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = logging.getLogger(LOGGER_NAME)
