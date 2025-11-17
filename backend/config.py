"""
Configuration module for AI Radio backend.
Centralizes all configuration settings and removes hardcoded paths.
"""

import os
from pathlib import Path
from datetime import timedelta


class Config:
    """Base configuration class"""

    # Base directories
    BASE_DIR = Path(__file__).parent.parent
    BACKEND_DIR = Path(__file__).parent

    # Flask core settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    TESTING = False

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR}/instance/ai_radio.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE', 500 * 1024 * 1024))  # 500MB default
    UPLOAD_FOLDER = Path(os.environ.get('UPLOAD_FOLDER', BASE_DIR / 'media' / 'uploads'))
    MEDIA_FOLDER = Path(os.environ.get('MEDIA_FOLDER', BASE_DIR / 'media'))

    # Media processing settings
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'avi', 'mov', 'mkv'}
    ALLOWED_MIME_TYPES = {
        'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4', 'audio/flac',
        'audio/aac', 'audio/x-m4a',
        'video/mp4', 'video/webm', 'video/quicktime', 'video/x-matroska',
        'video/x-msvideo'
    }
    MAX_MEDIA_DURATION = int(os.environ.get('MAX_MEDIA_DURATION', 3600))  # 1 hour in seconds

    # Processing directories
    PENDING_DIR = UPLOAD_FOLDER / 'pending'
    AUDIO_DIR = MEDIA_FOLDER / 'audio'
    VIDEO_DIR = MEDIA_FOLDER / 'video'
    THUMBNAIL_DIR = MEDIA_FOLDER / 'thumbnails'
    DJ_INTRO_DIR = MEDIA_FOLDER / 'dj_intros'
    PLAYLIST_DIR = MEDIA_FOLDER / 'playlists'
    VIDEO_STREAM_DIR = MEDIA_FOLDER / 'video_stream'

    # Redis/Celery settings
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', REDIS_URL)
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', REDIS_URL)

    # Rate limiting
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() in ('true', '1', 't')
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', REDIS_URL)
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '100 per minute')

    # Session settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 't')
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    CORS_ALLOW_CREDENTIALS = True

    # AI Brain settings (for DJ intro generation)
    AI_BRAIN_URL = os.environ.get('AI_BRAIN_URL', 'http://localhost:8080')
    AI_BRAIN_TIMEOUT = int(os.environ.get('AI_BRAIN_TIMEOUT', 30))

    # Streaming settings
    ICECAST_HOST = os.environ.get('ICECAST_HOST', 'localhost')
    ICECAST_PORT = int(os.environ.get('ICECAST_PORT', 8000))
    ICECAST_CONFIG = Path(os.environ.get('ICECAST_CONFIG', BASE_DIR / 'config' / 'icecast.xml'))
    LIQUIDSOAP_CONFIG = Path(os.environ.get('LIQUIDSOAP_CONFIG', BASE_DIR / 'config' / 'liquidsoap.liq'))
    STREAM_URL = os.environ.get('STREAM_URL', f'http://{ICECAST_HOST}:{ICECAST_PORT}/stream')

    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = Path(os.environ.get('LOG_FILE', BASE_DIR / 'logs' / 'ai_radio.log'))
    LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))

    # Security settings
    ENABLE_MALWARE_SCAN = os.environ.get('ENABLE_MALWARE_SCAN', 'False').lower() in ('true', '1', 't')
    CLAMAV_HOST = os.environ.get('CLAMAV_HOST', 'localhost')
    CLAMAV_PORT = int(os.environ.get('CLAMAV_PORT', 3310))

    # FFmpeg settings
    FFMPEG_BINARY = os.environ.get('FFMPEG_BINARY', 'ffmpeg')
    FFPROBE_BINARY = os.environ.get('FFPROBE_BINARY', 'ffprobe')
    FFMPEG_THREADS = int(os.environ.get('FFMPEG_THREADS', 2))

    # Feature flags
    ENABLE_VIDEO_STREAMING = os.environ.get('ENABLE_VIDEO_STREAMING', 'True').lower() in ('true', '1', 't')
    ENABLE_AI_INTROS = os.environ.get('ENABLE_AI_INTROS', 'True').lower() in ('true', '1', 't')
    REQUIRE_EMAIL_VERIFICATION = os.environ.get('REQUIRE_EMAIL_VERIFICATION', 'False').lower() in ('true', '1', 't')

    @classmethod
    def init_app(cls, app):
        """Initialize application with this config"""
        # Create necessary directories
        for directory in [
            cls.UPLOAD_FOLDER,
            cls.MEDIA_FOLDER,
            cls.PENDING_DIR,
            cls.AUDIO_DIR,
            cls.VIDEO_DIR,
            cls.THUMBNAIL_DIR,
            cls.DJ_INTRO_DIR,
            cls.PLAYLIST_DIR,
            cls.VIDEO_STREAM_DIR,
            cls.LOG_FILE.parent,
            cls.BASE_DIR / 'instance',
        ]:
            Path(directory).mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

    # Require these to be set in production
    @classmethod
    def init_app(cls, app):
        super().init_app(app)

        # Ensure critical settings are configured
        if cls.SECRET_KEY == 'dev-key-change-in-production':
            raise ValueError('SECRET_KEY must be set in production!')

        if 'sqlite' in cls.SQLALCHEMY_DATABASE_URI:
            import warnings
            warnings.warn('Using SQLite in production is not recommended!')


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(config_name=None):
    """Get configuration class by name"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, DevelopmentConfig)
