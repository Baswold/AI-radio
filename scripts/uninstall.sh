#!/bin/bash

# Stop all services
echo "Stopping all services..."
brew services stop supervisor
brew services stop redis

# Remove Python packages
echo "Removing Python packages..."
pip uninstall -r requirements.txt -y

# Clean up media files
echo "Cleaning up media files..."
rm -rf /Users/basil_jackson/Documents/ai_radio/media/*

# Remove database
echo "Removing database..."
rm -f ai_radio.db

# Remove logs
echo "Removing logs..."
sudo rm -rf /var/log/ai_radio

# Remove supervisor config
echo "Removing supervisor configuration..."
rm -f /usr/local/etc/supervisor.d/ai_radio.ini

echo "Uninstall complete!"
