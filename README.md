# AI Radio 📻✨

> *The world's first fully AI-generated media ecosystem*

An innovative AI-powered radio platform that combines Flask backend architecture, automated content generation, and live streaming capabilities. Built to create a completely autonomous media experience powered by open-source AI models and Raspberry Pi infrastructure.

## 🚀 Features

- **🎵 Automated Radio Streaming** - Live broadcasts via Icecast & Liquidsoap
- **🤖 AI-Generated Content** - DJ intros, transitions, and custom content
- **📁 Media Upload System** - Upload audio/video with intelligent processing
- **👤 User Authentication** - Secure registration and login system
- **🎛️ Playlist Management** - Automated scheduling and content curation
- **⚡ Real-time Processing** - Background tasks with Celery & Redis
- **📊 REST API** - Complete API with 20+ endpoints
- **🌐 Web Interface** - Professional frontend with real-time updates

## 🏗️ Architecture

### Core Components
- **Backend**: Flask + SQLAlchemy + Celery task queue
- **AI Brain**: External GPU server for AI model inference
- **Streaming**: Liquidsoap automation + Icecast server
- **Frontend**: HTML/CSS/JavaScript with API integration
- **Database**: SQLAlchemy with comprehensive media models
- **Task Scheduling**: Redis-backed background processing

### Target Deployment
```
┌─────────────────┐     ┌──────────────────┐
│   AI Brain      │────▶│  Pi Cluster      │
│ (Desktop/GPU)   │     │  (3-5 Pi 4Bs)    │
│                 │     │                  │
│ • GPT Models    │     │ • Web Server     │
│ • TTS Engine    │     │ • Stream Server  │
│ • Content Gen   │     │ • File Storage   │
└─────────────────┘     └──────────────────┘
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Redis server
- FFmpeg
- Icecast2
- Liquidsoap

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd ai_radio

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
export SECRET_KEY="your-secret-key"
export DATABASE_URL="sqlite:///ai_radio.db"
export REDIS_URL="redis://localhost:6379/0"

# Initialize database
python -c "from backend.app import create_app; from backend.models import db; app = create_app(); app.app_context().push(); db.create_all()"

# Start services
redis-server &
celery -A backend.celery_tasks.celery worker --loglevel=info &
python backend/app.py
```

### Production Setup
1. **Configure AI Brain Server** - Set up external GPU server for AI models
2. **Setup Raspberry Pi Cluster** - Deploy across multiple Pi nodes
3. **Configure Streaming** - Start Icecast and Liquidsoap services
4. **Setup Nginx** - Configure reverse proxy with SSL
5. **Environment Variables** - Move secrets to production configuration

## 📁 Project Structure

```
ai_radio/
├── backend/               # Flask application
│   ├── app.py            # Main Flask app
│   ├── models.py         # Database models
│   ├── api.py            # REST API endpoints
│   ├── auth.py           # Authentication system
│   ├── upload_handler.py # Media upload processing
│   ├── ai_generator.py   # AI content generation
│   ├── scheduler.py      # Playlist automation
│   └── celery_tasks.py   # Background tasks
├── frontend/             # Web interface
│   ├── static/          # CSS, JS, assets
│   └── templates/       # HTML templates
├── config/              # Configuration files
│   ├── icecast.xml     # Icecast server config
│   └── liquidsoap.liq  # Radio automation script
├── media/              # Media storage
│   ├── audio/         # Audio files
│   ├── uploads/       # User uploads
│   └── dj_intros/     # AI-generated intros
└── scripts/           # Utility scripts
```

## 🔌 API Endpoints

The platform provides a comprehensive REST API:

- **Authentication**: `/auth/login`, `/auth/register`, `/auth/logout`
- **Media Management**: `/api/media/*`, `/upload/*`
- **Streaming**: `/api/now-playing`, `/api/playlist`
- **User Management**: `/api/users`, `/api/profile`
- **Health Check**: `/health`

See `backend/api.py` for complete endpoint documentation.

## 🤖 AI Integration

The system integrates with external AI models for:
- **Text-to-Speech** - AI-generated DJ voices
- **Content Generation** - Automated show content
- **Media Processing** - Intelligent audio/video handling
- **Playlist Curation** - Smart content scheduling

## 🔧 Configuration

### Environment Variables
```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///ai_radio.db
REDIS_URL=redis://localhost:6379/0
UPLOAD_FOLDER=/path/to/uploads
MEDIA_FOLDER=/path/to/media
AI_BRAIN_URL=http://ai-brain-server:8080
```

### Streaming Configuration
- **Icecast**: Configure `config/icecast.xml` for your streaming setup
- **Liquidsoap**: Customize `config/liquidsoap.liq` for radio automation

## 🚧 Development Status

### ✅ Completed
- Core Flask application architecture
- User authentication & authorization
- Media upload & processing system
- Database models & API endpoints
- AI integration framework
- Streaming automation setup
- Web interface & templates

### 🔄 In Progress
- Redis task queue optimization
- AI Brain server deployment
- Production deployment scripts
- Frontend-backend integration refinements

### 📋 Planned
- Video streaming capabilities
- Advanced AI content generation
- Performance optimization
- Monitoring & analytics
- Mobile-responsive interface

## 📊 Health & Monitoring

The system includes health check endpoints and monitoring capabilities:
- **Health Check**: `GET /health` - Service status
- **System Status**: Monitor streaming, AI services, and database
- **Performance Metrics**: Track uploads, generation times, and streaming stats

## 🔒 Security

Security features implemented:
- ✅ Password hashing with bcrypt
- ✅ File upload validation & sanitization
- ✅ Rate limiting on API endpoints
- ✅ Secure session management
- ⚠️ SSL/HTTPS required for production
- ⚠️ Content validation for AI-generated media

## 🤝 Contributing

This project is designed as a comprehensive AI media platform. When contributing:

1. Follow the existing Flask blueprint architecture
2. Maintain separation between AI processing and web serving
3. Ensure all uploads are properly validated
4. Test streaming functionality thoroughly
5. Document any new API endpoints

## 📄 License

This project is part of an open-source AI media ecosystem initiative.

## 🎯 Vision

Creating the world's first fully autonomous AI radio station that generates, curates, and broadcasts content 24/7 using open-source AI models and community-driven infrastructure.

---

*Built with ❤️ for the future of AI-generated media*