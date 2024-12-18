# src/utils/logging.py
from loguru import logger
import sys
from pathlib import Path
from typing import  Union

class AppLogger:
    """Centralized logging configuration for the application"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.log_path = Path("../logs")
        self.log_path.mkdir(exist_ok=True)
        
        # Remove default logger
        logger.remove()
        
        # Add console logger
        logger.add(
            sys.stdout,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
            level="INFO"
        )
        
        # Add file logger
        logger.add(
            self.log_path / "app.log",
            rotation="500 MB",
            retention="10 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="INFO"
        )
        
        # Add error log
        logger.add(
            self.log_path / "error.log",
            rotation="100 MB",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR"
        )

    @staticmethod
    def get_logger(name: Union[str, None] = None):
        """Get a logger instance for a specific module"""
        return logger.bind(module=name if name else "app")

app_logger = AppLogger()

def get_logger(name: Union[str, None] = None):
    return app_logger.get_logger(name)
