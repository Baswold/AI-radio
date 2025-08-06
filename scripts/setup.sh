#!/bin/bash

# Create needed directories
mkdir -p /Users/basil_jackson/Documents/ai_radio/media/{audio,video,dj_intros,uploads/pending,archive}

# Install system dependencies
echo "Installing system dependencies..."
brew install redis nginx python3 ffmpeg

# Install Python packages
echo "Installing Python packages..."
python3 -m pip install -r requirements.txt

# Start Redis server
echo "Starting Redis server..."
brew services start redis

# Create and setup environment file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update .env with your production values"
fi

# Initialize database
echo "Initializing database..."
export FLASK_APP=backend/app.py
flask db init
flask db upgrade

# Setup supervisor for process management
echo "Installing and configuring supervisor..."
brew install supervisor

echo "Setting up supervisor configurations..."
cat > /usr/local/etc/supervisor.d/ai_radio.ini << EOL
[program:flask]
command=gunicorn -w 4 -b 127.0.0.1:5000 'backend.app:create_app()'
directory=/Users/basil_jackson/Documents/ai_radio
user=basil_jackson
autostart=true
autorestart=true
stderr_logfile=/var/log/ai_radio/flask.err.log
stdout_logfile=/var/log/ai_radio/flask.out.log

[program:celery]
command=celery -A backend.celery_tasks.celery worker --loglevel=info
directory=/Users/basil_jackson/Documents/ai_radio
user=basil_jackson
autostart=true
autorestart=true
stderr_logfile=/var/log/ai_radio/celery.err.log
stdout_logfile=/var/log/ai_radio/celery.out.log

[program:icecast]
command=icecast -c config/icecast.xml
user=basil_jackson
autostart=true
autorestart=true
stderr_logfile=/var/log/ai_radio/icecast.err.log
stdout_logfile=/var/log/ai_radio/icecast.out.log

[program:liquidsoap]
command=liquidsoap config/liquidsoap.liq
user=basil_jackson
autostart=true
autorestart=true
stderr_logfile=/var/log/ai_radio/liquidsoap.err.log
stdout_logfile=/var/log/ai_radio/liquidsoap.out.log
EOL

# Create log directory
sudo mkdir -p /var/log/ai_radio
sudo chown -R basil_jackson:staff /var/log/ai_radio

# Start services
echo "Starting services..."
brew services start supervisor

echo "Setup complete! Please:"
echo "1. Update .env with your production values"
echo "2. Configure Nginx using the provided nginx.conf"
echo "3. Set up SSL certificates for production"
echo "4. Start the system with: brew services start supervisor"
