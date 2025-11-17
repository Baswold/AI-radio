"""
Centralized logging configuration for AI Radio backend.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(app):
    """
    Configure comprehensive logging for the application.

    Args:
        app: Flask application instance
    """
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_file = app.config.get('LOG_FILE')
    log_max_bytes = app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024)
    log_backup_count = app.config.get('LOG_BACKUP_COUNT', 5)

    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(detailed_formatter if app.debug else simple_formatter)
    root_logger.addHandler(console_handler)

    # File handler (rotating)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=log_max_bytes,
            backupCount=log_backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)

    # Error file handler (separate file for errors)
    if log_file:
        error_log_file = str(Path(log_file).parent / 'error.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=log_max_bytes,
            backupCount=log_backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)

    # Set Flask app logger
    app.logger.setLevel(log_level)

    # Reduce noise from third-party libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    app.logger.info('Logging system initialized')
    app.logger.info(f'Log level: {logging.getLevelName(log_level)}')
    app.logger.info(f'Log file: {log_file}')


class SecurityLogger:
    """Logger for security-related events"""

    def __init__(self, app=None):
        self.logger = logging.getLogger('security')
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize security logger with app context"""
        self.logger.setLevel(logging.INFO)

        # Create security log file
        log_dir = Path(app.config.get('LOG_FILE')).parent
        security_log = log_dir / 'security.log'

        handler = logging.handlers.RotatingFileHandler(
            security_log,
            maxBytes=app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
        )

        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_login_attempt(self, username, success, ip_address):
        """Log login attempt"""
        status = 'SUCCESS' if success else 'FAILED'
        self.logger.info(f'Login {status}: user={username}, ip={ip_address}')

    def log_failed_authorization(self, user, resource, ip_address):
        """Log failed authorization attempt"""
        self.logger.warning(
            f'Authorization FAILED: user={user}, resource={resource}, ip={ip_address}'
        )

    def log_suspicious_activity(self, description, user=None, ip_address=None):
        """Log suspicious activity"""
        self.logger.warning(
            f'SUSPICIOUS: {description}, user={user}, ip={ip_address}'
        )

    def log_upload(self, user, filename, file_size):
        """Log file upload"""
        self.logger.info(
            f'Upload: user={user}, file={filename}, size={file_size} bytes'
        )

    def log_admin_action(self, admin_user, action, target=None):
        """Log admin action"""
        self.logger.info(
            f'Admin action: admin={admin_user}, action={action}, target={target}'
        )


class PerformanceLogger:
    """Logger for performance monitoring"""

    def __init__(self, app=None):
        self.logger = logging.getLogger('performance')
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize performance logger"""
        self.logger.setLevel(logging.INFO)

        log_dir = Path(app.config.get('LOG_FILE')).parent
        perf_log = log_dir / 'performance.log'

        handler = logging.handlers.RotatingFileHandler(
            perf_log,
            maxBytes=app.config.get('LOG_MAX_BYTES', 10 * 1024 * 1024),
            backupCount=app.config.get('LOG_BACKUP_COUNT', 5)
        )

        formatter = logging.Formatter(
            '[%(asctime)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def log_request(self, method, path, duration, status_code):
        """Log HTTP request performance"""
        self.logger.info(
            f'{method} {path} - {status_code} - {duration:.3f}s'
        )

    def log_media_processing(self, filename, operation, duration):
        """Log media processing performance"""
        self.logger.info(
            f'Media processing: {operation} on {filename} took {duration:.2f}s'
        )

    def log_database_query(self, query, duration):
        """Log slow database queries"""
        if duration > 1.0:  # Log queries taking more than 1 second
            self.logger.warning(
                f'Slow query ({duration:.3f}s): {query[:200]}'
            )


def get_logger(name):
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
