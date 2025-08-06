# AI Media Platform - Complete Implementation Guide

## System Architecture

### Hardware Setup
```
┌─────────────────┐     ┌──────────────────┐
│   AI Brain      │────▶│  Pi Cluster      │
│ (Desktop/GPU)   │     │  (3-5 Pi 4Bs)    │
│                 │     │                  │
│ • GPT-OSS 20B   │     │ • Web Server     │
│ • TTS Models    │     │ • Stream Server  │
│ • Video Gen     │     │ • File Storage   │
└─────────────────┘     └──────────────────┘
```

### Role Distribution

| Component | Hardware | Purpose |
|-----------|----------|---------|
| AI Brain | Desktop with GPU | Runs GPT-OSS, TTS (Coqui/Bark), video generation |
| Pi Master | Raspberry Pi 4B | Orchestrates playlists, scheduling, control logic |
| Stream Node | Raspberry Pi | Runs Icecast/Liquidsoap for streaming |
| Web Node | Raspberry Pi | Hosts website, handles uploads |
| Storage | Pi + External SSD/NAS | Stores all media files and metadata |

## Project Structure

```
/ai-media-platform/
├── backend/
│   ├── app.py                 # Flask main app
│   ├── models.py              # SQLAlchemy models
│   ├── auth.py                # User authentication
│   ├── upload_handler.py      # File upload processing
│   ├── scheduler.py           # Playlist & scheduling
│   └── ai_generator.py        # GPT-OSS & TTS integration
│
├── frontend/
│   ├── templates/
│   │   ├── index.html         # Homepage
│   │   ├── stream.html        # Live stream player
│   │   ├── explore.html       # Browse content
│   │   ├── upload.html        # Upload form
│   │   └── dashboard.html     # User dashboard
│   └── static/
│       ├── css/
│       ├── js/
│       └── assets/
│
├── media/
│   ├── audio/
│   │   ├── music/
│   │   ├── podcasts/
│   │   └── dj_intros/
│   ├── video/
│   │   ├── animations/
│   │   ├── stories/
│   │   └── educational/
│   └── uploads/
│       └── pending/           # Awaiting review
│
├── ai_models/
│   ├── gpt_oss/              # GPT-OSS model files
│   ├── tts/                  # Coqui/Bark models
│   └── prompts/              # DJ personality prompts
│
├── config/
│   ├── icecast.xml           # Streaming config
│   ├── liquidsoap.liq        # Audio mixing config
│   └── nginx.conf            # Web server config
│
└── scripts/
    ├── setup.sh              # Initial setup script
    ├── generate_dj.py        # Batch DJ line generator
    └── transcode.py          # Video/audio processing
```

## Implementation Steps

### Phase 1: Core Infrastructure (Week 1)

#### 1.1 Set up Raspberry Pi Cluster
```bash
# On each Pi
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip nginx ffmpeg sqlite3 -y

# Install Python dependencies
pip3 install flask flask-sqlalchemy flask-login bcrypt
pip3 install celery redis  # For task queue
```

#### 1.2 Database Schema
```python
# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploads = db.relationship('Upload', backref='user', lazy=True)

class Upload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    media_type = db.Column(db.String(20))  # 'audio' or 'video'
    category = db.Column(db.String(50))
    filename = db.Column(db.String(255))
    file_hash = db.Column(db.String(64))  # For duplicate detection
    duration = db.Column(db.Integer)  # In seconds
    status = db.Column(db.String(20), default='pending')
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    played_count = db.Column(db.Integer, default=0)
    tags = db.Column(db.JSON)

class Segment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('upload.id'))
    dj_intro_text = db.Column(db.Text)
    dj_intro_audio = db.Column(db.String(255))
    scheduled_time = db.Column(db.DateTime)
    played_at = db.Column(db.DateTime)
```

### Phase 2: AI Integration (Week 2)

