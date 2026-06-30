import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "tally_sync_agent", log_level: str = "INFO") -> logging.Logger:
    """
    Sets up a logger with a Console handler and a Rotating File handler.
    Path is resolved safely using abspath(__file__).
    """
    # Attach handlers to the ROOT logger to avoid multiple open file handles
    # which break file rotation on Windows.
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        level = getattr(logging, log_level.upper(), logging.INFO)
        root_logger.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        
        # 1. Console Stream Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 2. Rotating File Handler
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "sync_agent.log"),
            maxBytes=5 * 1024 * 1024,  # 5 MB split cap
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    return logger
