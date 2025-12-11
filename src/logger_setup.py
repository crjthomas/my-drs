"""
Logging setup for LBW Decision System
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(
    log_path: Optional[str] = None,
    log_level: str = "INFO",
    rotation: str = "500 MB",
    retention: str = "10 days"
) -> None:
    """
    Setup logging configuration
    
    Args:
        log_path: Path to log directory
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        rotation: When to rotate log files
        retention: How long to keep log files
    """
    # Remove default handler
    logger.remove()
    
    # Add console handler with formatting
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # Add file handler if log path provided
    if log_path:
        log_dir = Path(log_path)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # General log file
        logger.add(
            log_dir / "lbw_system_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level=log_level,
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
        
        # Error log file
        logger.add(
            log_dir / "errors_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation=rotation,
            retention=retention,
            compression="zip"
        )
        
        # Decision log file (for LBW decisions)
        logger.add(
            log_dir / "decisions_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}",
            level="INFO",
            rotation=rotation,
            retention=retention,
            filter=lambda record: "DECISION" in record["extra"]
        )
    
    logger.info(f"Logger initialized with level {log_level}")


def log_decision(decision_data: dict) -> None:
    """
    Log an LBW decision with structured data
    
    Args:
        decision_data: Dictionary containing decision information
    """
    logger.bind(DECISION=True).info(f"LBW Decision: {decision_data}")