#### 2.1 GPT-OSS DJ Generator (runs on AI Brain)
```python
# ai_generator.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json

class AIHost:
    def __init__(self, model_path="gpt-oss-20b"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
    def generate_intro(self, metadata):
        prompt = f"""You are a friendly AI DJ for an all-AI media station. 
        Create a brief, engaging introduction for:
        Title: {metadata['title']}
        Creator: {metadata['username']}
        Type: {metadata['media_type']}
        Description: {metadata['description']}
        
        Keep it under 30 seconds when spoken. Be creative and fun!
        """
        
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            inputs.input_ids,
            max_length=150,
            temperature=0.8,
            do_sample=True
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def generate_segment_transition(self, current, next_item):
        prompt = f"""Create a smooth transition from "{current['title']}" 
        to "{next_item['title']}". Keep it natural and brief."""
        # Similar generation logic
        pass
```

#### 2.2 TTS Integration (Coqui for local TTS)
```python
# tts_handler.py
from TTS.api import TTS

class VoiceSynthesizer:
    def __init__(self):
        # Use Coqui TTS with a good quality model
        self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
        
    def generate_audio(self, text, output_path):
        self.tts.tts_to_file(
            text=text,
            file_path=output_path,
            speaker="default",
            language="en"
        )
        return output_path
```

### Phase 3: Upload & Processing System (Week 3)

#### 3.1 Upload Handler
```python
# upload_handler.py
import hashlib
import os
from werkzeug.utils import secure_filename
import ffmpeg
import subprocess

class MediaProcessor:
    ALLOWED_AUDIO = {'mp3', 'wav', 'ogg', 'm4a'}
    ALLOWED_VIDEO = {'mp4', 'webm', 'avi', 'mov'}
    
    def __init__(self, upload_dir="/media/uploads/pending"):
        self.upload_dir = upload_dir
        
    def process_upload(self, file, metadata):
        # Check file hash for duplicates
        file_hash = self.get_file_hash(file)
        
        # Validate file format
        if not self.validate_format(file):
            raise ValueError("Invalid file format")
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(self.upload_dir, filename)
        file.save(filepath)
        
        # Process based on type
        if metadata['media_type'] == 'audio':
            return self.process_audio(filepath)
        else:
            return self.process_video(filepath)
    
    def process_audio(self, filepath):
        # Convert to MP3 if needed, normalize audio
        output_path = filepath.replace(os.path.splitext(filepath)[1], '.mp3')
        
        ffmpeg.input(filepath).output(
            output_path,
            audio_bitrate='192k',
            af='loudnorm=I=-16:TP=-1.5:LRA=11'
        ).run()
        
        # Get duration
        probe = ffmpeg.probe(output_path)
        duration = float(probe['streams'][0]['duration'])
        
        return {
            'filepath': output_path,
            'duration': duration
        }
    
    def process_video(self, filepath):
        # Transcode to web-friendly format
        output_path = filepath.replace(os.path.splitext(filepath)[1], '.mp4')
        
        ffmpeg.input(filepath).output(
            output_path,
            vcodec='libx264',
            acodec='aac',
            preset='fast',
            crf=23,
            maxrate='2M',
            bufsize='4M'
        ).run()
        
        # Generate thumbnail
        thumbnail_path = output_path.replace('.mp4', '_thumb.jpg')
        ffmpeg.input(output_path, ss=5).output(
            thumbnail_path,
            vframes=1
        ).run()
        
        return {
            'filepath': output_path,
            'thumbnail': thumbnail_path
        }
    
    def get_file_hash(self, file):
        hasher = hashlib.sha256()
        for chunk in iter(lambda: file.read(4096), b""):
            hasher.update(chunk)
        file.seek(0)  # Reset file pointer
        return hasher.hexdigest()
```

### Phase 4: Streaming Setup (Week 4)

#### 4.1 Icecast Configuration
```xml
<!-- icecast.xml -->
<icecast>
    <location>AI Media Platform</location>
    <admin>admin@localhost</admin>
    <limits>
        <clients>100</clients>
        <sources>2</sources>
        <threadpool>5</threadpool>
        <queue-size>524288</queue-size>
        <client-timeout>30</client-timeout>
        <header-timeout>15</header-timeout>
        <source-timeout>10</source-timeout>
    </limits>
    
    <authentication>
        <source-password>hackme</source-password>
        <relay-password>hackme</relay-password>
        <admin-user>admin</admin-user>
        <admin-password>hackme</admin-password>
    </authentication>
    
    <hostname>localhost</hostname>
    
    <listen-socket>
        <port>8000</port>
    </listen-socket>
    
    <mount>
        <mount-name>/stream</mount-name>
        <fallback-mount>/silence.mp3</fallback-mount>
        <public>1</public>
    </mount>
</icecast>
```

