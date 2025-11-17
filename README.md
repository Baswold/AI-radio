# AI Radio 📻✨

> *The world's first fully AI-generated media ecosystem - Now with enterprise-grade security and scalability*

An innovative AI-powered radio platform combining Flask backend architecture, automated content generation, and live streaming capabilities. Built to create a completely autonomous media experience powered by open-source AI models with production-ready infrastructure.

## 🚀 Features

### Core Functionality
- **🎵 Automated Radio Streaming** - Live broadcasts via Icecast & Liquidsoap
- **🤖 AI-Generated Content** - DJ intros, transitions, and custom content
- **📁 Media Upload System** - Upload audio/video with intelligent processing
- **👤 User Authentication** - Secure registration and login system with role-based access
- **🎛️ Playlist Management** - Automated scheduling and content curation
- **⚡ Real-time Processing** - Background tasks with Celery & Redis
- **📊 REST API** - Complete API with 20+ endpoints
- **🌐 Web Interface** - Professional frontend with real-time updates

### Security & Performance (NEW!)
- **🔒 Enhanced Security** - Admin authorization, CSRF protection, XSS prevention
- **📝 Comprehensive Logging** - Structured logging with security and performance monitoring
- **🚦 Rate Limiting** - Prevent abuse with configurable rate limits
- **🔍 Input Validation** - Sanitization and validation for all user inputs
- **🛡️ Path Traversal Protection** - Secure file serving and upload handling
- **🦠 Malware Scanning** - Optional ClamAV integration for upload security
- **📊 Database Optimization** - Indexes and query optimization for better performance
- **🐳 Docker Support** - Full containerization with Docker Compose

## 🏗️ Architecture

### Core Components
- **Backend**: Flask + SQLAlchemy + Celery task queue
- **Configuration**: Environment-based config with dotenv support
- **Security**: Middleware for admin auth, rate limiting, and security headers
- **Logging**: Structured logging with separate security and performance logs
- **AI Brain**: External GPU server for AI model inference
- **Streaming**: Liquidsoap automation + Icecast server
- **Frontend**: HTML/CSS/JavaScript with API integration
- **Database**: SQLAlchemy with indexed and optimized models
- **Task Scheduling**: Redis-backed background processing
- **Containerization**: Docker and Docker Compose for easy deployment

### Target Deployment
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   AI Brain      │────▶│  Backend Cluster │────▶│  Load Balancer  │
│ (Desktop/GPU)   │     │  (Docker Swarm)  │     │  (Nginx/Proxy)  │
│                 │     │                  │     │                 │
│ • GPT Models    │     │ • Flask API      │     │ • SSL/TLS       │
│ • TTS Engine    │     │ • Celery Workers │     │ • Static Files  │
│ • Content Gen   │     │ • Redis/Postgres │     │ • Rate Limiting │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Redis server
- FFmpeg
- Icecast2 (optional)
- Liquidsoap (optional)
- Docker & Docker Compose (recommended)
- PostgreSQL (recommended for production)

### Quick Start with Docker (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd AI-radio

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Access the application
# Backend API: http://localhost:5000
# Health check: http://localhost:5000/health
```

### Manual Installation

```bash
# Clone the repository
git clone <repository-url>
cd AI-radio

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python -c "from backend.app import create_app; from backend.models import db; app = create_app(); app.app_context().push(); db.create_all()"

# Start Redis
redis-server &

# Start Celery worker
cd backend
celery -A celery_tasks.celery worker --loglevel=info &

# Start Celery beat (for scheduled tasks)
celery -A celery_tasks.celery beat --loglevel=info &

# Start Flask application
python app.py
```

### Production Setup

1. **Environment Configuration**
   ```bash
   # Set production environment
   export FLASK_ENV=production
   export SECRET_KEY="$(openssl rand -hex 32)"
   export DATABASE_URL="postgresql://user:password@localhost/airadio"
   export SESSION_COOKIE_SECURE=True
   ```

2. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb airadio

   # Run migrations (if using Alembic)
   alembic upgrade head
   ```

3. **Start with Gunicorn**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 300 "backend.app:create_app()"
   ```

4. **Configure Nginx** (sample configuration in `docs/nginx.conf`)

5. **Setup SSL/TLS** (use Let's Encrypt certbot)

## 📁 Project Structure

```
AI-radio/
├── backend/                   # Flask application
│   ├── app.py                # Main Flask app (IMPROVED)
│   ├── config.py             # Configuration system (NEW)
│   ├── models.py             # Database models (IMPROVED with indexes)
│   ├── middleware.py         # Security middleware (NEW)
│   ├── logger.py             # Logging system (NEW)
│   ├── api.py                # REST API endpoints (IMPROVED)
│   ├── auth.py               # Authentication system
│   ├── upload_handler.py     # Media upload (original)
│   ├── upload_handler_improved.py  # Improved upload handler (NEW)
│   ├── ai_generator.py       # AI content generation
│   ├── scheduler.py          # Playlist automation
│   ├── streaming_manager.py  # Streaming control
│   ├── celery_tasks.py       # Background tasks
│   ├── requirements.txt      # Python dependencies (NEW)
│   └── tests/                # Test suite (NEW)
│       ├── conftest.py       # Test configuration
│       └── test_auth.py      # Authentication tests
├── frontend/                  # Web interface
│   ├── static/               # CSS, JS, assets
│   └── templates/            # HTML templates
├── config/                    # Configuration files
│   ├── icecast.xml           # Icecast server config
│   └── liquidsoap.liq        # Radio automation script
├── media/                     # Media storage
│   ├── audio/                # Processed audio
│   ├── video/                # Processed video
│   ├── uploads/              # User uploads
│   ├── thumbnails/           # Video thumbnails
│   └── dj_intros/            # AI-generated intros
├── logs/                      # Application logs (NEW)
│   ├── ai_radio.log          # Main log
│   ├── error.log             # Error log
│   ├── security.log          # Security events (NEW)
│   └── performance.log       # Performance metrics (NEW)
├── Dockerfile                 # Docker image (NEW)
├── docker-compose.yml         # Docker Compose config (NEW)
├── .env.example              # Environment template (IMPROVED)
├── README.md                 # This file (IMPROVED)
└── SECURITY.md               # Security documentation (NEW)
```

## 🔌 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/profile` - Get user profile
- `GET /auth/check` - Check authentication status

