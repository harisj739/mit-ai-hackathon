"""
Logging configuration for Stressor.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json
from .config import settings


class SecureFormatter(logging.Formatter):
    """Custom formatter that redacts sensitive information."""
    
    SENSITIVE_FIELDS = {
        'api_key', 'secret', 'password', 'token', 'key', 
        'auth', 'credential', 'private'
    }
    
    def format(self, record):
        """Format log record with sensitive data redaction."""
        # Redact sensitive information from log messages
        if hasattr(record, 'msg'): 
            record.msg = self._redact_sensitive_data(str(record.msg))
        
        if hasattr(record, 'args') and isinstance(record.args, dict):
            record.args = self._redact_sensitive_data(record.args)
        
        return super().format(record)
    
    def _redact_sensitive_data(self, data):
        """Redact sensitive information from data."""
        if isinstance(data, str):
            for field in self.SENSITIVE_FIELDS:
                # Simple redaction - replace with asterisks
                data = self._redact_pattern(data, field)
        elif isinstance(data, dict):
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                    data[key] = '***REDACTED***'
                else:
                    data[key] = self._redact_sensitive_data(value)
        
        return data
    
    def _redact_pattern(self, text: str, pattern: str) -> str:
        """Redact pattern matches in text."""
        import re
        # Replace API keys, tokens, etc. with asterisks
        pattern_regex = rf'({pattern}[_=:]\s*)([a-zA-Z0-9\-_]{8,})'
        return re.sub(pattern_regex, r'\1***REDACTED***', text, flags=re.IGNORECASE)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry)


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    enable_json: bool = False
) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        enable_json: Enable JSON formatting for logs
    """
    # Use settings if not provided
    if log_level is None:
        log_level = settings.log_level
    
    if log_file is None:
        log_file = settings.log_directory / f"failproof_llm_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Create log directory if it doesn't exist
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger() # initializing the root logger
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    if enable_json:
        console_formatter = JSONFormatter()
    else:
        console_formatter = SecureFormatter(settings.log_format)
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    if enable_json:
        file_formatter = JSONFormatter()
    else:
        file_formatter = SecureFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Security handler for sensitive operations
    security_logger = logging.getLogger('security')
    security_file = settings.log_directory / 'security.log'
    security_handler = logging.handlers.RotatingFileHandler(
        security_file,
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(SecureFormatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    ))
    security_logger.addHandler(security_handler)
    
    # Suppress verbose logs from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_security_event(event_type: str, details: dict, user_id: Optional[str] = None):
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        details: Event details
        user_id: Associated user ID
    """
    security_logger = logging.getLogger('security')
    
    log_data = {
        'event_type': event_type,
        'details': details,
        'timestamp': datetime.utcnow().isoformat(),
        'user_id': user_id,
        'ip_address': _get_client_ip(),
    }
    
    security_logger.info(f"Security event: {event_type} - {json.dumps(log_data)}")


def _get_client_ip() -> Optional[str]:
    """Get client IP address (placeholder for web context)."""
    # This would be implemented based on the web framework being used
    return None 