#### 4.2 Liquidsoap Script
```ruby
# liquidsoap.liq
#!/usr/bin/liquidsoap

# Log configuration
log.file.path := "/var/log/liquidsoap/radio.log"

# Load playlist
playlist = playlist(reload_mode="watch", "/media/playlists/current.m3u")

# Add DJ intros
def add_dj_intro(m) =
  intro_file = "/media/dj_intros/#{m['id']}_intro.mp3"
  if file.exists(intro_file) then
    sequence([single(intro_file), source.drop(source=playlist)])
  else
    playlist
  end
end

# Apply audio processing
radio = normalize(playlist)
radio = add_dj_intro(radio)

# Output to Icecast
output.icecast(
  %mp3(bitrate=192),
  host="localhost",
  port=8000,
  password="hackme",
  mount="/stream",
  name="AI Media Platform",
  description="100% AI-Generated Content",
  radio
)
```

### Phase 5: Web Interface (Week 5)

#### 5.1 Flask App Structure
```python
# app.py
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///platform.db'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)

@app.route('/')
def index():
    # Show featured content, live stream info
    featured = Upload.query.filter_by(status='approved').limit(6).all()
    return render_template('index.html', featured=featured)

@app.route('/stream')
def stream():
    # Live stream player page
    now_playing = get_now_playing()
    return render_template('stream.html', now_playing=now_playing)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        metadata = {
            'title': request.form['title'],
            'description': request.form['description'],
            'media_type': request.form['media_type'],
            'category': request.form['category'],
            'tags': request.form.getlist('tags')
        }
        
        # Process upload
        processor = MediaProcessor()
        result = processor.process_upload(file, metadata)
        
        # Save to database
        upload = Upload(
            user_id=current_user.id,
            title=metadata['title'],
            description=metadata['description'],
            media_type=metadata['media_type'],
            category=metadata['category'],
            filename=result['filepath'],
            duration=result.get('duration'),
            tags=metadata['tags']
        )
        db.session.add(upload)
        db.session.commit()
        
        # Queue AI intro generation
        generate_dj_intro.delay(upload.id)
        
        return redirect(url_for('dashboard'))
    
    return render_template('upload.html')

@app.route('/explore')
def explore():
    # Browse all content
    page = request.args.get('page', 1, type=int)
    media_type = request.args.get('type', 'all')
    
    query = Upload.query.filter_by(status='approved')
    if media_type != 'all':
        query = query.filter_by(media_type=media_type)
    
    uploads = query.paginate(page=page, per_page=20)
    return render_template('explore.html', uploads=uploads)

@app.route('/api/now_playing')
def api_now_playing():
    # Return current playing info as JSON
    return jsonify(get_now_playing())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

## Deployment Guide

### Step 1: Initial Pi Setup
```bash
# Clone repository
git clone https://github.com/yourusername/ai-media-platform.git
cd ai-media-platform

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Initialize database
python3 -c "from app import db; db.create_all()"
```

### Step 2: Configure AI Brain (Desktop)
```bash
# Install GPT-OSS
pip install transformers torch accelerate

# Download GPT-OSS-20B model
python -c "from transformers import AutoModelForCausalLM; AutoModelForCausalLM.from_pretrained('openai/gpt-oss-20b')"

# Install TTS
pip install TTS

# Set up remote API endpoint for Pi cluster to call
python ai_brain_server.py
```

### Step 3: Start Services
```bash
# On Stream Pi
icecast2 -c /config/icecast.xml
liquidsoap /config/liquidsoap.liq

# On Web Pi
python app.py

# On Master Pi
python scheduler.py
```

### Step 4: Configure Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /stream {
        proxy_pass http://localhost:8000/stream;
        proxy_buffering off;
    }
    
    location /static {
        alias /ai-media-platform/frontend/static;
    }
    
    location /media {
        alias /media;
        expires 30d;
    }
}
```

## Advanced Features

