"""
Pytest configuration and fixtures for AI Radio tests.
"""

import pytest
import tempfile
import os
from pathlib import Path
from app import create_app
from models import db, User, Upload
from io import BytesIO


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Create temporary directory for test files
    test_dir = tempfile.mkdtemp()

    # Create test configuration
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,
        'UPLOAD_FOLDER': Path(test_dir) / 'uploads',
        'MEDIA_FOLDER': Path(test_dir) / 'media',
        'PENDING_DIR': Path(test_dir) / 'uploads' / 'pending',
        'AUDIO_DIR': Path(test_dir) / 'media' / 'audio',
        'VIDEO_DIR': Path(test_dir) / 'media' / 'video',
        'THUMBNAIL_DIR': Path(test_dir) / 'media' / 'thumbnails',
        'DJ_INTRO_DIR': Path(test_dir) / 'media' / 'dj_intros',
        'PLAYLIST_DIR': Path(test_dir) / 'media' / 'playlists',
        'VIDEO_STREAM_DIR': Path(test_dir) / 'media' / 'video_stream',
        'LOG_FILE': Path(test_dir) / 'logs' / 'test.log',
        'RATELIMIT_ENABLED': False,
        'ENABLE_MALWARE_SCAN': False,
        'ENABLE_AI_INTROS': False,
        'MAX_CONTENT_LENGTH': 500 * 1024 * 1024,
    }

    app = create_app('testing')

    # Override config
    app.config.update(test_config)

    # Create directories
    for key in ['UPLOAD_FOLDER', 'MEDIA_FOLDER', 'PENDING_DIR', 'AUDIO_DIR',
                'VIDEO_DIR', 'THUMBNAIL_DIR', 'DJ_INTRO_DIR', 'PLAYLIST_DIR',
                'VIDEO_STREAM_DIR']:
        Path(app.config[key]).mkdir(parents=True, exist_ok=True)

    Path(app.config['LOG_FILE']).parent.mkdir(parents=True, exist_ok=True)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    # Cleanup
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com'
        )
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()

        # Refresh to get ID
        db.session.refresh(user)
        yield user


@pytest.fixture
def admin_user(app):
    """Create an admin user"""
    with app.app_context():
        user = User(
            username='admin',
            email='admin@example.com',
            is_admin=True
        )
        user.set_password('adminpassword')
        db.session.add(user)
        db.session.commit()

        db.session.refresh(user)
        yield user


@pytest.fixture
def auth_client(client, test_user):
    """Create authenticated test client"""
    client.post('/auth/login', json={
        'login': test_user.username,
        'password': 'testpassword'
    })
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Create authenticated admin test client"""
    client.post('/auth/login', json={
        'login': admin_user.username,
        'password': 'adminpassword'
    })
    return client


@pytest.fixture
def test_upload(app, test_user):
    """Create a test upload"""
    with app.app_context():
        upload = Upload(
            user_id=test_user.id,
            title='Test Upload',
            description='Test description',
            media_type='audio',
            category='test',
            filename='/tmp/test.mp3',
            file_hash='abc123',
            file_size=1024,
            duration=180,
            status='pending',
            tags=['test', 'example']
        )
        db.session.add(upload)
        db.session.commit()

        db.session.refresh(upload)
        yield upload


@pytest.fixture
def approved_upload(app, test_user):
    """Create an approved upload"""
    with app.app_context():
        upload = Upload(
            user_id=test_user.id,
            title='Approved Upload',
            description='Approved test upload',
            media_type='audio',
            category='music',
            filename='/tmp/approved.mp3',
            file_hash='def456',
            file_size=2048,
            duration=240,
            status='approved',
            played_count=10,
            tags=['music', 'test']
        )
        db.session.add(upload)
        db.session.commit()

        db.session.refresh(upload)
        yield upload


@pytest.fixture
def sample_audio_file():
    """Create a sample audio file for testing"""
    # Create a minimal valid MP3 file header
    # This is a very basic MP3 frame header
    mp3_data = b'\xFF\xFB\x90\x00' + b'\x00' * 1000

    return BytesIO(mp3_data), 'test.mp3'


@pytest.fixture
def sample_video_file():
    """Create a sample video file for testing"""
    # Create minimal video data
    video_data = b'\x00\x00\x00\x20ftypmp42' + b'\x00' * 1000

    return BytesIO(video_data), 'test.mp4'
