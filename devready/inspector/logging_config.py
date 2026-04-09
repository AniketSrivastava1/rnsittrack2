import logging
import sys
from typing import Optional

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """Configures centralized logging for the inspector."""
    
    # Create logger
    logger = logging.getLogger("devready.inspector")
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    logger.info(f"Logging initialized at level {logging.getLevelName(level)}")
    return logger
