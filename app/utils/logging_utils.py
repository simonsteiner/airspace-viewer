"""Centralized logging utilities for the airspace-viewer application.

This module provides a simple, consistent way to control debug logging across
all modules without verbose parameters or complex configurations.
"""

import logging
import os
from typing import Optional

# Module-level logger instance

_logger: Optional[logging.Logger] = None
_debug_enabled: bool = False


def get_logger(module_name: str) -> logging.Logger:
    """Get a debug logger for a specific module.

    Args:
        module_name (str): The name of the module requesting the logger.

    Returns:
        logging.Logger: A configured logger instance.
    """
    if _logger is None:
        _setup_logging()

    return logging.getLogger(f"airspace_viewer.{module_name}")


def _setup_logging() -> None:
    """Set up the logging configuration based on environment and Flask config."""
    global _logger, _debug_enabled

    print("Setting up logging...")
    # Try to get debug setting from Flask app context first
    try:
        from flask import current_app

        _debug_enabled = current_app.config.get("DEBUG_LOGGING", False)
        print(f"Debug logging enabled: {_debug_enabled}")
    except (ImportError, RuntimeError):
        # Fall back to environment variable if not in Flask context
        print("Falling back to environment variable for debug logging")
        _debug_enabled = os.environ.get("AIRSPACE_DEBUG", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    # Configure the main logger
    logger_name = "airspace_viewer"
    _logger = logging.getLogger(logger_name)

    print(f"Configuring logger '{logger_name}' with debug enabled: {_debug_enabled}")
    print(f"Current logger level: {_logger.level}")

    # Only add handler if it doesn't already exist
    if not _logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] [%(name)s] %(message)s")
        handler.setFormatter(formatter)
        _logger.addHandler(handler)

    # Prevent propagation to avoid duplicate messages
    _logger.propagate = False
    info_log(
        "logging_utils",
        f"Logging setup complete. Debug mode: {_debug_enabled}",
    )
    info_log(
        "logging_utils",
        f"Logger level: {_logger.level}",
    )


def set_debug_enabled(enabled: bool) -> None:
    """Manually enable or disable debug logging.

    Args:
        enabled (bool): Whether to enable debug logging.
    """
    global _debug_enabled
    _debug_enabled = enabled

    if _logger is not None:
        _logger.setLevel(logging.DEBUG if enabled else logging.WARNING)
        # Update all child loggers
        for name in logging.getLogger().manager.loggerDict:
            if name.startswith("airspace_viewer."):
                child_logger = logging.getLogger(name)
                child_logger.setLevel(logging.DEBUG if enabled else logging.WARNING)


def debug_log(module_name: str, message: str) -> None:
    """Log a debug message for a specific module.

    Args:
        module_name (str): The name of the module logging the message.
        message (str): The debug message to log.
    """
    logger = get_logger(module_name)
    logger.debug(message)


def info_log(module_name: str, message: str) -> None:
    """Log an info message for a specific module.

    Args:
        module_name (str): The name of the module logging the message.
        message (str): The info message to log.
    """
    logger = get_logger(module_name)
    logger.info(message)


def error_log(module_name: str, message: str) -> None:
    """Log an error message for a specific module.

    Args:
        module_name (str): The name of the module logging the message.
        message (str): The error message to log.
    """
    logger = get_logger(module_name)
    logger.error(message)


def warning_log(module_name: str, message: str) -> None:
    """Log a warning message for a specific module.

    Args:
        module_name (str): The name of the module logging the message.
        message (str): The warning message to log.
    """
    logger = get_logger(module_name)
    logger.warning(message)
