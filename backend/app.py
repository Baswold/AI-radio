from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import Flask, jsonify
from flask_login import LoginManager
from flask_cors import CORS
import os
from models import db, User
from auth import auth_bp
from upload_handler import upload_bp
from api import api_bp

def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ai_radio.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', '/Users/basil_jackson/Documents/ai_radio/media/uploads')
    app.config['MEDIA_FOLDER'] = os.environ.get('MEDIA_FOLDER', '/Users/basil_jackson/Documents/ai_radio/media')
    
    # Initialize rate limiter
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["100 per minute"],
        storage_uri=os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    )
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(upload_bp, url_prefix='/upload')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'ai-radio-backend'
        })
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)