"""
Structured Logging Framework - Story 5.1

Centralized logging with structured fields, correlation IDs, and log levels.
Part of Epic 5: Common Components.
"""
import logging
import json
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
import sys
from contextlib import contextmanager


class LogLevel(Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    Structured logger with JSON output and correlation tracking.
    
    Features:
    - JSON-formatted logs
    - Correlation IDs for request tracking
    - Contextual fields (agent_id, pr_number, etc.)
    - Performance metrics
    - Log aggregation support
    """
    
    def __init__(
        self,
        name: str,
        level: str = "INFO",
        output_format: str = "json",
        include_timestamp: bool = True,
        include_caller: bool = True
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (typically module name)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            output_format: Format (json or text)
            include_timestamp: Include timestamp in logs
            include_caller: Include caller info (file, line)
        """
        self.name = name
        self.level = getattr(logging, level.upper())
        self.output_format = output_format
        self.include_timestamp = include_timestamp
        self.include_caller = include_caller
        
        # Context storage
        self.context: Dict[str, Any] = {}
        self.correlation_id: Optional[str] = None
        
        # Performance tracking
        self.operation_starts: Dict[str, float] = {}
        
        # Setup Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Add our handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(self._get_formatter())
        self.logger.addHandler(handler)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """Log error message."""
        if exc_info:
            kwargs["exc_info"] = True
        self._log(LogLevel.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, **kwargs)
    
    def set_correlation_id(self, correlation_id: Optional[str] = None) -> str:
        """
        Set correlation ID for request tracking.
        
        Args:
            correlation_id: Correlation ID (generated if not provided)
            
        Returns:
            Correlation ID
        """
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())
        
        self.correlation_id = correlation_id
        return correlation_id
    
    def set_context(self, **kwargs) -> None:
        """Set contextual fields for all subsequent logs."""
        self.context.update(kwargs)
    
    def clear_context(self) -> None:
        """Clear all contextual fields."""
        self.context.clear()
        self.correlation_id = None
    
    @contextmanager
    def operation(self, operation_name: str, **metadata):
        """
        Context manager for timing operations.
        
        Usage:
            with logger.operation("process_pr", pr_number=42):
                # do work
                pass
        """
        start_time = time.time()
        self.info(f"Starting operation: {operation_name}", **metadata)
        
        try:
            yield
            duration = time.time() - start_time
            self.info(
                f"Completed operation: {operation_name}",
                duration_ms=int(duration * 1000),
                **metadata
            )
        except Exception as e:
            duration = time.time() - start_time
            self.error(
                f"Failed operation: {operation_name}",
                error=str(e),
                duration_ms=int(duration * 1000),
                exc_info=True,
                **metadata
            )
            raise
    
    def _log(self, level: LogLevel, message: str, **kwargs) -> None:
        """Internal log method."""
        # Build log record
        record = {
            "message": message,
            "level": level.value,
            "logger": self.name
        }
        
        # Add timestamp
        if self.include_timestamp:
            record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Add correlation ID
        if self.correlation_id:
            record["correlation_id"] = self.correlation_id
        
        # Add context
        record.update(self.context)
        
        # Add kwargs
        record.update(kwargs)
        
        # Log via Python logger
        log_func = getattr(self.logger, level.value.lower())
        
        if self.output_format == "json":
            log_func(json.dumps(record))
        else:
            # Text format
            context_str = " ".join(f"{k}={v}" for k, v in record.items() if k not in ["message", "level", "logger"])
            log_func(f"{message} {context_str}")
    
    def _get_formatter(self) -> logging.Formatter:
        """Get log formatter."""
        if self.output_format == "json":
            return logging.Formatter("%(message)s")
        else:
            return logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )


class LoggerFactory:
    """
    Factory for creating loggers with consistent configuration.
    """
    
    _loggers: Dict[str, StructuredLogger] = {}
    _default_level: str = "INFO"
    _default_format: str = "json"
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        level: Optional[str] = None,
        output_format: Optional[str] = None
    ) -> StructuredLogger:
        """
        Get or create a logger.
        
        Args:
            name: Logger name
            level: Log level (default: INFO)
            output_format: Format (default: json)
            
        Returns:
            StructuredLogger instance
        """
        if name not in cls._loggers:
            cls._loggers[name] = StructuredLogger(
                name=name,
                level=level or cls._default_level,
                output_format=output_format or cls._default_format
            )
        
        return cls._loggers[name]
    
    @classmethod
    def configure(cls, level: str = "INFO", output_format: str = "json") -> None:
        """
        Configure default settings for all loggers.
        
        Args:
            level: Default log level
            output_format: Default output format
        """
        cls._default_level = level
        cls._default_format = output_format
        
        # Update existing loggers
        for logger in cls._loggers.values():
            logger.level = getattr(logging, level.upper())
            logger.output_format = output_format


# Convenience functions

def get_logger(name: str) -> StructuredLogger:
    """Get a logger instance."""
    return LoggerFactory.get_logger(name)


def configure_logging(level: str = "INFO", output_format: str = "json") -> None:
    """Configure logging globally."""
    LoggerFactory.configure(level=level, output_format=output_format)
