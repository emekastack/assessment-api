import logging
import sys
import os

# This is a simple, self-contained logging setup.
# It reads the LOG_LEVEL directly from the environment, with a sensible default.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# A mapping from string level to logging level constant
level_map = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Get the root logger
_logger = logging.getLogger()
_logger.setLevel(level_map.get(LOG_LEVEL, logging.INFO))

# Create a handler to print logs to the console (stderr)
_handler = logging.StreamHandler(sys.stderr)

# Create a formatter
_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_handler.setFormatter(_formatter)

# Add the handler to the logger if it doesn't have one already
if not _logger.handlers:
    _logger.addHandler(_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance for a given module name.
    """
    return logging.getLogger(name)
