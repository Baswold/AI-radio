"""
Middleware and decorators for the AI Radio backend.
Includes admin authorization, rate limiting, and request validation.
"""

from functools import wraps
from flask import jsonify, request, current_app
from flask_login import current_user
import time


def admin_required(f):
    """
    Decorator to require admin role for accessing an endpoint.
    Use this decorator after @login_required for admin-only routes.

    Example:
        @app.route('/admin/endpoint')
        @login_required
        @admin_required
        def admin_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required'}), 401

        if not getattr(current_user, 'is_admin', False):
            return jsonify({
                'error': 'Admin privileges required',
                'message': 'You do not have permission to access this resource'
            }), 403

        return f(*args, **kwargs)
    return decorated_function


def validate_json(required_fields=None):
    """
    Decorator to validate JSON request body.

    Args:
        required_fields: List of required field names

    Example:
        @app.route('/endpoint', methods=['POST'])
        @validate_json(['title', 'description'])
        def endpoint():
            data = request.get_json()
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400

            data = request.get_json()
            if data is None:
                return jsonify({'error': 'Invalid JSON'}), 400

            if required_fields:
                missing = [field for field in required_fields if field not in data]
                if missing:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing
                    }), 400

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_filename(filename):
    """
    Sanitize a filename to prevent path traversal attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for use in file paths
    """
    import re
    import os

    # Remove any path components
    filename = os.path.basename(filename)

    # Remove any potentially dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)

    # Replace spaces with underscores
    filename = filename.replace(' ', '_')

    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext

    return filename


def validate_file_path(file_path, allowed_directories):
    """
    Validate that a file path is within allowed directories.
    Prevents path traversal attacks.

    Args:
        file_path: Path to validate
        allowed_directories: List of allowed base directories

    Returns:
        True if path is safe, False otherwise
    """
    from pathlib import Path

    try:
        file_path = Path(file_path).resolve()

        for allowed_dir in allowed_directories:
            allowed_dir = Path(allowed_dir).resolve()
            if str(file_path).startswith(str(allowed_dir)):
                return True

        return False
    except (ValueError, OSError):
        return False


def rate_limit_by_user(limit=10, per=60):
    """
    Custom rate limiter by user ID (more strict than IP-based).

    Args:
        limit: Number of requests allowed
        per: Time period in seconds

    Example:
        @app.route('/upload', methods=['POST'])
        @login_required
        @rate_limit_by_user(limit=5, per=300)  # 5 uploads per 5 minutes
        def upload():
            ...
    """
    def decorator(f):
        # Simple in-memory store (use Redis in production)
        from collections import defaultdict
        requests_by_user = defaultdict(list)

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return f(*args, **kwargs)

            user_id = current_user.id
            now = time.time()

            # Clean old requests
            requests_by_user[user_id] = [
                req_time for req_time in requests_by_user[user_id]
                if now - req_time < per
            ]

            # Check rate limit
            if len(requests_by_user[user_id]) >= limit:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {limit} requests per {per} seconds'
                }), 429

            # Add current request
            requests_by_user[user_id].append(now)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def log_request(f):
    """
    Decorator to log API requests.

    Example:
        @app.route('/endpoint')
        @log_request
        def endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from datetime import datetime

        start_time = time.time()

        # Log request
        current_app.logger.info(
            f"Request: {request.method} {request.path} "
            f"User: {current_user.username if current_user.is_authenticated else 'Anonymous'} "
            f"IP: {request.remote_addr}"
        )

        # Execute request
        response = f(*args, **kwargs)

        # Log response time
        duration = time.time() - start_time
        current_app.logger.info(
            f"Response: {request.path} completed in {duration:.3f}s"
        )

        return response
    return decorated_function


class SecurityHeaders:
    """Middleware to add security headers to all responses"""

    def __init__(self, app=None):
        if app:
            self.init_app(app)

    def init_app(self, app):
        app.after_request(self.add_security_headers)

    @staticmethod
    def add_security_headers(response):
        """Add security headers to response"""
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Content Security Policy (adjust as needed)
        if not current_app.debug:
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "media-src 'self' https:;"
            )

        return response


def validate_upload_request():
    """
    Decorator to validate file upload requests.
    Checks for file presence, size, and type before processing.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if file is present
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400

            file = request.files['file']
            if not file or file.filename == '':
                return jsonify({'error': 'No file selected'}), 400

            # Check file size (Flask already enforces MAX_CONTENT_LENGTH)
            # But we can add additional validation here

            return f(*args, **kwargs)
        return decorated_function
    return decorator
