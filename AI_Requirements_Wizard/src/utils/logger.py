import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config.settings import settings


def get_logger(name: str) -> logging.Logger:
    """Create and configure a logger for the application.

    This logger writes to both console and a rotating logfile inside the configured
    logs directory. Do not log secrets or large payloads.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    # File handler with rotation
    fh = RotatingFileHandler(str(log_file), maxBytes=5 * 1024 * 1024, backupCount=5)
    fh.setLevel(logging.INFO)
    fh_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(fh_formatter)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(ch_formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    # Prevent propagation to the root logger twice
    logger.propagate = False
    return logger