### Video Streaming with HLS
```python
# video_streamer.py
def create_hls_stream(video_path, output_dir):
    """Convert video to HLS format for adaptive streaming"""
    
    # Create multiple quality versions
    qualities = [
        {'resolution': '1920x1080', 'bitrate': '5000k', 'name': '1080p'},
        {'resolution': '1280x720', 'bitrate': '2800k', 'name': '720p'},
        {'resolution': '854x480', 'bitrate': '1400k', 'name': '480p'},
    ]
    
    for q in qualities:
        output_path = f"{output_dir}/{q['name']}.m3u8"
        
        ffmpeg.input(video_path).output(
            output_path,
            format='hls',
            hls_time=10,
            hls_list_size=0,
            vf=f"scale={q['resolution']}",
            b=q['bitrate']
        ).run()
    
    # Create master playlist
    create_master_playlist(output_dir, qualities)
```

### AI Content Generation Pipeline
```python
# content_generator.py
from celery import Celery

celery = Celery('tasks', broker='redis://localhost:6379')

@celery.task
def generate_daily_content():
    """Generate fresh AI content daily"""
    
    # Generate AI podcast episode
    podcast_script = ai_host.generate_podcast_script(topic="Tech News")
    podcast_audio = voice_synth.generate_audio(podcast_script)
    
    # Generate AI music
    music_prompt = "Chill electronic ambient for studying"
    # Use local music generation model
    
    # Create video content
    story_script = ai_host.generate_kids_story()
    # Generate animation with local video model
    
    return "Daily content generated"

@celery.task
def generate_dj_intro(upload_id):
    """Generate AI DJ intro for new upload"""
    upload = Upload.query.get(upload_id)
    
    intro_text = ai_host.generate_intro({
        'title': upload.title,
        'username': upload.user.username,
        'media_type': upload.media_type,
        'description': upload.description
    })
    
    intro_audio = voice_synth.generate_audio(
        intro_text,
        f"/media/dj_intros/{upload_id}_intro.mp3"
    )
    
    upload.dj_intro_text = intro_text
    upload.dj_intro_audio = intro_audio
    db.session.commit()
```

## Performance Optimization

### Caching Strategy
```python
# Use Redis for caching
import redis
cache = redis.Redis(host='localhost', port=6379, db=0)

def get_now_playing():
    # Check cache first
    cached = cache.get('now_playing')
    if cached:
        return json.loads(cached)
    
    # Generate fresh data
    data = generate_now_playing_info()
    cache.setex('now_playing', 30, json.dumps(data))
    return data
```

### CDN for Static Content
```bash
# Use Cloudflare or local caching proxy
# Configure nginx to cache static files
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Monitoring & Maintenance

### Health Checks
```python
# health_check.py
def check_services():
    checks = {
        'database': check_db_connection(),
        'streaming': check_icecast_status(),
        'storage': check_disk_space(),
        'ai_brain': check_ai_brain_api()
    }
    return all(checks.values())
```

### Auto-cleanup Script
```python
# cleanup.py
def cleanup_old_files():
    """Remove files older than 30 days that haven't been played"""
    cutoff_date = datetime.now() - timedelta(days=30)
    
    old_uploads = Upload.query.filter(
        Upload.uploaded_at < cutoff_date,
        Upload.played_count == 0
    ).all()
    
    for upload in old_uploads:
        # Archive to cold storage or delete
        archive_file(upload.filename)
        upload.status = 'archived'
    
    db.session.commit()
```

## Security Considerations

1. **Content Validation**: Verify all uploads are actually AI-generated
2. **Rate Limiting**: Prevent spam uploads
3. **User Authentication**: Secure login with bcrypt
4. **File Scanning**: Check uploads for malicious content
5. **HTTPS**: Use Let's Encrypt for SSL certificates

## Scaling Plan

As your platform grows:
1. Add more Pis to the cluster for load balancing
2. Implement distributed storage with GlusterFS
3. Use message queue (RabbitMQ) for task distribution
4. Add CDN for global content delivery
5. Implement analytics to track popular content

## Next Steps

1. **MVP Launch**: Start with audio-only, basic upload system
2. **Community Building**: Create Discord/forum for creators
3. **Feature Expansion**: Add video, live streaming, chat
4. **Monetization**: Optional premium features, donations
5. **Federation**: Connect with other AI content platforms

---

This platform will be the world's first fully AI-generated media ecosystem. The combination of open-source AI models, Raspberry Pi infrastructure, and community-driven content makes it truly unique!