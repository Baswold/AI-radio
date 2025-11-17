"""Flask application factory for the AI Radio backend."""

import os
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_login import LoginManager, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

from config import get_config
from models import db, User
from auth import auth_bp
from upload_handler import upload_bp
from api import api_bp
from logger import setup_logging, SecurityLogger, PerformanceLogger
from middleware import SecurityHeaders
import time

# Load environment variables
load_dotenv()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    config_class.init_app(app)

    # Setup logging
    setup_logging(app)
    app.logger.info('AI Radio backend starting...')
    app.logger.info(f'Environment: {config_name or os.environ.get("FLASK_ENV", "development")}')

    # Initialize security and performance loggers
    security_logger = SecurityLogger(app)
    performance_logger = PerformanceLogger(app)

    # Initialize rate limiter
    if app.config.get('RATELIMIT_ENABLED', True):
        limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            default_limits=[app.config.get('RATELIMIT_DEFAULT', '100 per minute')],
            storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
        )
        app.logger.info('Rate limiting enabled')
    else:
        app.logger.info('Rate limiting disabled')

    # Initialize extensions
    db.init_app(app)
    app.logger.info('Database initialized')

    # Initialize CORS
    CORS(app, origins=app.config.get('CORS_ORIGINS', ['*']),
         supports_credentials=app.config.get('CORS_ALLOW_CREDENTIALS', True))
    app.logger.info('CORS initialized')

    # Initialize security headers middleware
    SecurityHeaders(app)
    app.logger.info('Security headers middleware initialized')

    # Initialize Flask-Login
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({'error': 'Authentication required'}), 401

    # Request logging middleware
    @app.before_request
    def before_request():
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            if duration > 1.0:  # Log slow requests
                app.logger.warning(
                    f'Slow request: {request.method} {request.path} took {duration:.3f}s'
                )

            # Log to performance logger
            performance_logger.log_request(
                request.method,
                request.path,
                duration,
                response.status_code
            )

        return response

    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        app.logger.warning(f'Bad request: {request.path} - {str(e)}')
        return jsonify({'error': 'Bad request', 'message': str(e)}), 400

    @app.errorhandler(401)
    def unauthorized_error(e):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        app.logger.warning(
            f'Forbidden: {request.path} - User: {current_user.username if current_user.is_authenticated else "Anonymous"}'
        )
        return jsonify({'error': 'Forbidden', 'message': 'You do not have permission'}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        max_size = app.config.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024)
        max_size_mb = max_size / (1024 * 1024)
        return jsonify({
            'error': 'File too large',
            'message': f'Maximum file size is {max_size_mb:.0f}MB'
        }), 413

    @app.errorhandler(429)
    def ratelimit_handler(e):
        app.logger.warning(f'Rate limit exceeded: {request.remote_addr} - {request.path}')
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f'Internal server error: {request.path} - {str(e)}', exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.logger.info('Blueprints registered')

    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except Exception as e:
            app.logger.error(f'Database health check failed: {e}')
            db_status = 'unhealthy'

        return jsonify({
            'status': 'healthy' if db_status == 'healthy' else 'degraded',
            'service': 'ai-radio-backend',
            'database': db_status,
            'timestamp': time.time()
        }), 200 if db_status == 'healthy' else 503

    # Create database tables
    with app.app_context():
        db.create_all()
        app.logger.info('Database tables created/verified')

        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@localhost',
                is_admin=True
            )
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            app.logger.info('Default admin user created (username: admin, password: admin123)')

    app.logger.info('AI Radio backend initialized successfully')
    return app


if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', False))
