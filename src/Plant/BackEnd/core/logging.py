"""
Structured logging setup
JSON format for parsing + filtering
"""

import logging
import json
from typing import Any
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON logs.
    Useful for log aggregation and parsing.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            str: JSON-formatted log line
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add tenant_id, user_id, endpoint, and duration if present
        if hasattr(record, 'tenant_id'):
            log_data["tenant_id"] = record.tenant_id
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'endpoint'):
            log_data["endpoint"] = record.endpoint
        if hasattr(record, 'duration'):
            log_data["duration"] = record.duration
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (INFO, DEBUG, WARNING, ERROR)
        
    Returns:
        logging.Logger: Configured logger
        
    Example:
        logger = get_logger(__name__)
        logger.info("Something happened", extra={"user_id": 123})
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with JSON formatter
    handler = logging.StreamHandler()
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