### Media Management
- `POST /upload/` - Upload media file
- `GET /upload/my-uploads` - Get user's uploads
- `GET /api/media/audio/<id>` - Stream audio
- `GET /api/media/video/<id>` - Stream video
- `GET /api/media/thumbnail/<id>` - Get thumbnail

### Public Content
- `GET /api/now-playing` - Currently playing content
- `GET /api/stream-info` - Stream information
- `GET /api/featured-content` - Featured content
- `GET /api/explore` - Browse content with filters
- `GET /api/search` - Search content

### User Content (Authenticated)
- `GET /api/playlist/current` - Current playlist
- `GET /api/recommendations` - Personalized recommendations
- `GET /api/upload/<id>` - Upload details
- `GET /api/stats/overview` - Platform statistics

### Admin Endpoints (Admin Only) 🔒
- `GET /api/admin/pending` - Pending uploads
- `POST /api/admin/approve/<id>` - Approve upload
- `POST /api/admin/streaming/start` - Start streaming
- `POST /api/admin/streaming/stop` - Stop streaming
- `POST /api/admin/streaming/restart` - Restart streaming
- `POST /api/admin/streaming/skip-track` - Skip current track

### System
- `GET /health` - Health check endpoint

## 🔐 Security Features

### Authentication & Authorization
- ✅ bcrypt password hashing
- ✅ Role-based access control (User/Admin)
- ✅ Session management with secure cookies
- ✅ Admin-only endpoints protection
- ✅ Automatic admin user creation

### Input Validation & Sanitization
- ✅ Comprehensive file validation (extension, MIME type, size)
- ✅ Path traversal protection
- ✅ Filename sanitization
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS protection with security headers
- ✅ CSRF protection

### Network Security
- ✅ Rate limiting (configurable per endpoint)
- ✅ Security headers (X-Frame-Options, CSP, etc.)
- ✅ CORS configuration
- ✅ HTTPS/SSL support (production)

### File Security
- ✅ File type validation
- ✅ Malware scanning (optional ClamAV integration)
- ✅ Secure file storage
- ✅ Duplicate detection (SHA256 hashing)

### Logging & Monitoring
- ✅ Structured logging system
- ✅ Security event logging
- ✅ Performance monitoring
- ✅ Error tracking
- ✅ Request/response logging

## 📊 Configuration

### Environment Variables

See `.env.example` for complete configuration options:

**Essential Settings:**
```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=postgresql://user:password@localhost/airadio
REDIS_URL=redis://localhost:6379/0
```

**File Storage:**
```bash
UPLOAD_FOLDER=./media/uploads
MEDIA_FOLDER=./media
MAX_UPLOAD_SIZE=524288000  # 500MB
```

**Security:**
```bash
SESSION_COOKIE_SECURE=True  # HTTPS only
ENABLE_MALWARE_SCAN=True    # Requires ClamAV
RATELIMIT_ENABLED=True
```

**Features:**
```bash
ENABLE_AI_INTROS=True
ENABLE_VIDEO_STREAMING=True
```

## 🧪 Testing

```bash
# Install test dependencies
pip install -r backend/requirements.txt

# Run tests
cd backend
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v
```

## 📈 Performance Optimization

### Database
- ✅ Indexed columns for faster queries
- ✅ Eager loading to prevent N+1 queries
- ✅ Connection pooling
- ✅ Query optimization

### File Processing
- ✅ Async processing with Celery
- ✅ Streaming file uploads
- ✅ Efficient hashing (chunked)
- ✅ FFmpeg optimization

### Caching
- ✅ Redis for session storage
- ✅ Rate limit storage in Redis
- ⚠️ Response caching (TODO)

## 🐛 Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Check database URL
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

**Redis connection errors:**
```bash
# Check Redis is running
redis-cli ping

# Check Redis URL
echo $REDIS_URL
```

**Upload failures:**
```bash
# Check permissions
ls -la media/uploads

# Check disk space
df -h

# Check FFmpeg
ffmpeg -version
```

**Import errors:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

## 🚀 Deployment

### Docker Deployment (Recommended)

```bash
# Production deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale workers
docker-compose up -d --scale celery=4

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Deployment

See `docs/DEPLOYMENT.md` for detailed deployment instructions.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Use type hints where applicable
- Log important events

## 📄 License

This project is part of an open-source AI media ecosystem initiative.

## 🎯 Vision

Creating the world's first fully autonomous AI radio station that generates, curates, and broadcasts content 24/7 using open-source AI models and community-driven infrastructure - now with enterprise-grade security and scalability.

## 📚 Additional Documentation

- [Security Policy](SECURITY.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## 🙏 Acknowledgments

- Flask community
- Celery project
- FFmpeg team
- Open-source AI community

---

*Built with ❤️ for the future of AI-generated media*

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123`
- **⚠️ Change immediately in production!**
