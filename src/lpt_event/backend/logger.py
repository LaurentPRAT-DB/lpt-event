import logging
import sys
from typing import Optional
from .._metadata import app_name


class CustomFormatter(logging.Formatter):
    """Custom log formatter with colored output and pipe-separated format.

    Formats log records with a structured, pipe-separated format that includes:
    - Timestamp with milliseconds
    - Application name
    - Log level (colored if terminal supports it)
    - Abbreviated module.function location (max 20 chars)
    - Log message
    - Exception traceback (if present)

    The formatter intelligently abbreviates long module paths and function names
    to keep the location field within 20 characters while maintaining readability.

    Format:
        YYYY-MM-DD HH:MM:SS.mmm | app_name | LEVEL | location | message

    Attributes:
        use_colors (bool): Whether to apply ANSI color codes to log levels.
            Colors are only applied if stderr is a TTY.
        COLORS (dict): ANSI color codes for each log level.

    Example:
        >>> formatter = CustomFormatter(use_colors=True)
        >>> handler.setFormatter(formatter)
        >>> logger.info("Server started")
        2024-01-09 10:30:45.123 | lpt-event    | INFO     | app.lifespan         | Server started
    """

    # Color codes for different log levels
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def __init__(self, use_colors: bool = True):
        """Initialize the custom formatter.

        Args:
            use_colors (bool): Whether to use colored output. Defaults to True.
                Colors are only applied if stderr is a TTY (terminal).
        """
        super().__init__()
        self.use_colors = use_colors

    def _abbreviate_location(
        self, module: str, func_name: str, max_length: int = 20
    ) -> str:
        """
        Abbreviate module and function name to fit within max_length.

        Args:
            module: Module name (may contain dots)
            func_name: Function name
            max_length: Maximum length of the combined string

        Returns:
            Abbreviated location string
        """
        # Handle case when function is <module> (module-level code)
        if func_name == "<module>":
            location = module if module else "<module>"
        # Handle case when module is not provided
        elif not module or module == "__main__":
            location = func_name
        else:
            location = f"{module}.{func_name}"

        # If it fits, return as-is
        if len(location) <= max_length:
            return location

        # Try abbreviating module parts to first letter
        if module and module != "__main__" and func_name != "<module>":
            parts = module.split(".")
            abbreviated_parts = [p[0] for p in parts]
            abbreviated_module = ".".join(abbreviated_parts)
            location = f"{abbreviated_module}.{func_name}"

            # If still too long, truncate function name
            if len(location) > max_length:
                available_for_func = (
                    max_length - len(abbreviated_module) - 1
                )  # -1 for the dot
                if available_for_func > 0:
                    location = f"{abbreviated_module}.{func_name[:available_for_func]}"
                else:
                    # Extreme case: just use abbreviated module
                    location = abbreviated_module[:max_length]
        else:
            # No module, just truncate function name (or module name if func is <module>)
            location = location[:max_length]

        return location

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record into a pipe-separated string with colors.

        Transforms a LogRecord into a human-readable, structured log line with:
        - Timestamp with millisecond precision
        - Application name (padded to 12 chars)
        - Colored log level (padded to 8 chars)
        - Abbreviated module.function location (max 20 chars)
        - Log message
        - Exception traceback (if exception info is present)

        Args:
            record (logging.LogRecord): The log record to format.

        Returns:
            str: Formatted log line with pipe separators and optional colors.

        Example:
            >>> record = logging.LogRecord(...)
            >>> formatted = formatter.format(record)
            >>> print(formatted)
            2024-01-09 10:30:45.123 | lpt-event    | INFO     | runtime.validate_db  | Database validated
        """
        # Get the time with milliseconds
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        # Add milliseconds
        timestamp = f"{timestamp}.{int(record.msecs):03d}"

        # Get the module name
        module = record.module

        # Get function/class name
        func_name = record.funcName

        # Combine and abbreviate module and function name
        location = self._abbreviate_location(module, func_name, max_length=20)

        # Get log level
        level = record.levelname

        # Apply colors if enabled
        if self.use_colors and sys.stderr.isatty():
            level_color = self.COLORS.get(level, self.COLORS["RESET"])
            reset_color = self.COLORS["RESET"]
            colored_level = f"{level_color}{level:8s}{reset_color}"
        else:
            colored_level = f"{level:8s}"

        # Format the message
        message = record.getMessage()

        # Create the pipe-separated format
        log_line = (
            f"{timestamp} | {app_name:12s} | {colored_level} | "
            f"{location:20s} | {message}"
        )

        # Add exception info if present
        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)

        return log_line


def setup_logger(
    name: Optional[str] = None,
    level: int = logging.INFO,
    use_colors: bool = True,
) -> logging.Logger:
    """
    Set up and configure a logger with custom formatting.

    Args:
        name: Logger name. If None, returns the root logger.
        level: Logging level (default: INFO).
        use_colors: Whether to use colored output (default: True).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    # Set custom formatter
    formatter = CustomFormatter(use_colors=use_colors)
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    return logger


# Create the default logger instance for the application
logger = setup_logger(app_name, level=logging.INFO)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name. If None, returns the default app logger.

    Returns:
        Logger instance.
    """
    if name is None:
        return logger
    return setup_logger(name)
