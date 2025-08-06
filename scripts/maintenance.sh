#!/bin/bash

# Source environment variables
source .env

# Function to send notification
notify() {
    local message=$1
    local level=${2:-info}  # Default to info level
    
    # Add your notification method here (Slack, email, etc.)
    echo "[$(date)] [$level] $message" >> /var/log/ai_radio/maintenance.log
    
    if [ "$level" = "error" ]; then
        # Send urgent notifications for errors
        # Example: Send email or Slack message
        echo "Error: $message" | mail -s "AI Radio Error" $ADMIN_EMAIL
    fi
}

# Check disk space
check_disk_space() {
    local threshold=90  # Percentage
    local disk_use=$(df -h $MEDIA_FOLDER | awk 'NR==2 {print $5}' | tr -d '%')
    
    if [ $disk_use -gt $threshold ]; then
        notify "Disk usage is at ${disk_use}%" error
        # Trigger cleanup script
        python3 cleanup.py --force
    fi
}

# Check services
check_services() {
    services=("redis" "icecast" "liquidsoap" "supervisor")
    
    for service in "${services[@]}"; do
        if ! brew services list | grep $service | grep started > /dev/null; then
            notify "Service $service is not running" error
            brew services restart $service
        fi
    }
}

# Run maintenance tasks
echo "Starting maintenance checks..."

# Check disk space
check_disk_space

# Check services
check_services

# Run cleanup script
python3 cleanup.py

# Check health
response=$(curl -s http://localhost:5000/health)
if [[ $response != *"healthy"* ]]; then
    notify "Health check failed" error
fi

echo "Maintenance complete"
