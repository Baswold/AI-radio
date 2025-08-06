from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    uploads = db.relationship('Upload', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    media_type = db.Column(db.String(20), nullable=False)  # 'audio' or 'video'
    category = db.Column(db.String(50))
    filename = db.Column(db.String(255))
    file_hash = db.Column(db.String(64))  # For duplicate detection
    duration = db.Column(db.Integer)  # In seconds
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    played_count = db.Column(db.Integer, default=0)
    last_played = db.Column(db.DateTime)
    tags = db.Column(db.JSON)
    thumbnail_path = db.Column(db.String(255))
    segments = db.relationship('Segment', backref='upload', lazy=True, cascade='all, delete-orphan')

class Segment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'), nullable=False)
    dj_intro_text = db.Column(db.Text)
    dj_intro_audio = db.Column(db.String(255))
    scheduled_time = db.Column(db.DateTime)
    played_at = db.Column(db.DateTime)
    position_in_playlist = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    entries = db.relationship('PlaylistEntry', backref='playlist', lazy=True, cascade='all, delete-orphan')

class PlaylistEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.Integer, db.ForeignKey('playlist.id'), nullable=False)
    upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

class StreamStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    current_upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'))
    current_segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'))
    started_at = db.Column(db.DateTime)
    listeners = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    current_upload = db.relationship('Upload')
    current_segment = db.relationship('Segment')