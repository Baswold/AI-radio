# AI Radio Project - Development Notes & Architecture Guide

## 1. Project Overview & Vision
This is an AI-powered radio application with a Flask backend and static frontend. The ultimate vision is to create the world's first fully AI-generated media ecosystem, combining open-source AI models, Raspberry Pi infrastructure, and community-driven content.

**Core Features:**
- User authentication and registration
- Media upload processing (audio/video)
- Automated playlist management and scheduling
- AI-generated DJ intros and transitions
- Live streaming via Icecast and Liquidsoap

---

## 2. Target System Architecture
The proposed architecture is a distributed model designed for scalability and separation of concerns.

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

---

## 3. Code Analysis & Implementation Status

### ✅ Well-Implemented / Complete
- **Authentication System** (`auth.py`): Robust implementation with proper validation and security.
- **Database Models** (`models.py`): Comprehensive schema for all core features.
- **Upload Processing** (`upload_handler.py`): Sophisticated media handling with FFmpeg.
- **API Blueprint** (`api.py`): A complete REST API with 20+ endpoints.
- **AI Generation Core** (`ai_generator.py`): Sophisticated AI host and TTS system.
- **Playlist Management** (`scheduler.py`): Full scheduler and playlist automation.
- **Task Queue** (`celery_tasks.py`): Background processing for AI tasks and system maintenance.
- **Streaming Automation** (`liquidsoap.liq`): Professional radio automation script.
- **Frontend**: Professional UI templates, CSS, and JS API client are in place.

### 🔧 Technical Architecture Now Complete:
- **Backend**: Flask + Celery + Redis task queue
- **AI**: External AI Brain server + local fallbacks
- **Streaming**: Liquidsoap + Icecast with dual quality streams  
- **Frontend**: HTML templates + CSS + JavaScript API client
- **Database**: SQLAlchemy with comprehensive models
- **Task Scheduling**: Cron-based playlist automation

### 🚨 Next Critical Steps:
1. **Redis Setup** - Celery requires a running Redis broker.
2. **Icecast Configuration** - Finalize and review `icecast.xml`.
3. **AI Brain Server** - The external GPU server needs to be implemented and deployed.
4. **Environment Variables** - Move all hardcoded secrets and paths to a production-ready environment configuration.

---

## 4. Architectural Notes & Discrepancies
This section notes differences between the `ai-platform-architecture.md` blueprint and the current implementation.

- **AI Integration**: The blueprint suggests running `transformers` models directly on the AI Brain. The current implementation uses a more flexible approach, where the Flask app calls an external API on the AI Brain. This is a good pattern as it decouples the main app from the heavy AI workload.
- **Database Schema**: The blueprint proposes a simpler schema. The implemented `models.py` is more detailed and robust, which is an improvement.
- **Project Structure**: The blueprint suggests `ai_models/` and `scripts/` directories. These are not present in the current project, but could be added for better organization, especially for setup and utility scripts.
- **Configuration**: The blueprint mentions an `nginx.conf`. This will be a critical component for deployment as a reverse proxy.

---

## 5. Implementation & Deployment Plan
This is the phased plan adapted from the architecture guide.

### Phase 1-4: Core Infrastructure (Largely Complete)
The current codebase has already implemented the majority of features outlined in the first four phases of the architecture guide, including database schema, AI integration logic, upload processing, and the core streaming setup.

### Phase 5: Web Interface & Deployment
This is the next major focus area.

#### 5.1 Finalize Frontend-Backend Integration
- Connect all frontend JS controls in `main.js` to the corresponding backend API endpoints in `api.py`.
- Ensure real-time updates for "Now Playing" information.
- Test the full upload-to-playlist pipeline from the UI.

#### 5.2 Deployment Steps
1.  **Setup Pi Cluster & AI Brain**:
    - On each Pi: `sudo apt update && sudo apt install python3-pip nginx ffmpeg redis-server -y`
    - Install Python dependencies from `requirements.txt`.
2.  **Configure AI Brain (Desktop)**:
    - Install `transformers`, `torch`, `TTS`, etc.
    - Deploy the AI Brain as a REST API server that the main app can call.
3.  **Initialize Database**:
    - Run `python3 -c "from app import db; db.create_all()"` on the Web/Master Pi.
4.  **Start Services**:
    - **Stream Pi**: `icecast2 -c config/icecast.xml` & `liquidsoap config/liquidsoap.liq`
    - **Web Pi**: `gunicorn -w 4 'app:app'` (or similar production server)
    - **Master Pi**: `celery -A celery_tasks.celery worker --loglevel=info` & `python scheduler.py`
5.  **Configure Nginx Reverse Proxy**:
    - Use a configuration similar to the one in the architecture guide to route traffic to the Flask app (`:5000`) and Icecast (`:8000`).
    - Set up SSL with Let's Encrypt.

---

## 6. Security Considerations
- ✅ **Password Hashing**: Implemented with bcrypt.
- ✅ **File Uploads**: Using secure filenames and format validation.
- ⚠️ **Rate Limiting**: Needs to be implemented to prevent API abuse and spam uploads.
- ⚠️ **Secret Management**: Secret key and passwords must be moved to environment variables.
- ⚠️ **Content Validation**: A process may be needed to verify all uploads are actually AI-generated.
- ⚠️ **File Scanning**: Consider adding a step to scan uploads for malicious content.
- ⚠️ **HTTPS**: Essential for production deployment.

---

## 7. Advanced Features & Future Roadmap
- **Video Streaming**: Implement HLS adaptive streaming for video content as outlined in the architecture guide.
- **AI Content Generation**: Set up the `generate_daily_content` Celery task to create new AI podcasts, music, or stories automatically.
- **Performance**: Implement Redis caching for frequently accessed data like "Now Playing" info and API results. Use a CDN for static assets.
- **Monitoring**: Create a health check endpoint or script (`health_check.py`) to monitor the status of the database, streaming server, and AI Brain.
- **Maintenance**: Implement an auto-cleanup script to archive or delete old, unplayed content.

---
*Last updated: 2025-08-06 - Architecture guide integrated.*