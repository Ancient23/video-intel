"""
Logging configuration for Video Intelligence Platform.
Provides structured logging with JSON output for better observability.
"""

import logging
import sys
import structlog


def configure_logging(log_level=logging.INFO):
    """
    Configure structlog for JSON logging with Video Intelligence specific processors.
    
    Args:
        log_level: The logging level to use (default: INFO)
    """
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            structlog.processors.dict_tracebacks,
            structlog.dev.ConsoleRenderer()
            if sys.stdout.isatty()
            else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


# Configure logging on module import
configure_logging()

# Shared logger instance
logger = structlog.get_logger()


def get_logger(name: str = None) -> structlog.BoundLogger:
    """
    Get a logger instance with optional name binding.
    
    Args:
        name: Optional logger name to bind
        
    Returns:
        Configured structlog logger
    """
    log = structlog.get_logger()
    if name:
        log = log.bind(logger_name=name)
    return log